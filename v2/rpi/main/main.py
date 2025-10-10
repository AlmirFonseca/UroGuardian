
# enter 'src' through sys.path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print(sys.path)

# import os
# print(os.environ["PATH"])

from src.controller import Controller

if __name__ == "__main__":
    controller = Controller()
    # controller.start()
    
    # Loop infinito para manter o programa rodando
    while True:
        pass