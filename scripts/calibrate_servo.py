"""Servo Calibration

Type an angle and press Enter to move the servo there, so you can find the
real neutral/flat position and drop angle for your physical build. Update the
angle constants in src/servo_sorter.py with whatever you find here.

Usage:
    python scripts/calibrate_servo.py [--channel 8]
"""
from __future__ import annotations

import argparse

from adafruit_servokit import ServoKit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--channel", type=int, default=8,
        help="Servo channel to test (8 = rotate, 11 = tilt, per src/servo_sorter.py)",
    )
    args = parser.parse_args()

    kit = ServoKit(channels=16)

    print("Servo Calibration")
    print(f"Testing channel {args.channel}")
    print("Type an angle (0-180) and press Enter to move there.")
    print("Type 'q' to quit.\n")

    kit.servo[args.channel].angle = 90
    print("Starting at 90 degrees.")

    while True:
        user_input = input("\nEnter angle (0-180) or 'q' to quit: ").strip()

        if user_input.lower() == "q":
            break

        try:
            angle = int(user_input)
            if 0 <= angle <= 180:
                kit.servo[args.channel].angle = angle
                print(f"Moved to {angle} degrees.")
            else:
                print("Please enter a number between 0 and 180.")
        except ValueError:
            print("Please enter a valid number, or 'q' to quit.")

    print("\nDone. Note down the angles that worked!")


if __name__ == "__main__":
    main()
