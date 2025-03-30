import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import unittest
from src.spectrum import Spectrum

class TestSpectrum(unittest.TestCase):

    def setUp(self):
        self.spectrum = Spectrum()

    def test_get_channels(self):
        channels = self.spectrum.get_channels()
        self.assertEqual(len(channels), 8)  # Should have 8 channels for the AS7341 sensor

    def test_read_spectrum(self):
        spectrum_data = self.spectrum.read_spectrum()
        self.assertIsInstance(spectrum_data, dict)

if __name__ == "__main__":
    unittest.main()
