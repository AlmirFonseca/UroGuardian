import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from src.led import RGBLED
from src.config_manager import ConfigManager
import time

def led_demo():
    config_manager = ConfigManager()
    led = RGBLED(config_manager)

    # Definindo a cor do LED RGB
    print("Setting LED color to red=100, green=50, blue=25...")
    led.set_color(100, 50, 25)

    # Ajustando a cor individualmente
    print("Setting individual color for Red to 75...")
    led.set_individual_color('R', 75)

    print("Setting individual color for Green to 50...")
    led.set_individual_color('G', 50)

    print("Setting individual color for Blue to 25...")
    led.set_individual_color('B', 25)

    # Desligando o LED
    print("Turning off the LED...")
    led.turn_off()

    # Realizando a limpeza dos GPIO
    print("Cleaning up GPIO...")
    led.cleanup()

if __name__ == "__main__":
    led_demo()
