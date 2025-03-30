from typing import Optional
from src.config_manager import ConfigManager


class Logger:
    """Classe para registro de mensagens com controle de níveis de debug.

    Permite segmentação em níveis (DEBUG, INFO, WARNING, ERROR, FATAL, LOG, EXCEPTION, VERBOSE) e a 
    utilização de tags de três letras.
    O nível de debug inicial é obtido a partir do arquivo de configuração YAML.

    Attributes:
        level (int): Nível atual de debug.
        show_tag (bool): Define se as tags serão exibidas nas mensagens.
    """

    LEVELS = {
        "VERBOSE": 0,
        "DEBUG": 1,
        "INFO": 2,
        "LOG": 3,
        "WARNING": 4,
        "ERROR": 5,
        "EXCEPTION": 6,
        "FATAL": 7,
        "OFF": 8
    }

    TAGS = {
        0: "VRB",
        1: "DBG",
        2: "INF",
        3: "LOG",
        4: "WRN",
        5: "ERR",
        6: "EXC",
        7: "FTL",
        8: "OFF"
    }

    def __init__(self, config_path: str = "config/logging.yaml") -> None:
        """Inicializa o Logger com base nas configurações carregadas.

        Args:
            config_path (str): Caminho para o arquivo YAML com as configurações de logging.
        """
        config_manager = ConfigManager()
        logging_config = config_manager.get("logging")
        level_str = logging_config.get("level", "INFO")
        self.level = self.LEVELS.get(level_str.upper(), 2)
        self.show_tag = True

    def set_level(self, level: str) -> None:
        """Define o nível de debug manualmente.

        Args:
            level (str): Novo nível de debug ("VERBOSE", "DEBUG", "INFO", "LOG", "WARNING", "ERROR",
            "EXCEPTION", "FATAL").
        """
        self.level = self.LEVELS.get(level.upper(), self.level)

    def enable_tags(self) -> None:
        """Habilita a exibição das tags nas mensagens."""
        self.show_tag = True

    def disable_tags(self) -> None:
        """Desabilita a exibição das tags nas mensagens."""
        self.show_tag = False

    def print(self, message: str, level: str = "INFO", show_tag: Optional[bool] = None) -> None:
        """Exibe uma mensagem de acordo com o nível especificado.

        Args:
            message (str): Mensagem a ser exibida.
            level (str): Nível de debug da mensagem.
            show_tag (Optional[bool]): Força a exibição ou ocultação da tag apenas para esta 
            mensagem.
        """
        msg_level = self.LEVELS.get(level.upper(), 2)
        if msg_level >= self.level:
            tag = self.TAGS[msg_level] if (self.show_tag if show_tag is None else show_tag) else ""
            formatted_message = f"[{tag}] {message}" if tag else message
            print(formatted_message, end="")

    def println(self, message: str, level: str = "INFO", show_tag: Optional[bool] = None) -> None:
        """Exibe uma mensagem seguida de nova linha.

        Args:
            message (str): Mensagem a ser exibida.
            level (str): Nível de debug da mensagem.
            show_tag (Optional[bool]): Força a exibição ou ocultação da tag apenas para esta mensagem.
        """
        self.print(message + "\n", level, show_tag)
        
    def print_separator(self, level: str = "INFO", show_tag: Optional[bool] = None, sep_type: str = "-=", size: int = 40) -> None:
        """Exibe uma linha separadora.

        Args:
            level (str): Nível de debug da mensagem.
            show_tag (Optional[bool]): Força a exibição ou ocultação da tag apenas para esta mensagem.
            sep_type (str): Tipo de separador ("-=", "=", "-", " ", ".").
            size (int): Tamanho do separador.
        """
        separator = sep_type * size
        self.println(separator, level, show_tag)
