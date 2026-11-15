"""Holds GPIO21 low (button pressed, wired to GND) for 2 seconds -> safely
shuts down the Pi. Talks to the GPIO pin directly via lgpio instead of
gpiozero, since gpiozero's automatic pin-driver detection isn't working
correctly on this system."""
import time
import subprocess
import lgpio

GPIO_PIN = 12
HOLD_SECONDS = 2.0

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, GPIO_PIN, lgpio.SET_PULL_UP)

print("[shutdown button] Ready. Hold the button for 2 seconds to shut down.")

held_since = None
try:
    while True:
        level = lgpio.gpio_read(h, GPIO_PIN)
        pressed = (level == 0)  # pulled low when pressed (other leg wired to GND)

        if pressed:
            if held_since is None:
                held_since = time.time()
            elif time.time() - held_since >= HOLD_SECONDS:
                print("[shutdown button] Held for 2 seconds - shutting down safely...")
                subprocess.run(["sudo", "shutdown", "-h", "now"])
                break
        else:
            held_since = None

        time.sleep(0.05)
finally:
    lgpio.gpiochip_close(h)
