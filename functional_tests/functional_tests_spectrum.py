from src.spectrum import Spectrum

spectrum = Spectrum()

# Get spectrum data from the sensor
spectrum_data = spectrum.read_spectrum()

# Display the spectrum data
print(f"Spectrum data: {spectrum_data}")
