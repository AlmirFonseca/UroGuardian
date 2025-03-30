import os
import yaml
from typing import Dict, Any

class ConfigManager:
    """Classe para gerenciar arquivos de configuração YAML.

    Esta classe carrega arquivos de configuração YAML de um diretório especificado e armazena seus 
    conteúdos em dicionários.
    Permite acessar configurações por nome e recarregar dinamicamente as configurações.

    Attributes:
        config_dir (str): Caminho do diretório onde os arquivos YAML estão armazenados.
        configs (Dict[str, Any]): Dicionário contendo as configurações carregadas, indexadas pelo 
        nome do arquivo.
    """

    def __init__(self, config_dir: str = "../config") -> None:
        """Inicializa o gerenciador de configuração.

        Args:
            config_dir (str, optional): Diretório contendo os arquivos YAML. O padrão é "config".

        Raises:
            FileNotFoundError: Se o diretório especificado não existir.
        """
        self.config_dir = config_dir
        self.configs: Dict[str, Any] = {}
        self.load_configs()
        
    def load_configs(self) -> None:
        """Carrega todos os arquivos YAML do diretório de configuração.

        Raises:
            FileNotFoundError: Se o diretório especificado não existir.
        """
        if not os.path.exists(self.config_dir):
            raise FileNotFoundError(f"Diretório '{self.config_dir}' não encontrado.")

        for file_name in os.listdir(self.config_dir):
            if file_name.endswith(".yaml") or file_name.endswith(".yml"):
                config_name = os.path.splitext(file_name)[0]
                file_path = os.path.join(self.config_dir, file_name)
                with open(file_path, "r") as file:
                    self.configs[config_name] = yaml.safe_load(file)

    def get(self, config_name: str) -> Dict[str, Any]:
        """Retorna o conteúdo do arquivo de configuração especificado.

        Args:
            config_name (str): Nome do arquivo de configuração (sem extensão).

        Returns:
            Dict[str, Any]: Dicionário com o conteúdo do arquivo YAML.

        Raises:
            KeyError: Se a configuração especificada não for encontrada.
        """
        config = self.configs.get(config_name)
        if config is None:
            raise KeyError(f"Configuração '{config_name}' não encontrada.")
        return config

    def reload(self) -> None:
        """Recarrega todas as configurações do diretório.

        Raises:
            FileNotFoundError: Se o diretório especificado não existir ao recarregar.
        """
        self.configs.clear()
        self.load_configs()
