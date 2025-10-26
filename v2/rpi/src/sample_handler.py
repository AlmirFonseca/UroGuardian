from datetime import datetime
import random
from typing import Dict, Any
import time

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

    def __init__(self, database: Database, controller: "Controller"):
        """Inicializa o SampleHandler com o banco de dados alvo.

        Args:
            database (Database): Instância do gerenciador de banco de dados.

        Returns:
            None
        """
        self.db = database
        self.logger = Logger()
        self.controller = controller
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
            
            # Altera o estado global para "collecting"
            self.controller.set_stage({"stage": "collecting"})

        # Insere o datapoint no banco, associando ao sample_id corrente
        payload["sample_id"] = self.current_sample_id
        
        # print("TOPIC:", "handle_datapoint")
        # print("DATA:", payload)
        # print("DATA TYPE:", type(payload))
        # for d in payload:
        #     print(" -", d, ":", payload[d], "(", type(payload[d]), ")")
            
        # # force timestamp to be and str
        # payload["timestamp"] = str(payload["timestamp"])
        
        # # if sample_id is None, set to -1
        # if payload["sample_id"] is None:
        #     payload["sample_id"] = -1
        
        self.db.insert_dict_into_table("spectrum_datapoints", payload, query_key="insert_spectrum_datapoint")
        self.logger.println(f"Datapoint armazenado (sample {self.current_sample_id}): {payload}", "DEBUG")

        if flag == -1:
            # Fim da sample: marca encerramento e dispara etapa de pós-processamento
            self.db.close_sample(self.current_sample_id, end_timestamp=timestamp)
            self.logger.println(f"Finalizando sample {self.current_sample_id} em {timestamp}", "INFO")
            
            # Altera o estado global para "processing"
            self.controller.set_stage({"stage": "processing"})
            
            self.process_sample(self.current_sample_id)
            self.current_sample_id = None

    def process_sample(self, sample_id: int) -> None:
        """Mock de callback chamado no final do ciclo da amostra, para processamento extra.

        Args:
            sample_id (int): ID da amostra recém-finalizada.

        Returns:
            None
        """
        
        hydration_result = random.choice(["Hidratado", "OK", "Desidratado", "Muito desidratado", "Severamente desidratado"])  # MOCK result
        print(f"[MOCK] Processamento extra da amostra finalizada: {sample_id} (hidratação: {hydration_result})")
        
        # Update sample with hydration result
        self.db.update_data(
            table="urine_samples",
            data={"hydration_level": hydration_result},
            condition=f"sample_id = {sample_id}"
        )

        # Simula tempo de processamento
        time.sleep(2)
        
        # Altera o estado global para 'results'
        self.controller.set_stage({"stage": "results"})

    def associate_sample_to_user(self, user_id: int, sample_id: int = None) -> None:
        """Associa um usuário a uma amostra específica no banco de dados.

        Args:
            user_id (int): ID do usuário a ser associado.
            sample_id (int): ID da amostra a ser associada.

        Returns:
            None
        """
        self.db.update_data(
            table="urine_samples",
            data={"user_id": user_id},
            condition=f"sample_id = {sample_id if sample_id is not None else self.current_sample_id}"
        )