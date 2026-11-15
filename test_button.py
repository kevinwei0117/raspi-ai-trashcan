"""Safe test - just prints the GPIO21 pin state every 0.2s. No shutdown."""
import time
import lgpio

GPIO_PIN = 21

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, GPIO_PIN, lgpio.SET_PULL_UP)

print("Watching pin 21. Press Ctrl+C to stop.")
try:
    while True:
        level = lgpio.gpio_read(h, GPIO_PIN)
        state = "PRESSED (low)" if level == 0 else "not pressed (high)"
        print(f"pin21 = {level}  ->  {state}")
        time.sleep(0.3)
except KeyboardInterrupt:
    pass
finally:
    lgpio.gpiochip_close(h)
