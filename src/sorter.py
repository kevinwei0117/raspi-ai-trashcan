"""Drives an optional physical indicator (LEDs) per trash category on Pi GPIO.

Wiring is a suggestion, not a requirement: each category lights one LED (with an
inline resistor) on the pin below. If RPi.GPIO isn't available (e.g. running on a
laptop for testing), this becomes a no-op so the rest of the pipeline still runs.
"""
from __future__ import annotations

CATEGORY_PINS = {
    "glass": 17,
    "metal": 27,
    "plastic": 22,
    "other": 23,
}


class Sorter:
    def __init__(self):
        self._gpio = None
        try:
            import RPi.GPIO as GPIO

            self._gpio = GPIO
            self._gpio.setmode(GPIO.BCM)
            for pin in CATEGORY_PINS.values():
                self._gpio.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        except (ImportError, RuntimeError):
            self._gpio = None  # not on a Pi, or GPIO unavailable

    def indicate(self, category: str) -> None:
        if self._gpio is None:
            return
        for cat, pin in CATEGORY_PINS.items():
            self._gpio.output(pin, self._gpio.HIGH if cat == category else self._gpio.LOW)

    def close(self) -> None:
        if self._gpio is not None:
            self._gpio.cleanup()

    def __enter__(self) -> "Sorter":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
