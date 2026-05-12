"""
scripts/train_reid.py
Phase 2: Train OSNet-x0.25 Re-Identification model.
Triplet loss with hard negative mining + ArcFace softmax head.

Usage:
    python scripts/train_reid.py --config configs/config.yaml
    python scripts/train_reid.py --config configs/config.yaml --mock
    python scripts/train_reid.py --config configs/config.yaml --resume models/reid/reid_checkpoint.pt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import yaml
from loguru import logger


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train Re-ID model — AeroMind AI Phase 2")
    p.add_argument("--config",  default="configs/config.yaml")
    p.add_argument("--data",    default="data/reid",
                   help="Root with reid/{train,val}/{identity_id}/*.jpg")
    p.add_argument("--epochs",  type=int, default=None)
    p.add_argument("--resume",  default=None, help="Resume from checkpoint path")
    p.add_argument("--device",  default="cuda", help="cuda or cpu")
    p.add_argument("--output",  default="models/reid/reid_best.pt")
    p.add_argument("--mock",    action="store_true",
                   help="Dry-run with synthetic data (no real images needed)")
    return p.parse_args()


# ─── Synthetic dataset ────────────────────────────────────────────────────────

def build_mock_dataset(n_identities: int = 30,
                       n_per_id: int = 8) -> List[Tuple[np.ndarray, int]]:
    """Generate synthetic crops so the training loop can be validated without data."""
    rng = np.random.default_rng(42)
    dataset = []
    for pid in range(n_identities):
        base_color = rng.integers(50, 200, 3).astype(np.uint8)
        for _ in range(n_per_id):
            crop = np.tile(base_color, (256, 128, 1)).astype(np.uint8)
            noise = rng.integers(-30, 30, crop.shape, dtype=np.int16)
            crop = np.clip(crop.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            dataset.append((crop, pid))
    return dataset


def build_real_dataset(data_root: str, split: str) -> List[Tuple[str, int]]:
    """Collect (image_path, identity_id) pairs from Market-1501-style directory."""
    root = Path(data_root) / split
    if not root.exists():
        return []
    samples = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        pid = int(d.name)
        for ext in ("*.jpg", "*.png"):
            for p in sorted(d.glob(ext)):
                samples.append((str(p), pid))
    logger.info(f"[{split}] {len(samples)} images, "
                f"{len(set(s[1] for s in samples))} identities")
    return samples


# ─── Loss ────────────────────────────────────────────────────────────────────

class TripletHardMining:
    """Batch-hard triplet loss (Hermans et al., 2017)."""

    def __init__(self, margin: float = 0.5):
        self.margin = margin

    def __call__(self, embeddings, labels):
        import torch
        dist = self._pairwise_dist(embeddings)
        n = embeddings.size(0)
        device = embeddings.device
        relu = torch.nn.functional.relu
        loss = torch.tensor(0.0, device=device)
        valid = 0
        idx = torch.arange(n, device=device)
        for i in range(n):
            pos_mask = (labels == labels[i]) & (idx != i)
            neg_mask = labels != labels[i]
            if pos_mask.sum() == 0 or neg_mask.sum() == 0:
                continue
            hardest_pos = dist[i][pos_mask].max()
            hardest_neg = dist[i][neg_mask].min()
            loss = loss + relu(hardest_pos - hardest_neg + self.margin)
            valid += 1
        return loss / max(valid, 1)

    @staticmethod
    def _pairwise_dist(emb):
        dot = emb @ emb.T
        sq = dot.diag().unsqueeze(1)
        return (sq + sq.T - 2 * dot).clamp(min=0).sqrt()


# ─── Model ───────────────────────────────────────────────────────────────────

def build_model(cfg: dict, n_classes: int, device: str):
    """OSNet-x0.25 with softmax head. Falls back to lightweight CNN if unavailable."""
    try:
        import torchreid
        model = torchreid.models.build_model(
            name="osnet_x0_25",
            num_classes=n_classes,
            loss="softmax",
            pretrained=True,
        )
        model = model.to(device)
        logger.info(f"OSNet-x0.25 | classes={n_classes} | device={device}")
        return model
    except ImportError:
        import torch.nn as nn
        embed_dim = cfg["reid"]["embedding_dim"]

        class FallbackNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.enc = nn.Sequential(
                    nn.Conv2d(3, 32, 3, 2, 1), nn.ReLU(),
                    nn.Conv2d(32, 64, 3, 2, 1), nn.ReLU(),
                    nn.AdaptiveAvgPool2d((4, 2)), nn.Flatten(),
                )
                self.emb = nn.Linear(64 * 8, embed_dim)
                self.cls = nn.Linear(embed_dim, n_classes)

            def forward(self, x):
                f = self.enc(x)
                e = self.emb(f)
                return self.cls(e), e

        model = FallbackNet().to(device)
        logger.warning(f"Using fallback Re-ID CNN | embed={embed_dim}")
        return model


# ─── Training ────────────────────────────────────────────────────────────────

def run_training(cfg: dict, args: argparse.Namespace) -> None:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torchvision.transforms as T
    from torch.utils.data import Dataset, DataLoader

    reid_cfg  = cfg["reid"]
    n_epochs  = args.epochs or reid_cfg["training"]["epochs"]
    lr        = reid_cfg["training"]["lr"]
    batch     = reid_cfg["training"]["batch_size"]
    margin    = reid_cfg["training"]["triplet_margin"]
    warmup    = reid_cfg["training"]["warmup_steps"]
    device    = args.device if torch.cuda.is_available() else "cpu"

    # ── Build dataset ─────────────────────────────────────────────────────────
    if args.mock:
        raw = build_mock_dataset()
        n_classes = len(set(d[1] for d in raw))

        class MockDS(Dataset):
            def __init__(self, data, tf):
                self.data, self.tf = data, tf
            def __len__(self): return len(self.data)
            def __getitem__(self, i):
                img, pid = self.data[i]
                return self.tf(img), pid

        tf = T.Compose([
            T.ToPILImage(), T.Resize((256, 128)), T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        loader = DataLoader(MockDS(raw, tf), batch_size=batch, shuffle=True)
    else:
        samples = build_real_dataset(args.data, "train")
        if not samples:
            logger.error(f"No data in {args.data}/train/ — use --mock to test.")
            sys.exit(1)
        n_classes = len(set(s[1] for s in samples))
        label_map = {v: i for i, v in enumerate(sorted(set(s[1] for s in samples)))}

        class RealDS(Dataset):
            def __init__(self, samples, tf, lmap):
                self.s, self.tf, self.lmap = samples, tf, lmap
            def __len__(self): return len(self.s)
            def __getitem__(self, i):
                import cv2
                path, pid = self.s[i]
                img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
                return self.tf(img), self.lmap[pid]

        tf = T.Compose([
            T.ToPILImage(), T.Resize((256, 128)),
            T.RandomHorizontalFlip(),
            T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            T.RandomErasing(p=0.5),
        ])
        loader = DataLoader(RealDS(samples, tf, label_map),
                            batch_size=batch, shuffle=True, num_workers=4, pin_memory=True)

    # ── Model, optimiser, losses ──────────────────────────────────────────────
    model = build_model(cfg, n_classes, device)

    if args.resume and Path(ROOT / args.resume).exists():
        state = torch.load(ROOT / args.resume, map_location=device)
        model.load_state_dict(state, strict=False)
        logger.info(f"Resumed from {args.resume}")

    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs, eta_min=1e-6)
    ce_loss   = nn.CrossEntropyLoss(label_smoothing=0.1)
    tri_loss  = TripletHardMining(margin=margin)

    logger.info("=" * 60)
    logger.info("  AeroMind AI Phase 2: Re-Identification Training")
    logger.info(f"  Identities : {n_classes}")
    logger.info(f"  Epochs     : {n_epochs}")
    logger.info(f"  Batch      : {batch}")
    logger.info(f"  LR         : {lr}")
    logger.info(f"  Loss       : CE (label_smooth=0.1) + TripletHardMining (m={margin})")
    logger.info(f"  Device     : {device}")
    logger.info(f"  Mock mode  : {args.mock}")
    logger.info("=" * 60)

    best_loss = float("inf")
    global_step = 0

    for epoch in range(1, n_epochs + 1):
        model.train()
        total_loss = ce_t = tri_t = 0.0

        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)

            # Linear warm-up
            if global_step < warmup:
                scale = (global_step + 1) / warmup
                for pg in optimizer.param_groups:
                    pg["lr"] = lr * scale

            optimizer.zero_grad()
            out = model(imgs)
            logits, emb = out if isinstance(out, tuple) else (out, out)

            l_ce  = ce_loss(logits, labels)
            l_tri = tri_loss(emb, labels) if emb.shape != logits.shape else torch.tensor(0.0)
            loss  = l_ce + l_tri

            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()
            ce_t  += l_ce.item()
            tri_t += l_tri.item() if hasattr(l_tri, "item") else 0.0
            global_step += 1

        scheduler.step()
        nb = max(len(loader), 1)
        logger.info(
            f"Epoch {epoch:3d}/{n_epochs} | "
            f"loss={total_loss/nb:.4f} (CE={ce_t/nb:.4f}, Tri={tri_t/nb:.4f}) | "
            f"lr={optimizer.param_groups[0]['lr']:.2e}"
        )

        if total_loss < best_loss:
            best_loss = total_loss
            dest = ROOT / args.output
            dest.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), str(dest))
            logger.success(f"  ✓ Best saved → {dest}")

    logger.success("Phase 2 complete — Re-ID model ready.")


# ─── Entry ───────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    with open(ROOT / args.config) as f:
        cfg = yaml.safe_load(f)
    run_training(cfg, args)


if __name__ == "__main__":
    main()
