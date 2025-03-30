import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.led import RGBLed

led = RGBLed(dt_pin=5, sck_pin=6)  # Sample pins

# Set color and brightness
led.set_color(255, 0, 0)  # Red
led.set_brightness(50)

# Display current color and brightness
print(f"LED color: {led.get_color()}")
print(f"LED brightness: {led.get_brightness()}")
