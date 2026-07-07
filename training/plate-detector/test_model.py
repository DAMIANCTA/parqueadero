from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = SCRIPT_DIR / "runs" / "detect" / "train" / "weights" / "best.pt"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test a trained YOLO plate detector on one image.")
    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL),
        help="Path to a trained YOLO weights file.",
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the image to test.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for predictions.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the annotated prediction image.",
    )
    parser.add_argument(
        "--project",
        default=str(SCRIPT_DIR / "runs" / "predict"),
        help="Directory for prediction outputs when --save is used.",
    )
    parser.add_argument(
        "--name",
        default="demo",
        help="Prediction run name when --save is used.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    model_path = Path(args.model).resolve()
    image_path = Path(args.image).resolve()

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    model = YOLO(str(model_path))
    results = model.predict(
        source=str(image_path),
        conf=args.conf,
        save=args.save,
        project=args.project,
        name=args.name,
        verbose=False,
    )

    if not results:
        print("No inference results returned.")
        return

    result = results[0]
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        print("No license plate detected.")
        return

    print(f"Image: {image_path}")
    for index, box in enumerate(boxes, start=1):
        xyxy = [float(value) for value in box.xyxy[0].tolist()]
        confidence = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else 0.0
        class_id = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else -1
        x1, y1, x2, y2 = xyxy
        width = x2 - x1
        height = y2 - y1
        print(
            f"Detection {index}: class_id={class_id} confidence={confidence:.4f} "
            f"bbox=(x={x1:.1f}, y={y1:.1f}, width={width:.1f}, height={height:.1f})"
        )

    if args.save:
        save_dir = Path(result.save_dir).resolve()
        print(f"Annotated image saved under: {save_dir}")


if __name__ == "__main__":
    main()
