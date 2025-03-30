import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import unittest
from unittest.mock import patch, MagicMock
import RPi.GPIO as GPIO

from src.led import RGBLED
from src.config_manager import ConfigManager

class TestRGBLED(unittest.TestCase):

    def setUp(self):
        # Mock ConfigManager para simular os arquivos de configuração
        self.config_manager = MagicMock(ConfigManager)
        self.config_manager.get.return_value = {
            "pins": {"LED_R": 17, "LED_G": 27, "LED_B": 22},
            "conf": {"brightness": 50, "led_type": "common_anode"}
        }

        # Mock de GPIO
        GPIO.setmode = MagicMock()
        GPIO.setup = MagicMock()
        GPIO.output = MagicMock()
        GPIO.cleanup = MagicMock()

        # Inicializa o controlador do LED RGB
        self.led = RGBLED(self.config_manager)

    def test_initialization(self):
        # Verifica se a configuração de pinos foi lida corretamente
        self.assertEqual(self.led.red_pin, 17)
        self.assertEqual(self.led.green_pin, 27)
        self.assertEqual(self.led.blue_pin, 22)
        
        # Verifica o valor de brilho padrão
        self.assertEqual(self.led.brightness, 50)
        
        # Verifica o tipo do LED (comum anodo)
        self.assertEqual(self.led.led_type, "common_anode")
        
        # Verifica se os pinos foram configurados corretamente
        GPIO.setup.assert_called_with([17, 27, 22], GPIO.OUT)

    def test_set_color(self):
        # Testa a definição da cor do LED RGB
        with patch.object(self.led, '_adjust_brightness') as mock_adjust_brightness:
            self.led.set_color(100, 50, 25)
            mock_adjust_brightness.assert_any_call(17, 100)  # LED R
            mock_adjust_brightness.assert_any_call(27, 50)   # LED G
            mock_adjust_brightness.assert_any_call(22, 25)   # LED B

    def test_set_individual_color(self):
        # Testa o ajuste de brilho de uma cor individual
        with patch.object(self.led, '_adjust_brightness') as mock_adjust_brightness:
            self.led.set_individual_color('R', 75)
            mock_adjust_brightness.assert_called_with(17, 75)

            self.led.set_individual_color('G', 50)
            mock_adjust_brightness.assert_called_with(27, 50)

            self.led.set_individual_color('B', 25)
            mock_adjust_brightness.assert_called_with(22, 25)

    def test_set_individual_color_invalid(self):
        # Testa se ValueError é lançado quando a cor fornecida é inválida
        with self.assertRaises(ValueError):
            self.led.set_individual_color('X', 75)

    def test_turn_off(self):
        # Testa se o LED é desligado
        with patch.object(self.led, 'set_color') as mock_set_color:
            self.led.turn_off()
            mock_set_color.assert_called_with(0, 0, 0)

    def test_cleanup(self):
        # Testa a limpeza dos GPIOs
        self.led.cleanup()
        GPIO.cleanup.assert_called_once()

if __name__ == "__main__":
    unittest.main()
