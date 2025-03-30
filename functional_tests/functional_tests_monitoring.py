import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from src.monitoring import SystemMonitoring
from src.database import Database
from src.config_manager import ConfigManager
import time

def monitoring_demo():
    config_manager = ConfigManager()
    db = Database(config_manager)

    # Inicializa o monitoramento com intervalo de 60 segundos
    monitoring = SystemMonitoring(db, time_interval=60)

    # Demonstração de coleta e armazenamento de dados
    monitoring.collect_and_store_data()

    # Obtém o uso atual de CPU
    cpu_usage = monitoring.get_cpu_usage()
    print(f"CPU Usage: {cpu_usage}%")

    # Obtém o uso atual de RAM
    ram_usage = monitoring.get_ram_usage()
    print(f"RAM Usage: {ram_usage}%")

    # Obtém o uso atual do disco
    disk_usage = monitoring.get_disk_usage()
    print(f"Disk Usage: {disk_usage}%")

    # Obtém o uso atual da rede
    network_usage = monitoring.get_network_usage()
    print(f"Network Usage: {network_usage} MB/s")

    # Obtém SSID e sinal de Wi-Fi
    wifi_info = monitoring.get_wifi_ssid_and_db()
    print(f"Wi-Fi SSID: {wifi_info[0] if wifi_info else 'N/A'}")
    print(f"Wi-Fi Signal Strength: {wifi_info[1] if wifi_info else 'N/A'} dB")

    # Inicia o monitoramento contínuo
    print("Starting continuous monitoring...")
    monitoring.start_monitoring()

if __name__ == "__main__":
    monitoring_demo()
