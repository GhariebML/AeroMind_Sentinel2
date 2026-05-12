"""
scripts/export_models.py
Edge-Ready Model Export Pipeline for AeroMind AI DroneTracking.

Exports trained PyTorch models to optimized formats for edge deployment:
  - ONNX:      Cross-platform, runs on CPU/GPU/NPU. Universal format.
  - TensorRT:  NVIDIA-optimized. Required for Jetson Orin/NX/Nano.

Usage:
    # Export all models (ONNX only by default)
    python scripts/export_models.py

    # Export to TensorRT as well (requires NVIDIA GPU + TensorRT installed)
    python scripts/export_models.py --trt

    # Export a specific model only
    python scripts/export_models.py --model yolo
    python scripts/export_models.py --model reid

Outputs (in models/exported/):
    yolov8m_aic4.onnx         — YOLOv8 detector, ONNX FP32
    yolov8m_aic4_fp16.onnx    — YOLOv8 detector, ONNX FP16 (faster)
    yolov8m_aic4.engine       — YOLOv8 detector, TensorRT (if --trt)
    osnet_reid.onnx            — OSNet Re-ID backbone, ONNX FP32
    osnet_reid.engine          — OSNet Re-ID backbone, TensorRT (if --trt)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

EXPORT_DIR = ROOT / "models" / "exported"

# ── Rich console output ────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import track
    console = Console()
    def log_info(msg):  console.print(f"[bold cyan]ℹ  {msg}[/]")
    def log_ok(msg):    console.print(f"[bold green]✓  {msg}[/]")
    def log_warn(msg):  console.print(f"[bold yellow]⚠  {msg}[/]")
    def log_err(msg):   console.print(f"[bold red]✗  {msg}[/]")
except ImportError:
    def log_info(msg):  print(f"INFO:  {msg}")
    def log_ok(msg):    print(f"OK:    {msg}")
    def log_warn(msg):  print(f"WARN:  {msg}")
    def log_err(msg):   print(f"ERROR: {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# YOLOv8 Export
# ─────────────────────────────────────────────────────────────────────────────

def export_yolo(weights_path: Path, export_trt: bool = False) -> dict:
    """Export YOLOv8 detector to ONNX (and optionally TensorRT)."""
    results = {}
    log_info(f"Exporting YOLOv8 from: {weights_path}")

    try:
        from ultralytics import YOLO

        model = YOLO(str(weights_path))
        input_size = 640

        # FP32 ONNX
        log_info("Exporting YOLOv8 → ONNX FP32 ...")
        t0 = time.time()
        out_path = model.export(
            format="onnx",
            imgsz=input_size,
            dynamic=True,           # Allow variable batch sizes
            simplify=True,          # Simplify ONNX graph
            opset=17,
        )
        elapsed = time.time() - t0
        onnx_fp32 = EXPORT_DIR / "yolov8m_aic4.onnx"
        Path(out_path).rename(onnx_fp32)
        results["yolo_onnx_fp32"] = {"path": str(onnx_fp32), "size_mb": onnx_fp32.stat().st_size / 1e6, "time_s": round(elapsed, 1)}
        log_ok(f"ONNX FP32 → {onnx_fp32} ({results['yolo_onnx_fp32']['size_mb']:.1f} MB, {elapsed:.1f}s)")

        # FP16 ONNX (half precision for faster inference on edge devices)
        log_info("Exporting YOLOv8 → ONNX FP16 ...")
        t0 = time.time()
        out_path_fp16 = model.export(
            format="onnx",
            imgsz=input_size,
            half=True,
            simplify=True,
            opset=17,
        )
        elapsed = time.time() - t0
        onnx_fp16 = EXPORT_DIR / "yolov8m_aic4_fp16.onnx"
        Path(out_path_fp16).rename(onnx_fp16)
        results["yolo_onnx_fp16"] = {"path": str(onnx_fp16), "size_mb": onnx_fp16.stat().st_size / 1e6, "time_s": round(elapsed, 1)}
        log_ok(f"ONNX FP16 → {onnx_fp16} ({results['yolo_onnx_fp16']['size_mb']:.1f} MB, {elapsed:.1f}s)")

        # TensorRT engine
        if export_trt:
            log_info("Exporting YOLOv8 → TensorRT FP16 engine ...")
            t0 = time.time()
            out_trt = model.export(
                format="engine",
                imgsz=input_size,
                half=True,
                simplify=True,
            )
            elapsed = time.time() - t0
            trt_path = EXPORT_DIR / "yolov8m_aic4.engine"
            Path(out_trt).rename(trt_path)
            results["yolo_trt"] = {"path": str(trt_path), "size_mb": trt_path.stat().st_size / 1e6, "time_s": round(elapsed, 1)}
            log_ok(f"TensorRT → {trt_path} ({results['yolo_trt']['size_mb']:.1f} MB, {elapsed:.1f}s)")

    except Exception as e:
        log_err(f"YOLOv8 export failed: {e}")
        results["error"] = str(e)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# OSNet Re-ID Export
# ─────────────────────────────────────────────────────────────────────────────

def export_reid(weights_path: Path, export_trt: bool = False) -> dict:
    """Export OSNet Re-ID backbone to ONNX (and optionally TensorRT)."""
    results = {}
    log_info(f"Exporting OSNet Re-ID from: {weights_path}")

    try:
        # Try to load OSNet via torchreid or as a generic torch model
        model = None
        try:
            import torchreid
            model = torchreid.models.build_model(
                name="osnet_x0_25",
                num_classes=1,
                pretrained=False,
            )
            checkpoint = torch.load(str(weights_path), map_location="cpu")
            state_dict = checkpoint.get("state_dict", checkpoint)
            model.load_state_dict(state_dict, strict=False)
            log_info("Loaded OSNet via torchreid.")
        except ImportError:
            log_warn("torchreid not installed — attempting generic torch.load.")
            model = torch.load(str(weights_path), map_location="cpu")

        if model is None:
            raise RuntimeError("Could not load Re-ID model.")

        model.eval()

        # Dummy input: (1, 3, 256, 128) — standard Re-ID crop size
        dummy_input = torch.randn(1, 3, 256, 128)

        # ONNX FP32
        log_info("Exporting OSNet → ONNX FP32 ...")
        t0 = time.time()
        onnx_path = EXPORT_DIR / "osnet_reid.onnx"
        torch.onnx.export(
            model,
            dummy_input,
            str(onnx_path),
            opset_version=17,
            input_names=["image"],
            output_names=["embedding"],
            dynamic_axes={
                "image":     {0: "batch_size"},
                "embedding": {0: "batch_size"},
            },
            do_constant_folding=True,
        )
        elapsed = time.time() - t0
        results["reid_onnx"] = {"path": str(onnx_path), "size_mb": onnx_path.stat().st_size / 1e6, "time_s": round(elapsed, 1)}
        log_ok(f"ONNX FP32 → {onnx_path} ({results['reid_onnx']['size_mb']:.1f} MB, {elapsed:.1f}s)")

        # TensorRT (requires tensorrt + polygraphy)
        if export_trt:
            log_info("Converting OSNet ONNX → TensorRT FP16 engine ...")
            try:
                import tensorrt as trt
                from polygraphy.backend.trt import (
                    TrtRunner, engine_from_network, network_from_onnx_path,
                    CreateConfig, Profile
                )
                engine_path = EXPORT_DIR / "osnet_reid.engine"
                profiles = [Profile().add("image", min=(1, 3, 256, 128), opt=(8, 3, 256, 128), max=(32, 3, 256, 128))]
                engine = engine_from_network(
                    network_from_onnx_path(str(onnx_path)),
                    config=CreateConfig(fp16=True, profiles=profiles),
                )
                with open(str(engine_path), "wb") as f:
                    f.write(engine.serialize())
                results["reid_trt"] = {"path": str(engine_path), "size_mb": engine_path.stat().st_size / 1e6}
                log_ok(f"TensorRT → {engine_path}")
            except ImportError:
                log_warn("TensorRT / Polygraphy not installed. Skipping Re-ID TRT export.")

    except FileNotFoundError:
        log_warn(f"Re-ID weights not found at {weights_path}. Skipping.")
        results["skipped"] = "weights not found"
    except Exception as e:
        log_err(f"Re-ID export failed: {e}")
        results["error"] = str(e)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Summary report
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(all_results: dict):
    try:
        from rich.table import Table
        from rich.console import Console
        c = Console()
        table = Table(title="Model Export Summary", show_header=True, header_style="bold cyan")
        table.add_column("Key",       style="dim",          width=20)
        table.add_column("Format",    style="bold",         width=12)
        table.add_column("Path",      style="green",        width=45)
        table.add_column("Size (MB)", justify="right",      width=10)
        table.add_column("Time (s)",  justify="right",      width=10)
        for model_key, results in all_results.items():
            for fmt, info in results.items():
                if isinstance(info, dict) and "path" in info:
                    table.add_row(
                        model_key, fmt,
                        Path(info["path"]).name,
                        f"{info.get('size_mb', 0):.1f}",
                        str(info.get("time_s", "—")),
                    )
        c.print(table)
    except ImportError:
        for model_key, results in all_results.items():
            for fmt, info in results.items():
                if isinstance(info, dict) and "path" in info:
                    print(f"{model_key} | {fmt} | {info['path']} | {info.get('size_mb',0):.1f} MB")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AeroMind AI Model Export — ONNX / TensorRT"
    )
    parser.add_argument("--model", choices=["yolo", "reid", "all"], default="all",
                        help="Which model to export (default: all)")
    parser.add_argument("--trt",   action="store_true",
                        help="Also export to TensorRT (requires NVIDIA GPU + TensorRT installed)")
    parser.add_argument("--yolo-weights", default="models/detection/best.pt",
                        help="Path to YOLOv8 weights (relative to project root)")
    parser.add_argument("--reid-weights", default="models/reid/reid_best.pt",
                        help="Path to OSNet Re-ID weights (relative to project root)")
    args = parser.parse_args()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    log_info(f"Export directory: {EXPORT_DIR}")
    if args.trt:
        log_warn("TensorRT mode enabled. This requires an NVIDIA GPU with TensorRT installed.")

    all_results = {}

    if args.model in ("yolo", "all"):
        yolo_weights = ROOT / args.yolo_weights
        if yolo_weights.exists():
            all_results["YOLOv8"] = export_yolo(yolo_weights, export_trt=args.trt)
        else:
            log_warn(f"YOLOv8 weights not found at {yolo_weights}. Skipping.")

    if args.model in ("reid", "all"):
        reid_weights = ROOT / args.reid_weights
        all_results["OSNet-ReID"] = export_reid(reid_weights, export_trt=args.trt)

    print_summary(all_results)
    log_ok("Export complete! Files saved to models/exported/")


if __name__ == "__main__":
    main()
