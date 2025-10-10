from datetime import datetime
from typing import Dict, Any

from src.config_manager import ConfigManager
from src.database import Database
from src.logger import Logger

class SampleHandler:
    """Gerencia o ciclo de uma amostra ("sample") durante o recebimento de pontos de dados espectrais.

    Mantém o estado da amostra em andamento para um determinado dispositivo, facilitando a criação,
    atualização e finalização automática da amostra conforme as flags dos datapoints recebidos.

    Attributes:
        db (Database): Instância da camada de acesso ao banco de dados.
        logger (Logger): Logger do sistema para depuração e registro.
        current_sample_id (Optional[int]): ID da amostra atualmente em execução (ciclo aberto).
    """

    def __init__(self, database: Database):
        """Inicializa o SampleHandler com o banco de dados alvo.

        Args:
            database (Database): Instância do gerenciador de banco de dados.

        Returns:
            None
        """
        self.db = database
        self.logger = Logger()
        # Mantém em memória a sample em andamento (por device, se quiser expandir, use dict)
        self.current_sample_id = None

    def handle_datapoint(self, payload: Dict[str, Any]) -> None:
        """Recebe um novo datapoint de espectro e gerencia seu ciclo de sample com base na flag.

        - Se flag = 1, inicia nova amostra.
        - Se flag = -1, encerra amostra, processa e limpa estado.
        - Em qualquer caso, armazena o datapoint associado ao sample_id atual.

        Args:
            payload (Dict[str, Any]): Dicionário contendo os dados da leitura, incluindo flag, device_id e timestamp.

        Returns:
            None

        Raises:
            KeyError: Se payload não contiver "flag" ou "device_id".
            Exception: Se ocorrer erro no acesso ao banco ao criar/fechar sample.
        """
        flag = int(payload["flag"])
        device_id = int(payload["device_id"])
        timestamp = payload.get("timestamp", datetime.now().isoformat())

        if flag == 1:
            # Início de nova sample: cria nova entrada em "samples"/"urine_samples"
            # e armazena o ID corrente para os próximos datapoints dessa amostra
            self.current_sample_id = self.db.create_sample(device_id, start_timestamp=timestamp)
            self.logger.println(f"Iniciando nova sample para device {device_id}: {self.current_sample_id}", "DEBUG")

        # Insere o datapoint no banco, associando ao sample_id corrente
        payload["sample_id"] = self.current_sample_id
        self.db.insert_dict_into_table("spectrum_datapoints", payload, query_key="insert_spectrum_datapoint")
        self.logger.println(f"Datapoint armazenado (sample {self.current_sample_id}): {payload}", "DEBUG")

        if flag == -1:
            # Fim da sample: marca encerramento e dispara etapa de pós-processamento
            self.db.close_sample(self.current_sample_id, end_timestamp=timestamp)
            self.logger.println(f"Finalizando sample {self.current_sample_id} em {timestamp}", "INFO")
            self.mock_post_process(self.current_sample_id)
            self.current_sample_id = None

    def mock_post_process(self, sample_id: int) -> None:
        """Mock de callback chamado no final do ciclo da amostra, para processamento extra.

        Args:
            sample_id (int): ID da amostra recém-finalizada.

        Returns:
            None
        """
        print(f"[MOCK] Processamento extra da amostra finalizada: {sample_id}")
