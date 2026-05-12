"""
scripts/train_detector.py
Phase 1: Fine-tune YOLOv8 on the AirSim aerial dataset.

Usage:
    python scripts/train_detector.py --config configs/config.yaml
    python scripts/train_detector.py --config configs/config.yaml --model yolov8l
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml
from loguru import logger


def parse_args():
    p = argparse.ArgumentParser(description="Train YOLOv8 detector — AeroMind AI Phase 1")
    p.add_argument("--config", default="configs/config.yaml")
    p.add_argument("--model", default=None, help="Override model (yolov8n/s/m/l/x)")
    p.add_argument("--data", default="configs/dataset.yaml",
                   help="Path to dataset YAML (YOLO format)")
    p.add_argument("--resume", default=None, help="Resume from checkpoint path")
    p.add_argument("--device", default="0", help="cuda:0 or cpu")
    p.add_argument("--project", default="experiments", help="Output project dir")
    p.add_argument("--name", default="detection_v1", help="Run name")
    return p.parse_args()


def build_dataset_yaml(cfg: dict, output_path: str = "configs/dataset.yaml") -> str:
    """
    Auto-generate YOLO dataset config from project config.
    Expects data/processed/images/{train,val,test} and data/annotations/.
    """
    dataset = {
        "path": str(ROOT / "data" / "processed"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(cfg["detection"]["classes"]),
        "names": list(cfg["detection"]["classes"].values()),
    }
    path = ROOT / output_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(dataset, f, default_flow_style=False)
    logger.info(f"Dataset YAML written → {path}")
    return str(path)


def train(cfg: dict, args) -> None:
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    det = cfg["detection"]
    model_name = args.model or det["model"]
    train_cfg = det["training"]

    # Load model (pretrained or from checkpoint)
    if args.resume:
        logger.info(f"Resuming from {args.resume}")
        model = YOLO(args.resume)
    else:
        logger.info(f"Loading {model_name} (pretrained ImageNet weights)")
        model = YOLO(f"{model_name}.pt")

    # Generate dataset config if needed
    data_path = args.data
    if not Path(data_path).exists():
        data_path = build_dataset_yaml(cfg)

    logger.info("=" * 60)
    logger.info("  AeroMind AI Phase 1: Detection Training")
    logger.info(f"  Model    : {model_name}")
    logger.info(f"  Epochs   : {train_cfg['epochs']}")
    logger.info(f"  Batch    : {train_cfg['batch_size']}")
    logger.info(f"  LR       : {train_cfg['lr0']} → {train_cfg['lrf']}")
    logger.info(f"  SAHI     : {det['sahi']['enabled']}")
    logger.info(f"  Classes  : {list(det['classes'].values())}")
    logger.info("=" * 60)

    results = model.train(
        data=data_path,
        epochs=train_cfg["epochs"],
        batch=train_cfg["batch_size"],
        imgsz=det["input_size"],
        lr0=train_cfg["lr0"],
        lrf=train_cfg["lrf"] / train_cfg["lr0"],  # YOLO lrf = final_lr / lr0 (ratio)
        warmup_epochs=train_cfg["warmup_epochs"],
        mosaic=float(train_cfg["augmentation"]["mosaic"]),
        mixup=train_cfg["augmentation"]["mixup"],
        degrees=0.0,
        perspective=train_cfg["augmentation"]["perspective"],
        conf=det["confidence_threshold"],
        iou=det["nms_iou_threshold"],
        device=args.device,
        project=args.project,
        name=args.name,
        plots=True,
        save=True,
        exist_ok=True,
        seed=cfg["project"]["seed"],
    )

    best_path = Path(args.project) / args.name / "weights" / "best.pt"
    logger.success(f"Training complete! Best weights → {best_path}")

    # Copy best weights to models/detection/
    dest = ROOT / "models" / "detection" / "best.pt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if best_path.exists():
        import shutil
        shutil.copy(best_path, dest)
        logger.success(f"Best weights copied → {dest}")

    # Print final mAP
    if hasattr(results, "results_dict"):
        metrics = results.results_dict
        map50 = metrics.get("metrics/mAP50(B)", 0) * 100
        map5095 = metrics.get("metrics/mAP50-95(B)", 0) * 100
        logger.info(f"  mAP@50: {map50:.2f}%")
        logger.info(f"  mAP@50-95: {map5095:.2f}%")


def main():
    args = parse_args()

    with open(ROOT / args.config) as f:
        cfg = yaml.safe_load(f)

    train(cfg, args)


if __name__ == "__main__":
    main()
