# logger.py
import logging
import os

LOG_FILE = "logs/firmware_patch.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger = logging.getLogger("firmware_logger")
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# Add handler if not already added
if not logger.hasHandlers():
    logger.addHandler(fh)