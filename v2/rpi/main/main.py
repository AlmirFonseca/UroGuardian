
# enter 'src' through sys.path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print(sys.path)

import time
import threading

# import os
# print(os.environ["PATH"])

from src.controller import Controller

if __name__ == "__main__":
    controller = Controller()
    # controller.start()

    if controller.config.get("conf").get("app_web_interface").get("active", True):
        threading.Thread(target=controller.webpage.run, daemon=True).start()
        
    time.sleep(5)
    
    # Inicia o navegador luakit via cmd
    if controller.config.get("conf").get("app_web_interface").get("launch_browser_on_start", True):
        import subprocess
        web_config = controller.config.get("conf").get("app_web_interface")
        host = web_config.get("host", "localhost")
        port = web_config.get("port", 5000)
        main_page = web_config.get("main_page", "welcome")
        url = f"http://{host}:{port}/{main_page}"
        controller.logger.println(f"Lançando navegador no URL: {url}", "INFO")
        try:
            subprocess.Popen(["luakit", url])
        except Exception as e:
            controller.logger.println(f"Erro ao lançar o navegador: {e}", "ERROR")
        
    # Loop infinito para manter o programa rodando
    while True:
        pass