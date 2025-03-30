import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import unittest
from src.logger import Logger

class TestLogger(unittest.TestCase):

    def setUp(self):
        self.logger = Logger()

    def test_log_level(self):
        self.logger.set_log_level("DEBUG")
        self.assertEqual(self.logger.log_level, "DEBUG")
        self.logger.log("INFO", "This is an info log.")
        self.logger.log("ERROR", "This is an error log.")

if __name__ == "__main__":
    unittest.main()
