
# enter 'src' through sys.path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print(sys.path)

import threading

# import os
# print(os.environ["PATH"])

from src.controller import Controller

if __name__ == "__main__":
    controller = Controller()
    # controller.start()
    
    if controller.config.get("conf").get("app_web_interface"):
        threading.Thread(target=controller.webpage.run, daemon=True).start()
    
    # Loop infinito para manter o programa rodando
    while True:
        pass