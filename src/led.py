import RPi.GPIO as GPIO
import time
from typing import Dict, Any
from src.config_manager import ConfigManager


class LED:
    """Classe base para controlar um LED com ajuste de brilho baseado em porcentagem.
    
    A classe permite controlar um LED analógico e ajustar o brilho utilizando um valor de brilho em porcentagem (0-100%).
    As configurações de GPIO e brilho são lidas dos arquivos de configuração 'pins.yaml' e 'conf.yaml'.
    """

    def __init__(self, config_manager: ConfigManager, gpio_pin: int, default_brightness: int = 50) -> None:
        """Inicializa o controlador do LED.

        Args:
            config_manager (ConfigManager): Instância do gerenciador de configurações para carregar as configurações do arquivo.
            gpio_pin (int): Pino GPIO para o LED.
            default_brightness (int, opcional): Percentual de brilho inicial (default é 50%).
        """
        # Carregar configurações de pino e brilho
        self.config_manager = config_manager
        self.gpio_pin = gpio_pin
        self.brightness = default_brightness

        # Configuração de GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.OUT)

        # Inicializa o PWM para o LED
        self.pwm = GPIO.PWM(self.gpio_pin, 1000)  # 1 kHz PWM
        self.pwm.start(0)  # Começa com o LED apagado
        self.set_brightness(self.brightness)

    def set_brightness(self, brightness: int) -> None:
        """Define o brilho do LED.
        
        Args:
            brightness (int): O valor de brilho (0 a 100%).
        
        Returns:
            None
        """
        pwm_duty = (brightness / 100) * 100  # Duty cycle de 0% a 100%
        self.pwm.ChangeDutyCycle(pwm_duty)

    def turn_on(self) -> None:
        """Liga o LED com o brilho configurado.
        
        Args:
            None
        
        Returns:
            None
        """
        self.set_brightness(self.brightness)

    def turn_off(self) -> None:
        """Desliga o LED, colocando o brilho em 0%.
        
        Args:
            None
        
        Returns:
            None
        """
        self.set_brightness(0)

    def cleanup(self) -> None:
        """Desfaz todas as configurações do GPIO e encerra o uso do PWM.
        
        Args:
            None
        
        Returns:
            None
        """
        self.pwm.stop()
        GPIO.cleanup()


class RGBLED(LED):
    """Classe para controlar um LED RGB analógico com ajuste de brilho baseado em porcentagem.

    A classe permite controlar um LED RGB comum (anodo ou cátodo comum) e ajustar o brilho de cada cor utilizando um valor de brilho em porcentagem (0-100%).
    As configurações de GPIO e brilho são lidas dos arquivos de configuração 'pins.yaml' e 'conf.yaml'.

    Attributes:
        gpio_pins (Dict[str, int]): Dicionário com os pinos GPIO para as cores R, G e B.
        led_type (str): Tipo de LED ('common_anode' ou 'common_cathode').
    """

    def __init__(self, config_manager: ConfigManager):
        """Inicializa o controlador do LED RGB.

        Args:
            config_manager (ConfigManager): Instância do gerenciador de configurações para carregar as configurações do arquivo.
        
        Raises:
            ValueError: Se a GPIO não estiver disponível ou não puder ser corretamente inicializada.
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

        # Inicializa os LEDs baseados na classe LED
        self.red_led = LED(config_manager, self.red_pin, self.brightness)
        self.green_led = LED(config_manager, self.green_pin, self.brightness)
        self.blue_led = LED(config_manager, self.blue_pin, self.brightness)

        # Inicializa o estado do LED com base no tipo
        self.invert_logic = self.led_type == "common_anode"
        
        # Inicializa os LEDs desligados
        self.set_color(0, 0, 0)

    def _adjust_brightness(self, pwm_instance, brightness: int) -> None:
        """Ajusta o brilho de um LED individual usando PWM.

        Args:
            pwm_instance (PWM instance): A instância do PWM do pino do LED.
            brightness (int): O valor de brilho (0 a 100%).

        Returns:
            None
        """
        if self.invert_logic:
            brightness = 100 - brightness  # Inverte a lógica para anodo comum

        pwm_duty = (brightness / 100) * 100  # Duty cycle de 0% a 100%
        pwm_instance.set_brightness(brightness)

    def set_color(self, red_brightness: int, green_brightness: int, blue_brightness: int) -> None:
        """Define a cor do LED RGB com base no brilho configurado de cada cor.

        Args:
            red_brightness (int): Brilho do LED vermelho.
            green_brightness (int): Brilho do LED verde.
            blue_brightness (int): Brilho do LED azul.

        Returns:
            None
        """
        self._adjust_brightness(self.red_led, red_brightness)
        self._adjust_brightness(self.green_led, green_brightness)
        self._adjust_brightness(self.blue_led, blue_brightness)

    def turn_off(self) -> None:
        """Desliga completamente o LED RGB, colocando o brilho de todas as cores em 0%.

        Args:
            None

        Returns:
            None
        """
        self.set_color(0, 0, 0)


class IRLED(LED):
    """Classe para controlar um LED infravermelho analógico com ajuste de brilho baseado em porcentagem.
    
    A classe permite controlar um LED infravermelho comum e ajustar o brilho utilizando um valor de brilho em porcentagem (0-100%).
    As configurações de GPIO e brilho são lidas dos arquivos de configuração 'pins.yaml' e 'conf.yaml'.

    Attributes:
        gpio_pin (int): Pino GPIO para o LED infravermelho.
        brightness (int): Percentual de brilho do LED (0 a 100%).
    """
    
    def __init__(self, config_manager: ConfigManager):
        """Inicializa o controlador do LED infravermelho.
        
        Args:
            config_manager (ConfigManager): Instância do gerenciador de configurações para carregar as configurações do arquivo.
        
        Raises:
            ValueError: Se a GPIO não estiver disponível ou não puder ser corretamente inicializada.
        """
        # Carregar configurações de pino e brilho
        self.config_manager = config_manager
        self.gpio_pin = self.config_manager.get("pins").get("LED_IR", 18)  # Default: GPIO 18
        self.brightness = self.config_manager.get("conf").get("brightness", 50)  # Default: 50%

        # Inicializa o LED usando a classe base LED
        super().__init__(config_manager, self.gpio_pin, self.brightness)

    def set_brightness(self, brightness: int) -> None:
        """Define o brilho do LED infravermelho.

        Args:
            brightness (int): O valor de brilho (0 a 100%).

        Returns:
            None
        """
        super().set_brightness(brightness)

    def turn_on(self) -> None:
        """Liga o LED infravermelho com o brilho configurado.

        Args:
            None

        Returns:
            None
        """
        super().turn_on()

    def turn_off(self) -> None:
        """Desliga completamente o LED infravermelho, colocando o brilho em 0%.

        Args:
            None

        Returns:
            None
        """
        super().turn_off()
