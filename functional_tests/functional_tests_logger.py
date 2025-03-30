from src.logger import Logger

logger = Logger()
logger.set_log_level("DEBUG")

# Log different levels
logger.log("INFO", "This is an info log.")
logger.log("ERROR", "This is an error log.")
logger.log("DEBUG", "This is a debug log.")
