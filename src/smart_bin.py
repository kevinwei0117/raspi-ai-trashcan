"""Smart Recycling Bin - full pipeline using the TrashNet-fine-tuned classifier.

Camera -> background-diff (restricted to a region of interest around the
tray, so background clutter/people don't trigger false detections) finds
the region that changed -> crop inward from that region (biased toward the
object's center, away from tray-glare at the edges) -> MobileNetV2
(fine-tuned on TrashNet) -> Recycle/Trash bin (src/category_map.py) ->
rotate platform to that bin -> tilt to drop.

The background is re-captured fresh after every sort (once the platform is
back at neutral), since the servos physically move the platform the camera
is watching. If "present" ever gets stuck true for too long we force a
background re-lock, regardless of whether a sort just happened.

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

ROI_X = 140
ROI_Y = 60
ROI_W = 360
ROI_H = 360

STABLE_FRAMES_REQUIRED = 2
MOTION_THRESHOLD = 6.0
MIN_BOX_AREA = 6000
BOX_PADDING_FRAC = -0.15  # negative = crop INWARD from the detected edges,
                          # away from tray glare/glow bleeding around the object

WARMUP_SECONDS = 2.0
BACKGROUND_AVERAGE_FRAMES = 10
POST_SORT_SETTLE_SECONDS = 0.5
STUCK_PRESENT_TIMEOUT = 4.0

DEFAULT_LOW_CONFIDENCE_BIN = "Trash"

DEBUG = True


def log(msg: str) -> None:
    print(msg, flush=True)


def resolve_bin(label: str, confidence: float, threshold: float) -> str:
    if confidence < threshold:
        return DEFAULT_LOW_CONFIDENCE_BIN
    return label_to_category(label)


def mean_diff(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())


def find_object_box(roi_frame: np.ndarray, roi_background: np.ndarray, diff_threshold: float):
    import cv2

    diff = np.abs(roi_frame.astype(np.int16) - roi_background.astype(np.int16)).astype(np.uint8)
    gray_diff = diff.mean(axis=2).astype(np.uint8)
    _, mask = cv2.threshold(gray_diff, int(diff_threshold), 255, cv2.THRESH_BINARY)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, 0.0

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < MIN_BOX_AREA:
        return None, area

    return cv2.boundingRect(largest), area


def crop_with_padding(roi_frame: np.ndarray, box) -> np.ndarray:
    x, y, w, h = box
    H, W = roi_frame.shape[:2]
    pad_x = int(w * BOX_PADDING_FRAC)
    pad_y = int(h * BOX_PADDING_FRAC)
    x0 = max(0, x - pad_x)
    y0 = max(0, y - pad_y)
    x1 = min(W, x + w + pad_x)
    y1 = min(H, y + h + pad_y)
    if x1 <= x0 or y1 <= y0:
        # box collapsed after inward crop (tiny object) - fall back to the
        # original uncropped detection instead of returning an empty image
        return roi_frame[y:y + h, x:x + w]
    return roi_frame[y0:y1, x0:x1]


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
        self.latest_result = {"label": "waiting...", "confidence": 0.0, "bin": None, "box": None}

        self._background: np.ndarray | None = None
        self._warmup_start: float | None = None
        self._warmup_frames: list[np.ndarray] = []

        self._previous_frame: np.ndarray | None = None
        self._still_streak = 0
        self._absent_streak = 0
        self._already_sorted = False
        self._present_since: float | None = None
        self._last_debug_print = 0.0

    def _get_latest_frame(self) -> np.ndarray | None:
        with self.frame_lock:
            return self.latest_frame

    def _roi(self, frame: np.ndarray) -> np.ndarray:
        return frame[ROI_Y:ROI_Y + ROI_H, ROI_X:ROI_X + ROI_W]

    def _start_background_capture(self) -> None:
        self._background = None
        self._warmup_start = None
        self._warmup_frames = []
        self._present_since = None
        self._still_streak = 0
        self._absent_streak = 0

    def _init_background(self, roi_frame: np.ndarray, warmup_seconds: float) -> bool:
        now = time.monotonic()
        if self._warmup_start is None:
            self._warmup_start = now

        if now - self._warmup_start < warmup_seconds:
            return False

        self._warmup_frames.append(roi_frame.astype(np.float32))
        if len(self._warmup_frames) < BACKGROUND_AVERAGE_FRAMES:
            return False

        self._background = np.mean(self._warmup_frames[-BACKGROUND_AVERAGE_FRAMES:], axis=0)
        self._previous_frame = roi_frame
        self._present_since = None
        log("Background locked in. Ready.")
        return True

    def ai_worker(self) -> None:
        first_background = True
        while self.running:
            try:
                frame = self._get_latest_frame()
                if frame is None:
                    time.sleep(0.02)
                    continue

                roi_frame = self._roi(frame)

                if self._background is None:
                    if first_background and self._warmup_start is None:
                        log("Warming up camera before locking in background...")
                    warmup = WARMUP_SECONDS if first_background else POST_SORT_SETTLE_SECONDS
                    if self._init_background(roi_frame, warmup):
                        first_background = False
                    time.sleep(0.05)
                    continue

                box, area = find_object_box(roi_frame, self._background, self.diff_threshold)
                present = box is not None
                motion = mean_diff(roi_frame, self._previous_frame) > MOTION_THRESHOLD
                self._previous_frame = roi_frame

                now = time.monotonic()
                if DEBUG and now - self._last_debug_print > 1.0:
                    log(f"[debug] present={present} area={area:.0f} motion={motion} already_sorted={self._already_sorted}")
                    self._last_debug_print = now

                if present:
                    if self._present_since is None:
                        self._present_since = now
                    elif (now - self._present_since) > STUCK_PRESENT_TIMEOUT:
                        log("Present too long with no resolution - assuming drift, re-locking background.")
                        self._start_background_capture()
                        self._already_sorted = False
                        self.latest_result = {"label": "waiting...", "confidence": 0.0, "bin": None, "box": None}
                        continue
                else:
                    self._present_since = None

                if present and not motion:
                    self._still_streak += 1
                    self._absent_streak = 0
                    x, y, w, h = box
                    self.latest_result["box"] = (x + ROI_X, y + ROI_Y, w, h)
                elif not present:
                    self._absent_streak += 1
                    self._still_streak = 0
                    self._background = 0.95 * self._background + 0.05 * roi_frame.astype(np.float32)
                else:
                    self._still_streak = 0

                if self._absent_streak >= STABLE_FRAMES_REQUIRED:
                    self._already_sorted = False
                    self.latest_result = {"label": "waiting...", "confidence": 0.0, "bin": None, "box": None}

                if self._still_streak >= STABLE_FRAMES_REQUIRED and not self._already_sorted:
                    from PIL import Image

                    crop = crop_with_padding(roi_frame, box)
                    (label, confidence), = self.classifier.predict(Image.fromarray(crop))
                    category = resolve_bin(label, confidence, self.confidence_threshold)
                    tag = f" (low-confidence -> {DEFAULT_LOW_CONFIDENCE_BIN})" if confidence < self.confidence_threshold else ""
                    x, y, w, h = box
                    self.latest_result = {
                        "label": label, "confidence": confidence, "bin": category,
                        "box": (x + ROI_X, y + ROI_Y, w, h),
                    }
                    log(f"Detected: {label} ({confidence * 100:.1f}%) -> {category}{tag}")

                    self.sorter.sort(category)

                    self._already_sorted = True
                    self._start_background_capture()
                    log("Re-locking background after sort...")
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
            cv2.resizeWindow("Smart Recycling Bin", 1024, 600)
            cv2.moveWindow("Smart Recycling Bin", 2560, 0)

        try:
            while True:
                frame = np.array(self.camera.capture())
                with self.frame_lock:
                    self.latest_frame = frame

                if cv2 is not None:
                    display = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.rectangle(display, (ROI_X, ROI_Y), (ROI_X + ROI_W, ROI_Y + ROI_H), (255, 128, 0), 1)

                    r = self.latest_result
                    color = (0, 165, 255) if r["confidence"] < self.confidence_threshold else (0, 255, 0)

                    box = r.get("box")
                    if box is not None:
                        x, y, w, h = box
                        cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)

                    text = f"{r['label']} ({r['confidence'] * 100:.0f}%) -> {r['bin']}"
                    cv2.putText(display, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.imshow("Smart Recycling Bin", display)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                else:
                    time.sleep(0.02)
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
    parser.add_argument("--diff-threshold", type=float, default=35.0)
    parser.add_argument("--cooldown", type=float, default=1.0)
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()

    bin_ = SmartBin(args.confidence_threshold, args.diff_threshold, args.cooldown)
    bin_.run(show_preview=not args.no_preview)


if __name__ == "__main__":
    main()
