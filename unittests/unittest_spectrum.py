import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import unittest
from unittest.mock import patch, MagicMock
import board

from src.spectrum import SpectrumSensor

class TestSpectrumSensor(unittest.TestCase):

    def setUp(self):
        # Mock ConfigManager para simular os arquivos de configuração
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = {
            "pins": {"LED_R": 17, "LED_G": 27, "LED_B": 22},
            "conf": {"brightness": 50, "led_type": "common_anode"}
        }

        # Cria o objeto SpectrumSensor
        self.spectrum = SpectrumSensor(i2c_bus=board.I2C())

    @patch.object(SpectrumSensor, 'read_channel', return_value=100)
    def test_read_channel(self, mock_read_channel):
        # Testa leitura de um canal específico
        reading = self.spectrum.read_channel("415nm")
        self.assertEqual(reading, 100)
        mock_read_channel.assert_called_with("415nm")

    @patch.object(SpectrumSensor, 'read_all_channels', return_value=(100, 150, 200, 250, 300, 350, 400, 450, 500, 550))
    def test_read_all_channels(self, mock_read_all_channels):
        # Testa a leitura de todos os canais
        readings = self.spectrum.read_all_channels()
        self.assertEqual(readings, (100, 150, 200, 250, 300, 350, 400, 450, 500, 550))

    @patch.object(SpectrumSensor, 'enable_flicker_detection')
    def test_enable_flicker_detection(self, mock_enable_flicker_detection):
        # Testa a habilitação da detecção de flicker
        self.spectrum.enable_flicker_detection(True)
        mock_enable_flicker_detection.assert_called_with(True)

    @patch.object(SpectrumSensor, 'get_flicker_detection_status', return_value=60)
    def test_get_flicker_detection_status(self, mock_get_flicker_detection_status):
        # Testa a obtenção do status da detecção de flicker
        status = self.spectrum.get_flicker_detection_status()
        self.assertEqual(status, 60)
        mock_get_flicker_detection_status.assert_called()

    @patch.object(SpectrumSensor, 'toggle_led')
    def test_toggle_led(self, mock_toggle_led):
        # Testa a ativação/desativação do LED
        self.spectrum.toggle_led(True)
        mock_toggle_led.assert_called_with(True)

    @patch.object(SpectrumSensor, 'set_led_current')
    def test_set_led_current(self, mock_set_led_current):
        # Testa o ajuste da corrente do LED
        self.spectrum.set_led_current(50)
        mock_set_led_current.assert_called_with(50)

    @patch('builtins.print')
    @patch.object(SpectrumSensor, 'read_channel', return_value=100)
    def test_display_channel_readings(self, mock_read_channel, mock_print):
        # Testa a exibição das leituras dos canais
        self.spectrum.display_channel_readings(["415nm", "555nm"])
        mock_print.assert_any_call("415nm: 100")
        mock_print.assert_any_call("555nm: 100")

    @patch('builtins.print')
    @patch.object(SpectrumSensor, 'read_all_channels', return_value=(100, 150, 200, 250, 300, 350, 400, 450, 500, 550))
    def test_display_all_channel_readings(self, mock_read_all_channels, mock_print):
        # Testa a exibição das leituras de todos os canais
        self.spectrum.display_all_channel_readings()
        mock_print.assert_any_call("415nm: 100")
        mock_print.assert_any_call("445nm: 150")
        mock_print.assert_any_call("680nm: 450")

if __name__ == "__main__":
    unittest.main()
