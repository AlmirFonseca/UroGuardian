import RPi.GPIO as GPIO
import time
from typing import Dict, Any

from src.config_manager import ConfigManager

class RGBLED:
    """Classe para controlar um LED RGB analógico com ajuste de brilho baseado em porcentagem.
    
    A classe permite controlar um LED RGB comum (anodo ou cátodo comum) e ajustar o brilho de cada cor utilizando um valor de brilho em porcentagem (0-100%).
    As configurações de GPIO e brilho são lidas dos arquivos de configuração 'pins.yaml' e 'conf.yaml'.

    Attributes:
        gpio_pins (Dict[str, int]): Dicionário com os pinos GPIO para as cores R, G e B.
        brightness (int): Percentual de brilho do LED (0 a 100%).
        led_type (str): Tipo de LED ('common_anode' ou 'common_cathode').
        red_pin (int): Pino GPIO para o LED vermelho.
        green_pin (int): Pino GPIO para o LED verde.
        blue_pin (int): Pino GPIO para o LED azul.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """Inicializa o controlador do LED RGB.
        
        Args:
            config_manager (ConfigManager): Instância do gerenciador de configurações para carregar as configurações do arquivo.
        
        Raises:
            ValueError: Se a GPIO não estiver disponível ou não puder se corretamente inicializada.
        """
        # Carregar configurações de pinos e brilho
        self.config_manager = config_manager
        self.gpio_pins = self.config_manager.get("pins")
        self.brightness = self.config_manager.get("conf").get("brightness", 50)  # Default: 50%
        self.led_type = self.config_manager.get("conf").get("led_type", "common_anode")  # Default: common_anode

        # Armazena os pinos de cada cor
        self.red_pin = self.gpio_pins['LED_R']
        self.green_pin = self.gpio_pins['LED_G']
        self.blue_pin = self.gpio_pins['LED_B']

        # Configuração de GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.red_pin, self.green_pin, self.blue_pin], GPIO.OUT)

        # Inicializa o estado do LED com base no tipo
        self.invert_logic = self.led_type == "common_anode"
        
        # Inicializa os LEDs com o brilho configurado
        self.set_color(self.brightness, self.brightness, self.brightness)

    def _adjust_brightness(self, pin: int, brightness: int) -> None:
        """Ajusta o brilho de um LED individual.
        
        Args:
            pin (int): O pino GPIO para o LED (R, G ou B).
            brightness (int): O valor de brilho (0 a 100%).
        
        Returns:
            None
        """
        if self.invert_logic:
            brightness = 100 - brightness  # Inverte a lógica para anodo comum
        pwm_duty = (brightness / 100) * 100  # Ajusta o brilho proporcional ao valor (0 a 100)
        GPIO.output(pin, pwm_duty)

    def set_color(self, red: int, green: int, blue: int) -> None:
        """Define a cor do LED RGB com valores de brilho individuais para R, G e B.
        
        Args:
            red (int): Valor de brilho para o LED vermelho (0 a 100%).
            green (int): Valor de brilho para o LED verde (0 a 100%).
            blue (int): Valor de brilho para o LED azul (0 a 100%).
        
        Returns:
            None
        """
        self._adjust_brightness(self.red_pin, red)
        self._adjust_brightness(self.green_pin, green)
        self._adjust_brightness(self.blue_pin, blue)

    def set_individual_color(self, color: str, brightness: int) -> None:
        """Define o brilho de uma cor individualmente (R, G ou B).
        
        Args:
            color (str): Cor a ser ajustada ('R', 'G' ou 'B').
            brightness (int): Valor de brilho (0 a 100%).
        
        Returns:
            None
            
        Raises:
            ValueError: Se a cor fornecida não for válida.
        """
        if color == 'R':
            self._adjust_brightness(self.red_pin, brightness)
        elif color == 'G':
            self._adjust_brightness(self.green_pin, brightness)
        elif color == 'B':
            self._adjust_brightness(self.blue_pin, brightness)
        else:
            raise ValueError("Cor inválida. Use 'R', 'G' ou 'B'.")

    def turn_off(self) -> None:
        """Desliga completamente o LED RGB, colocando o brilho de todas as cores em 0%.
        
        Args:
            None
        
        Returns:
            None
        """
        self.set_color(0, 0, 0)

    def cleanup(self) -> None:
        """Desfaz todas as configurações do GPIO e encerra o uso do PWM.
        
        Args:
            None
        
        Returns:
            None
        """
        GPIO.cleanup()
