import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.category_map import label_to_category


def test_glass():
    assert label_to_category("glass") == "glass"


def test_metal():
    assert label_to_category("metal") == "metal"


def test_plastic():
    assert label_to_category("plastic") == "plastic"


def test_cardboard_paper_trash_are_other():
    assert label_to_category("cardboard") == "other"
    assert label_to_category("paper") == "other"
    assert label_to_category("trash") == "other"


def test_case_insensitive():
    assert label_to_category("GLASS") == "glass"


def test_unknown_label_defaults_other():
    assert label_to_category("something-unexpected") == "other"
