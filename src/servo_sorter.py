"""Drives the two-servo physical sorter: a rotate servo that swaps which of
four bins sits under the drop chute, and a tilt servo that drops the item.

Hardware: a PCA9685 servo driver via adafruit_servokit. Falls back to a no-op
(prints what it would do) when adafruit_servokit or the board isn't available,
so the rest of the pipeline still runs on a Mac for development.

Angles below are calibrated for a specific physical build — re-run
scripts/calibrate_servo.py after any rebuild and update these if they drift.

CAUTION: BIN_ROTATE_ANGLES assumes four bin positions evenly spaced across
the rotate servo's 0-180 degree range (one every 60 degrees). The original
build only had positions calibrated at 0 and 180 for two bins — confirm your
physical platform actually has four aligned bin slots at these angles (via
scripts/calibrate_servo.py) before running unattended; a wrong angle means
the item drops between bins instead of into one.
"""
from __future__ import annotations

import time

# Servo 1: rotates the platform to align one of four bins under the drop chute.
ROTATE_CHANNEL = 8
ROTATE_NEUTRAL_ANGLE = 90

# Servo 2: always tilts the same direction to drop the item, since the
# platform itself already rotated to the correct bin. Physical "flat" is 30
# degrees, not 90 - TILT_OFFSET converts logical angles (90 = flat) to the
# servo's real physical angle.
TILT_CHANNEL = 11
TILT_OFFSET = 60
TILT_NEUTRAL_ANGLE = 90
TILT_DROP_ANGLE = 150

# category -> rotate angle, matching category_map.CATEGORIES. Verify these
# against your actual bin layout.
BIN_ROTATE_ANGLES = {
    "glass": 0,
    "metal": 60,
    "plastic": 120,
    "other": 180,
}


class ServoBinSorter:
    def __init__(self):
        self._kit = None
        try:
            from adafruit_servokit import ServoKit

            self._kit = ServoKit(channels=16)
            self._set_tilt(TILT_NEUTRAL_ANGLE)
            self._kit.servo[ROTATE_CHANNEL].angle = ROTATE_NEUTRAL_ANGLE
        except (ImportError, NotImplementedError, ValueError):
            self._kit = None  # not on a Pi, or no PCA9685 board attached

    def _set_tilt(self, logical_angle: float) -> None:
        physical_angle = max(0, min(180, logical_angle - TILT_OFFSET))
        self._kit.servo[TILT_CHANNEL].angle = physical_angle

    def sort(self, category: str) -> None:
        """Rotate the platform to `category` ('glass'/'metal'/'plastic'/'other')
        and drop the item."""
        rotate_angle = BIN_ROTATE_ANGLES.get(category, BIN_ROTATE_ANGLES["other"])

        if self._kit is None:
            print(f"[servo sorter] (no hardware) would rotate to {rotate_angle} deg "
                  f"({category}), tilt to drop, then reset")
            return

        self._kit.servo[ROTATE_CHANNEL].angle = rotate_angle
        time.sleep(1.0)

        self._set_tilt(TILT_DROP_ANGLE)
        time.sleep(1.3)

        self._set_tilt(TILT_NEUTRAL_ANGLE)
        time.sleep(0.4)
        self._kit.servo[ROTATE_CHANNEL].angle = ROTATE_NEUTRAL_ANGLE
        time.sleep(0.8)

    def close(self) -> None:
        pass  # ServoKit needs no explicit cleanup

    def __enter__(self) -> "ServoBinSorter":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
