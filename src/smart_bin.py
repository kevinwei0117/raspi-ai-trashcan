"""Smart Recycling Bin - full pipeline using the TrashNet-fine-tuned classifier.

Camera -> MobileNetV2 (fine-tuned on TrashNet: cardboard/glass/metal/paper/
plastic/trash, see scripts/train_trashnet.py) -> one of 4 bins (glass/metal/
plastic/other, see src/category_map.py) -> rotate platform to that bin ->
tilt to drop.
Anything below the confidence cutoff defaults to "other" regardless of label.

Unlike an object detector, a whole-frame classifier has no built-in "is
anything there" signal - it always predicts something, even for an empty
platform. Presence is instead detected by diffing each frame against a
rolling background: only once something changes the scene enough do we
classify and sort, then we wait for the platform to look "empty" again
before re-arming. Preview window is optional (--no-preview for headless runs).

Usage:
    python -m src.smart_bin [--no-preview] [--confidence-threshold 0.4]
"""
from __future__ import annotations

import argparse
import threading
import time
import traceback
from pathlib import Path

import numpy as np

from src.camera import Camera
from src.category_map import label_to_category
from src.classifier import TrashClassifier
from src.servo_sorter import ServoBinSorter

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "trashnet_mobilenet_v2.tflite"
LABELS_PATH = MODEL_DIR / "trashnet_labels.txt"

STABLE_FRAMES_REQUIRED = 3  # consecutive presence/absence frames before acting

DEFAULT_LOW_CONFIDENCE_BIN = "other"


def log(msg: str) -> None:
    print(msg, flush=True)


def resolve_bin(label: str, confidence: float, threshold: float) -> str:
    """Below the confidence threshold, always default to "other" since the
    model isn't sure enough to trust its material guess."""
    if confidence < threshold:
        return DEFAULT_LOW_CONFIDENCE_BIN
    return label_to_category(label)


def frame_changed(frame: np.ndarray, background: np.ndarray, diff_threshold: float) -> bool:
    """True if `frame` differs enough from `background` to mean something's there."""
    diff = np.abs(frame.astype(np.int16) - background.astype(np.int16))
    return float(diff.mean()) > diff_threshold


class SmartBin:
    def __init__(self, confidence_threshold: float, diff_threshold: float, cooldown: float):
        self.confidence_threshold = confidence_threshold
        self.diff_threshold = diff_threshold
        self.cooldown = cooldown

        if not MODEL_PATH.exists() or not LABELS_PATH.exists():
            raise SystemExit(
                f"TrashNet model missing. Run scripts/train_trashnet.py to produce "
                f"{MODEL_PATH.name} and {LABELS_PATH.name} in {MODEL_DIR}/ first."
            )

        log("Loading TrashNet-fine-tuned classifier...")
        self.classifier = TrashClassifier(MODEL_PATH, LABELS_PATH, top_k=1)

        log("Starting camera...")
        self.camera = Camera()

        log("Setting up servos...")
        self.sorter = ServoBinSorter()

        self.running = True
        self.frame_lock = threading.Lock()
        self.latest_frame: np.ndarray | None = None
        self.latest_result = {"label": "waiting...", "confidence": 0.0, "bin": None}
        self._background: np.ndarray | None = None
        self._present_streak = 0
        self._absent_streak = 0
        self._already_sorted = False

    def _get_latest_frame(self) -> np.ndarray | None:
        with self.frame_lock:
            return self.latest_frame

    def ai_worker(self) -> None:
        while self.running:
            try:
                frame = self._get_latest_frame()
                if frame is None:
                    time.sleep(0.02)
                    continue

                if self._background is None:
                    self._background = frame.astype(np.float32)
                    time.sleep(0.05)
                    continue

                present = frame_changed(frame, self._background, self.diff_threshold)

                if present:
                    self._present_streak += 1
                    self._absent_streak = 0
                else:
                    self._absent_streak += 1
                    self._present_streak = 0
                    # slowly adapt to lighting drift while nothing's there
                    self._background = 0.95 * self._background + 0.05 * frame.astype(np.float32)

                if self._absent_streak >= STABLE_FRAMES_REQUIRED:
                    self._already_sorted = False
                    self.latest_result = {"label": "waiting...", "confidence": 0.0, "bin": None}

                if (
                    present
                    and self._present_streak >= STABLE_FRAMES_REQUIRED
                    and not self._already_sorted
                ):
                    from PIL import Image

                    (label, confidence), = self.classifier.predict(Image.fromarray(frame))
                    category = resolve_bin(label, confidence, self.confidence_threshold)
                    tag = f" (low-confidence -> {DEFAULT_LOW_CONFIDENCE_BIN})" if confidence < self.confidence_threshold else ""
                    self.latest_result = {"label": label, "confidence": confidence, "bin": category}
                    log(f"Detected: {label} ({confidence * 100:.1f}%) -> {category}{tag}")

                    self.sorter.sort(category)

                    self._already_sorted = True
                    self._present_streak = 0
                    self._absent_streak = 0
                    time.sleep(self.cooldown)

            except Exception:
                log("!! AI WORKER CRASHED !!")
                traceback.print_exc()
                time.sleep(1.0)

    def run(self, show_preview: bool) -> None:
        log("Smart bin running. " + ("Press 'q' in the preview window or Ctrl+C to stop.\n" if show_preview else "Press Ctrl+C to stop.\n"))

        worker = threading.Thread(target=self.ai_worker, daemon=True)
        worker.start()

        cv2 = None
        if show_preview:
            import cv2 as _cv2

            cv2 = _cv2
            cv2.namedWindow("Smart Recycling Bin", cv2.WINDOW_NORMAL)

        try:
            while True:
                frame = np.array(self.camera.capture())
                with self.frame_lock:
                    self.latest_frame = frame

                if cv2 is not None:
                    display = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    r = self.latest_result
                    color = (0, 165, 255) if r["confidence"] < self.confidence_threshold else (0, 255, 0)
                    text = f"{r['label']} ({r['confidence'] * 100:.0f}%) -> {r['bin']}"
                    cv2.putText(display, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.imshow("Smart Recycling Bin", display)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                else:
                    time.sleep(0.05)
        except KeyboardInterrupt:
            log("\nStopping.")
        finally:
            self.running = False
            worker.join(timeout=2.0)
            if cv2 is not None:
                cv2.destroyAllWindows()
            self.camera.close()
            self.sorter.close()
            log("Shut down cleanly.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confidence-threshold", type=float, default=0.40)
    parser.add_argument("--diff-threshold", type=float, default=15.0,
                         help="Mean pixel diff (0-255) from background to count as 'something is there'")
    parser.add_argument("--cooldown", type=float, default=1.5,
                         help="Seconds to pause after a sort before re-arming")
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()

    bin_ = SmartBin(args.confidence_threshold, args.diff_threshold, args.cooldown)
    bin_.run(show_preview=not args.no_preview)


if __name__ == "__main__":
    main()
