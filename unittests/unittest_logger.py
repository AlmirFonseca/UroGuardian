import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.logger import Logger
from src.config_manager import ConfigManager
from unittest.mock import patch

class TestLogger(unittest.TestCase):

    def setUp(self):
        # Mock ConfigManager para controlar o nível inicial
        self.patcher = patch('src.config_manager.ConfigManager.get')
        self.mock_get = self.patcher.start()
        self.mock_get.return_value = {"level": "INFO"}

        self.logger = Logger()

    def tearDown(self):
        self.patcher.stop()

    def test_initialization(self):
        self.assertEqual(self.logger.level, Logger.LEVELS["INFO"])
        self.assertTrue(self.logger.show_tag)

    def test_set_level(self):
        self.logger.set_level("DEBUG")
        self.assertEqual(self.logger.level, Logger.LEVELS["DEBUG"])
        self.logger.set_level("ERROR")
        self.assertEqual(self.logger.level, Logger.LEVELS["ERROR"])

    def test_enable_disable_tags(self):
        self.logger.disable_tags()
        self.assertFalse(self.logger.show_tag)
        self.logger.enable_tags()
        self.assertTrue(self.logger.show_tag)

    @patch('builtins.print')
    def test_print(self, mock_print):
        self.logger.set_level("INFO")
        self.logger.print("Test Message", "INFO")
        mock_print.assert_called_with("[INF] Test Message", end="")

        self.logger.disable_tags()
        self.logger.print("No Tag Message", "INFO")
        mock_print.assert_called_with("No Tag Message", end="")

        self.logger.set_level("ERROR")
        self.logger.print("Should not print", "INFO")
        mock_print.assert_called_with("No Tag Message", end="")  # Não muda, pois não deve chamar novamente

    @patch('builtins.print')
    def test_println(self, mock_print):
        self.logger.println("Line Message", "WARNING")
        mock_print.assert_called_with("[WRN] Line Message\n", end="")

    @patch('builtins.print')
    def test_print_separator(self, mock_print):
        self.logger.print_separator(level="DEBUG", sep_type="=", size=10)
        mock_print.assert_called_with("[DBG] ==========\n", end="")

        self.logger.disable_tags()
        self.logger.print_separator(level="INFO", sep_type="-", size=5)
        mock_print.assert_called_with("-----\n", end="")

if __name__ == "__main__":
    unittest.main()

