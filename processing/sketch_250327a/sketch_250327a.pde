import processing.serial.*;

// === CONFIGURAÇÃO ===
boolean USE_SERIAL = false;  // true para usar a porta serial; false para mock aleatório
String PORT_NAME = "COM3";   // ajuste conforme necessário
int BAUD_RATE = 9600;

// === SENSOR SETUP ===
String[] channelNames = {
  "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "Clear", "Flicker", "NIR"
};

int[][] wavelengths = {
  {400, 410, 420}, {430, 440, 450}, {460, 470, 480}, {500, 510, 520},
  {540, 550, 560}, {573, 583, 593}, {610, 620, 630}, {660, 670, 680}
};

Serial myPort;
int[] sensorValues = new int[channelNames.length];
String incomingLine = "";

void setup() {
  size(900, 400);
  if (USE_SERIAL) {
    println("Available serial ports:");
    println(Serial.list());
    myPort = new Serial(this, PORT_NAME, BAUD_RATE);
    myPort.bufferUntil('\n');
  }
}

void draw() {
  background(255);
  drawAxes();
  drawBars();
}

void serialEvent(Serial port) {
  incomingLine = port.readStringUntil('\n');
  processLine(incomingLine);
}

void processLine(String line) {
  if (line == null) return;
  String[] parts = trim(split(line, ','));
  if (parts.length >= channelNames.length + 1) {
    for (int i = 0; i < channelNames.length; i++) {
      sensorValues[i] = int(parts[i]);
    }
  }
}

void drawAxes() {
  stroke(0);
  line(50, height - 50, width - 50, height - 50);
  line(50, height - 50, 50, 50);
  fill(0);
  textAlign(CENTER);
  for (int i = 0; i < channelNames.length; i++) {
    int x = int(map(i, 0, channelNames.length, 60, width - 60));
    text(channelNames[i], x, height - 30);
  }
}

void drawBars() {
  int barWidth = (width - 100) / channelNames.length;
  for (int i = 0; i < channelNames.length; i++) {
    int x = 60 + i * barWidth;
    int val = sensorValues[i];
    float barHeight = map(val, 0, 65535, 0, height - 100);
    int y = height - 50 - int(barHeight);

    if (i < 8) {
      // Degradê horizontal baseado em nanometria
      int[] wl = wavelengths[i];
      for (int j = 0; j < barWidth; j++) {
        float t = float(j) / barWidth;
        int nm = int(lerp(wl[0], wl[2], t));
        stroke(wavelengthToRGB(nm));
        line(x + j, height - 50, x + j, y);
      }
    } else {
      // Cores sólidas para Clear, Flicker, NIR
      color c = color(100 + i * 30, 100, 200);
      fill(c);
      noStroke();
      rect(x, y, barWidth - 4, barHeight);
    }
  }
}

// Função para gerar mock se não estiver usando serial
void keyPressed() {
  if (!USE_SERIAL && key == 'm') {
    for (int i = 0; i < sensorValues.length; i++) {
      sensorValues[i] = int(random(0, 65535));
    }
  }
}

// Mapeia comprimento de onda para cor RGB
color wavelengthToRGB(int wavelength) {
  float R = 0, G = 0, B = 0;
  if (wavelength >= 380 && wavelength < 440) {
    R = -(wavelength - 440) / (440 - 380.0);
    G = 0.0;
    B = 1.0;
  } else if (wavelength >= 440 && wavelength < 490) {
    R = 0.0;
    G = (wavelength - 440) / (490 - 440.0);
    B = 1.0;
  } else if (wavelength >= 490 && wavelength < 510) {
    R = 0.0;
    G = 1.0;
    B = -(wavelength - 510) / (510 - 490.0);
  } else if (wavelength >= 510 && wavelength < 580) {
    R = (wavelength - 510) / (580 - 510.0);
    G = 1.0;
    B = 0.0;
  } else if (wavelength >= 580 && wavelength < 645) {
    R = 1.0;
    G = -(wavelength - 645) / (645 - 580.0);
    B = 0.0;
  } else if (wavelength >= 645 && wavelength <= 780) {
    R = 1.0;
    G = 0.0;
    B = 0.0;
  }
  return color(R * 255, G * 255, B * 255);
}
