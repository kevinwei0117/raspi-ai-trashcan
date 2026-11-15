"""Live button state monitor - prints PRESSED/RELEASED continuously.
Use this to confirm wiring/pin before trusting the shutdown script."""
import time
import lgpio

GPIO_PIN = 12

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, GPIO_PIN, lgpio.SET_PULL_UP)

print(f"[monitor] Watching GPIO{GPIO_PIN}. Press Ctrl+C to stop.")

last_state = None
try:
    while True:
        level = lgpio.gpio_read(h, GPIO_PIN)
        pressed = (level == 0)

        if pressed != last_state:
            print("[monitor] PRESSED" if pressed else "[monitor] RELEASED")
            last_state = pressed

        time.sleep(0.05)
finally:
    lgpio.gpiochip_close(h)
