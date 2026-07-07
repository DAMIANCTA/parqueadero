from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = SCRIPT_DIR / "dataset" / "dataset.yaml"
DEFAULT_PROJECT = SCRIPT_DIR / "runs" / "detect"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a YOLO plate detector locally.")
    parser.add_argument(
        "--data",
        default=str(DEFAULT_DATASET),
        help="Path to YOLO dataset.yaml.",
    )
    parser.add_argument(
        "--model",
        default="yolo11n.pt",
        help="Base YOLO checkpoint, for example yolo11n.pt or yolo8n.pt.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Training image size.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs.",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size.",
    )
    parser.add_argument(
        "--project",
        default=str(DEFAULT_PROJECT),
        help="Directory where Ultralytics will save runs.",
    )
    parser.add_argument(
        "--name",
        default="train",
        help="Run name inside the project folder.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Optional device override, for example cpu, 0, or 0,1.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of dataloader workers.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dataset_path = Path(args.data).resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    project_path = Path(args.project).resolve()
    project_path.mkdir(parents=True, exist_ok=True)

    model = YOLO(args.model)
    results = model.train(
        data=str(dataset_path),
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        project=str(project_path),
        name=args.name,
        device=args.device,
        workers=args.workers,
    )

    print("Training completed.")
    print(f"Dataset: {dataset_path}")
    print(f"Project dir: {project_path}")
    print(f"Run name: {args.name}")
    if hasattr(results, "save_dir"):
        print(f"Run output: {results.save_dir}")
        print(f"Expected best weights: {Path(results.save_dir) / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()
