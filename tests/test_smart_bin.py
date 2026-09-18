import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.smart_bin import frame_changed, resolve_bin


def test_resolve_bin_plastic():
    assert resolve_bin("plastic", 0.9, threshold=0.4) == "plastic"


def test_resolve_bin_trash_label_maps_to_other():
    assert resolve_bin("trash", 0.9, threshold=0.4) == "other"


def test_resolve_bin_low_confidence_defaults_other():
    assert resolve_bin("plastic", 0.2, threshold=0.4) == "other"


def test_frame_changed_detects_difference():
    background = np.zeros((10, 10, 3), dtype=np.uint8)
    frame = np.full((10, 10, 3), 200, dtype=np.uint8)
    assert frame_changed(frame, background, diff_threshold=15.0) is True


def test_frame_changed_ignores_noise():
    background = np.full((10, 10, 3), 100, dtype=np.uint8)
    frame = background.copy()
    frame[0, 0, 0] = 102  # tiny single-pixel noise
    assert frame_changed(frame, background, diff_threshold=15.0) is False
