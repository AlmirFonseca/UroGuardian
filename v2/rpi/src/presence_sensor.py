import asyncio
import threading
import time
from enum import Enum

from aio_ld2410 import LD2410, ReportBasicStatus

from src.logger import Logger
from src.config_manager import ConfigManager

class PresenceEvent(Enum):
    URINAL_IN_USE = 0
    NEARBY_DETECTED = 1
    NO_PRESENCE = 2

class PresenceSensor:
    """
    Integração com o sensor LD2410 para detecção de presença.
    Permite polling contínuo em thread, acionando callback por evento.
    """

    def __init__(self, config_manager: ConfigManager, logger: Logger):
        self.config = config_manager
        self.logger = logger
        self.device_path = self.config.get("conf").get("presence_sensor").get("ld2410_device_path", "/dev/ttyS0")
        self.near_threshold_cm = self.config.get("conf").get("presence_sensor").get("near_threshold_cm", 120)
        self.in_use_threshold_cm = self.config.get("conf").get("presence_sensor").get("in_use_threshold_cm", 60)
        self.polling = False
        self._thread = None

    async def get_event(self, timeout: float = 10.0) -> PresenceEvent:
        self.logger.println("Conectando ao PresenceSensor...", "INFO")
        try:
            async with LD2410(self.device_path) as device:
                self.logger.println("Lendo dados do PresenceSensor...", "INFO")
                report = await asyncio.wait_for(device.get_next_report(), timeout=timeout)
                self.logger.println(f"Dados lidos do PresenceSensor: {report.basic}", "INFO")
                event = self._interpret_report(report.basic)
                self.logger.println(f"Evento de presença: {event.name} | {report.basic}", "DEBUG")
                return event
        except Exception as e:
            self.logger.println(f"Erro na leitura do PresenceSensor: {e}", "ERROR")
            return PresenceEvent.NO_PRESENCE

    def _interpret_report(self, rep: ReportBasicStatus) -> PresenceEvent:
        distances = [x for x in [rep.static_distance, rep.moving_distance, rep.detection_distance] if x]
        if not distances:
            return PresenceEvent.NO_PRESENCE
        min_dist = min(distances)
        if min_dist <= self.in_use_threshold_cm:
            return PresenceEvent.URINAL_IN_USE
        elif min_dist <= self.near_threshold_cm:
            return PresenceEvent.NEARBY_DETECTED
        else:
            return PresenceEvent.NO_PRESENCE

    def start_polling(self, on_event_callback, interval=1.0):
        """
        Inicia thread de polling chamando o callback com PresenceEvent a cada leitura.
        """
        if self.polling:
            self.logger.println("PresenceSensor já em polling.", "WARNING")
            return
        self.polling = True
        self._thread = threading.Thread(target=self._poll_loop, args=(on_event_callback, interval), daemon=True)
        self._thread.start()
        self.logger.println("PresenceSensor polling iniciado.", "INFO")

    def stop_polling(self):
        self.polling = False
        # Só chama join se NÃO está na thread de polling
        if self._thread and self._thread.is_alive() and threading.current_thread() != self._thread:
            self._thread.join(timeout=2)
        self.logger.println("PresenceSensor polling parado.", "INFO")

    def _poll_loop(self, callback, interval):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            last_event = None
            while self.polling:
                try:
                    event = loop.run_until_complete(self.get_event(timeout=1.2))
                except Exception:
                    event = PresenceEvent.NO_PRESENCE
                # Apenas chama callback em troca de estado OU sempre (ajuste aqui)
                callback(event)
                time.sleep(interval)
        finally:
            loop.close()

# ------- Exemplo de uso --------
# Use start_polling(callback) para polling.

# EXEMPLO DE USO ----------------------------------
# if __name__ == "__main__":
#     import sys
#     sys.path.append("..")  # Garante import ao rodar como script

#     async def main():
#         cfg = ConfigManager("../config")
#         log = Logger()
#         pres = PresenceSensor(cfg, log)
#         print("--- Teste de Presença ---")
#         for i in range(5):
#             evt = await pres.get_event()
#             print(f"Leitura {i+1}: Evento = {evt.name} (valor={evt.value})")
#             time.sleep(2)

#     asyncio.run(main())
