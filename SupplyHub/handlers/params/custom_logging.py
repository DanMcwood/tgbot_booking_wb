import logging
import colorlog

# Создаем новый уровень логирования INFO_SCHEDULED
INFO_SCHEDULED = 25
logging.addLevelName(INFO_SCHEDULED, "INFO_SCHEDULED")

INFO_BOOKING = 26
logging.addLevelName(INFO_BOOKING, "INFO_BOOKING")

# В custom_logging.py
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Устанавливаем минимальный уровень логирования на INFO

formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s',
    log_colors={
        'DEBUG': 'white',
        'INFO': 'cyan',
        'INFO_SCHEDULED': 'green',
        'INFO_BOOKING': 'yellow',
        'WARNING': 'red',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Функция для использования нового уровня
def info_scheduled(msg, *args, **kwargs):
    if logger.isEnabledFor(INFO_SCHEDULED):
        logger._log(INFO_SCHEDULED, msg, args, **kwargs)

def info_booking(msg, *args, **kwargs):
    if logger.isEnabledFor(INFO_BOOKING):
        logger._log(INFO_BOOKING, msg, args, **kwargs)
