import logging
from logging.handlers import RotatingFileHandler

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler with rotation
file_handler = RotatingFileHandler("app.log", maxBytes=5 * 1024 * 1024, backupCount=2)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Stream handler for console output
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
