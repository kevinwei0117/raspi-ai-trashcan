"""Maps TrashNet class labels to physical sort bins.

The TrashNet-fine-tuned classifier (see scripts/train_trashnet.py) predicts
one of 6 material classes directly: cardboard, glass, metal, paper, plastic,
trash. These collapse to 4 physical bins - glass, metal, and plastic each get
their own bin, and everything else (cardboard, paper, trash) goes to "other".
"""
from __future__ import annotations

CATEGORIES = ("glass", "metal", "plastic", "other")

_LABEL_TO_CATEGORY = {
    "glass": "glass",
    "metal": "metal",
    "plastic": "plastic",
    "cardboard": "other",
    "paper": "other",
    "trash": "other",
}

_DEFAULT_CATEGORY = "other"


def label_to_category(label: str) -> str:
    """Map a predicted TrashNet label to a physical sort bin."""
    return _LABEL_TO_CATEGORY.get(label.lower(), _DEFAULT_CATEGORY)
