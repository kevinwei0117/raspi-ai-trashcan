"""Maps TrashNet class labels to physical sort bins.

The TrashNet-fine-tuned classifier predicts one of 6 material classes:
cardboard, glass, metal, paper, plastic, trash. These collapse to our 2
physical bins: everything recyclable goes to "Recycle", genuine trash goes
to "Trash".
"""
from __future__ import annotations

CATEGORIES = ("Recycle", "Trash")

_LABEL_TO_CATEGORY = {
    "glass": "Recycle",
    "metal": "Recycle",
    "plastic": "Recycle",
    "cardboard": "Recycle",
    "paper": "Recycle",
    "trash": "Trash",
}

_DEFAULT_CATEGORY = "Trash"


def label_to_category(label: str) -> str:
    """Map a predicted TrashNet label to a physical sort bin."""
    return _LABEL_TO_CATEGORY.get(label.lower(), _DEFAULT_CATEGORY)
