"""Drives the two-servo physical sorter: a rotate servo that swaps which of
two bins sits under the drop chute, and a tilt servo that drops the item.

Hardware: a PCA9685 servo driver via adafruit_servokit.

All angles below are RAW values sent directly to the servo - no offset or
conversion math. Re-run the manual calibration one-liner and update these
five numbers if the physical build changes.
"""
from __future__ import annotations

import time

TILT_CHANNEL = 11
TILT_NEUTRAL_ANGLE = 30
TILT_DROP_ANGLE = 120

ROTATE_CHANNEL = 8
ROTATE_NEUTRAL_ANGLE = 90
ROTATE_RECYCLE_ANGLE = 0
ROTATE_TRASH_ANGLE = 180

BIN_ROTATE_ANGLES = {
    "Recycle": ROTATE_RECYCLE_ANGLE,
    "Trash": ROTATE_TRASH_ANGLE,
}


class ServoBinSorter:
    def __init__(self):
        self._kit = None
        try:
            from adafruit_servokit import ServoKit

            self._kit = ServoKit(channels=16)
            self._kit.servo[TILT_CHANNEL].angle = TILT_NEUTRAL_ANGLE
            self._kit.servo[ROTATE_CHANNEL].angle = ROTATE_NEUTRAL_ANGLE
            print("[servo sorter] Hardware initialized successfully.")
        except Exception as e:
            print(f"[servo sorter] !! Failed to initialize hardware: {type(e).__name__}: {e}")
            self._kit = None

    def sort(self, category: str) -> None:
        """Rotate to the bin for `category`, tilt down to drop the item,
        then tilt back and rotate back to neutral."""
        rotate_angle = BIN_ROTATE_ANGLES.get(category, ROTATE_TRASH_ANGLE)

        if self._kit is None:
            print(f"[servo sorter] (no hardware) would rotate to {rotate_angle}, "
                  f"tilt to {TILT_DROP_ANGLE}, tilt back to {TILT_NEUTRAL_ANGLE}")
            return

        try:
            self._kit.servo[ROTATE_CHANNEL].angle = rotate_angle
            time.sleep(1.0)

            self._kit.servo[TILT_CHANNEL].angle = TILT_DROP_ANGLE
            time.sleep(1.3)
        finally:
            self._kit.servo[TILT_CHANNEL].angle = TILT_NEUTRAL_ANGLE
            time.sleep(0.4)
            self._kit.servo[ROTATE_CHANNEL].angle = ROTATE_NEUTRAL_ANGLE
            time.sleep(0.8)

    def close(self) -> None:
        pass

    def __enter__(self) -> "ServoBinSorter":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
