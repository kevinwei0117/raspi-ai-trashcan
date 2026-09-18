# Trash Classifier

Points a camera at an object, classifies it with a MobileNetV2 model
fine-tuned on TrashNet, and sorts it into one of 4 bins: `glass`, `metal`,
`plastic`, or `other` (cardboard, paper, and general trash).

Runs today on your Mac's built-in webcam for development, and is meant to move
onto a Raspberry Pi + camera module unchanged — `src/camera.py` and
`src/sorter.py`/`src/servo_sorter.py` auto-detect the platform (Pi hardware
vs. a laptop with no GPIO/servos) so no code changes are needed when you
deploy.

## How it works

1. `src/camera.py` grabs a frame (Pi Camera via `picamera2` on a Pi, OpenCV
   webcam capture elsewhere).
2. `src/classifier.py` runs it through `models/trashnet_mobilenet_v2.tflite`,
   a quantized MobileNetV2 fine-tuned on TrashNet (see "Training the model"
   below) — **82.6% validation accuracy** in the included run.
3. `src/category_map.py` maps the predicted TrashNet label (cardboard, glass,
   metal, paper, plastic, trash) to one of the 4 physical bins: glass and
   metal and plastic each get their own bin; cardboard, paper, and trash all
   go to `other`.
4. Sorting happens one of two ways (see below): `src/sorter.py` lights an LED
   per bin on Pi GPIO pins, or `src/servo_sorter.py` physically rotates a
   platform + tilts to drop the item.

## Training the model

```bash
pip install -r requirements.txt -r requirements-train.txt
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='garythung/trashnet', filename='dataset-resized.zip', repo_type='dataset', local_dir='data')"
cd data && unzip dataset-resized.zip && rm -rf dataset-resized.zip __MACOSX .cache && cd ..
python scripts/train_trashnet.py   # ~10-15 min on a laptop CPU
```

Produces `models/trashnet_mobilenet_v2.tflite` and `models/trashnet_labels.txt`,
which both `src/main.py` and `src/smart_bin.py` expect. This must be done
before either will run — there's no bundled fallback model.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then follow "Training the model" above.

## Run (Mac, for testing)

```bash
python -m src.main
```

The first run will prompt macOS for camera permission — grant it to your
terminal/IDE. Press Ctrl+C to stop. Output looks like:

```
plastic (0.94) -> plastic
cardboard (0.97) -> other
```

`--confidence-threshold` (default 0.4) skips low-confidence frames rather
than reporting an unreliable guess.

## Deploying to a Raspberry Pi

1. Install `picamera2` and `RPi.GPIO` (already in `requirements.txt`, gated to
   only install on ARM Linux).
2. Wire an LED (with resistor) per bin to the BCM pins in
   `src/sorter.py::CATEGORY_PINS` (17/27/22/23 by default) — optional, only
   needed if you want a physical indicator.
3. Copy this project (including `models/`, however you produced it) to the
   Pi, run `pip install -r requirements.txt` there, then `python -m src.main`.
   Training is CPU/memory-heavy — do it on your Mac and copy the resulting
   `.tflite`/labels files over rather than training on the Pi itself.

No code changes needed — `Camera` and `Sorter` detect the Pi automatically.

## Physical sorter: `src/smart_bin.py`

A second, hardware-driving pipeline for a physical 4-bin sorter, built around
a PCA9685 servo driver (`adafruit_servokit`) rather than the LED indicator
above:

```
Camera -> TrashClassifier (TrashNet model) -> category_map -> ServoBinSorter
```

- **Presence detection**: a whole-frame classifier has no "nothing here"
  signal the way an object detector does, so `smart_bin.py` diffs each frame
  against a rolling background average and only classifies + sorts once the
  scene changes enough (`--diff-threshold`, default mean pixel diff of 15/255)
  and stays changed for a few consecutive frames — then waits for the
  platform to look empty again before re-arming.
- **4 bins**: `src/servo_sorter.py` rotates a platform servo to one of 4
  evenly-spaced angles (0°/60°/120°/180°, one per bin: glass/metal/plastic/
  other), then tilts a second servo to drop the item.
- **Confidence cutoff**: below `--confidence-threshold` (default 0.40),
  always sorts to `other` rather than trusting a low-confidence guess.

**Before running unattended**, run `python scripts/calibrate_servo.py
--channel 8` (rotate) and `--channel 11` (tilt) to confirm the angles in
`src/servo_sorter.py` actually line up with your bin positions — the four
evenly-spaced angles are a starting guess, not a calibrated value, and a
wrong angle drops the item between bins instead of into one.

```bash
python -m src.smart_bin              # with preview window
python -m src.smart_bin --no-preview # headless
```

Runs fine on a Mac for logic testing — `ServoBinSorter` no-ops and prints
what it would do when `adafruit_servokit`/the PCA9685 board aren't present.

## Tests

```bash
pip install pytest
pytest tests/
```
