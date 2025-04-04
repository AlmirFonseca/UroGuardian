import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.controller import Controller

def main():
    controller = Controller()
    controller.start()

if __name__ == "__main__":
    main()
