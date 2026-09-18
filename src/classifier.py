"""TFLite MobileNetV2 image classifier."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:  # dev machines without tflite-runtime installed
    from tensorflow.lite.python.interpreter import Interpreter


class TrashClassifier:
    def __init__(self, model_path: str | Path, labels_path: str | Path, top_k: int = 1):
        self._interpreter = Interpreter(model_path=str(model_path))
        self._interpreter.allocate_tensors()
        self._input_details = self._interpreter.get_input_details()[0]
        self._output_details = self._interpreter.get_output_details()[0]
        self._input_size = self._input_details["shape"][1:3]  # (height, width)
        self._labels = _load_labels(labels_path)
        self.top_k = top_k

    def predict(self, image: Image.Image) -> list[tuple[str, float]]:
        """Return up to top_k (label, confidence) pairs, most confident first."""
        tensor = self._preprocess(image)
        self._interpreter.set_tensor(self._input_details["index"], tensor)
        self._interpreter.invoke()
        output = self._interpreter.get_tensor(self._output_details["index"])[0]

        if self._output_details["dtype"] == np.uint8:
            scale, zero_point = self._output_details["quantization"]
            output = (output.astype(np.float32) - zero_point) * scale
            # Some models end in a softmax layer, so the dequantized output is
            # already a probability distribution (sums to ~1); others output
            # raw logits. Applying softmax to an already-softmaxed output
            # flattens it toward uniform, so only apply it when needed.
            if not np.isclose(output.sum(), 1.0, atol=0.05):
                output = _softmax(output)

        top_indices = np.argsort(output)[-self.top_k :][::-1]
        return [(self._labels[i], float(output[i])) for i in top_indices]

    def _preprocess(self, image: Image.Image) -> np.ndarray:
        resized = image.convert("RGB").resize(tuple(self._input_size[::-1]))
        array = np.asarray(resized)

        if self._input_details["dtype"] == np.uint8:
            array = array.astype(np.uint8)
        else:
            array = (array.astype(np.float32) / 127.5) - 1.0

        return np.expand_dims(array, axis=0)


def _load_labels(labels_path: str | Path) -> list[str]:
    with open(labels_path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    return exp / np.sum(exp)
