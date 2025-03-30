import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.spectrum import Spectrum

spectrum = Spectrum()

# Get spectrum data from the sensor
spectrum_data = spectrum.read_spectrum()

# Display the spectrum data
print(f"Spectrum data: {spectrum_data}")
