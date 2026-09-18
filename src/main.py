"""Live camera -> trash category loop, using the TrashNet-fine-tuned classifier.

Usage:
    python -m src.main [--interval SECONDS] [--confidence-threshold FLOAT]
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from src.camera import Camera
from src.category_map import label_to_category
from src.classifier import TrashClassifier
from src.sorter import Sorter

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "trashnet_mobilenet_v2.tflite"
LABELS_PATH = MODEL_DIR / "trashnet_labels.txt"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=1.5, help="Seconds between classifications")
    parser.add_argument("--confidence-threshold", type=float, default=0.4)
    args = parser.parse_args()

    if not MODEL_PATH.exists() or not LABELS_PATH.exists():
        raise SystemExit(
            f"TrashNet model missing. Run scripts/train_trashnet.py to produce "
            f"{MODEL_PATH.name} and {LABELS_PATH.name} in {MODEL_DIR}/ first."
        )

    classifier = TrashClassifier(MODEL_PATH, LABELS_PATH)

    with Camera() as camera, Sorter() as sorter:
        print("Trash classifier running. Press Ctrl+C to stop.")
        try:
            while True:
                frame = camera.capture()
                (label, confidence), = classifier.predict(frame)

                if confidence < args.confidence_threshold:
                    print(f"low confidence ({confidence:.2f}) for '{label}', skipping")
                    time.sleep(args.interval)
                    continue

                category = label_to_category(label)
                print(f"{label} ({confidence:.2f}) -> {category}")
                sorter.indicate(category)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopping.")


if __name__ == "__main__":
    main()
