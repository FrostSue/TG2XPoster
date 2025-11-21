import logging
import sys
import os
from colorlog import ColoredFormatter

def setup_logger(name="TgToTw"):
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger

    console_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - [%(levelname)s] - %(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red,bg_white'}
    )

    file_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger