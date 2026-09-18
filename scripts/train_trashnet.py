"""Fine-tunes MobileNetV2 (starting from ImageNet-pretrained weights) on the
TrashNet dataset and exports a quantized TFLite model in the input/output
format src/classifier.py expects (uint8 in, uint8-quantized softmax out).

Usage:
    python scripts/train_trashnet.py [--data-dir data/dataset-resized] [--epochs 10]

Requires the TrashNet images already downloaded to --data-dir, one
subdirectory per class (cardboard/glass/metal/paper/plastic/trash) — see
README.md for how to fetch it.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import tensorflow as tf

IMG_SIZE = (224, 224)
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


def build_model(num_classes: int) -> tf.keras.Model:
    base = tf.keras.applications.MobileNetV2(
        input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet"
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    return model, base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/dataset-resized")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--fine-tune-epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="training", seed=42,
        image_size=IMG_SIZE, batch_size=args.batch_size,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="validation", seed=42,
        image_size=IMG_SIZE, batch_size=args.batch_size,
    )
    class_names = train_ds.class_names
    print(f"Classes ({len(class_names)}): {class_names}")

    augment = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.1),
        tf.keras.layers.RandomZoom(0.1),
    ])
    train_ds = train_ds.map(lambda x, y: (augment(x, training=True), y))

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.cache().prefetch(autotune)
    val_ds = val_ds.cache().prefetch(autotune)

    model, base = build_model(len(class_names))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    print("Training classifier head...")
    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs)

    print("Fine-tuning top of base model...")
    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-5),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(train_ds, validation_data=val_ds, epochs=args.fine_tune_epochs)

    val_loss, val_acc = model.evaluate(val_ds)
    print(f"Final validation accuracy: {val_acc:.3f}")

    MODEL_DIR.mkdir(exist_ok=True)

    def representative_dataset():
        for images, _ in train_ds.unbatch().batch(1).take(100):
            yield [tf.cast(images, tf.float32)]

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.uint8
    converter.inference_output_type = tf.uint8
    tflite_model = converter.convert()

    model_path = MODEL_DIR / "trashnet_mobilenet_v2.tflite"
    model_path.write_bytes(tflite_model)

    labels_path = MODEL_DIR / "trashnet_labels.txt"
    labels_path.write_text("\n".join(class_names) + "\n")

    print(f"Saved {model_path} and {labels_path}")


if __name__ == "__main__":
    main()
