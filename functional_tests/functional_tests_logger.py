import sys
import os

# Adiciona a pasta pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.logger import Logger

def logger_demo():
    logger = Logger()

    # Exibindo o nível inicial configurado via YAML
    logger.print_separator(sep_type="=")
    logger.println("Logger Functional Test Started!", "INFO")
    logger.print_separator(sep_type="=")

    # Demonstrando cada nível de debug
    levels = ["VERBOSE", "DEBUG", "INFO", "LOG", "WARNING", "ERROR", "EXCEPTION", "FATAL"]
    for level in levels:
        logger.set_level(level)
        logger.println(f"--- Current level set to {level} ---", "LOG")
        for test_level in levels:
            logger.println(f"Testing message at {test_level} level.", test_level)

    # Resetando para nível INFO
    logger.set_level("INFO")
    logger.print_separator(sep_type="-=")

    # Testando exibição e ocultação das tags
    logger.println("Tags are enabled (default).", "INFO")
    logger.disable_tags()
    logger.println("Tags have been disabled.", "INFO")
    logger.enable_tags()
    logger.println("Tags re-enabled.", "INFO")

    # Testando método print (sem nova linha)
    logger.print("This is a partial message...", "INFO")
    logger.println(" Completed!", "INFO")

    # Testando separadores personalizados
    logger.print_separator(sep_type="-", size=30)
    logger.print_separator(level="DEBUG", sep_type=".", size=20)
    logger.print_separator(level="WARNING", sep_type="=-", size=15)

    logger.println("Logger Functional Test Completed!", "INFO")
    logger.print_separator(sep_type="=")

if __name__ == "__main__":
    logger_demo()

