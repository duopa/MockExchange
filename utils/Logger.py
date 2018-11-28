# -*- encoding: UTF-8 -*-
import logging
import os

from Interface import ROOT_PATH
from utils import load_yaml

LOG_FORMATTER = logging.Formatter(
    '%(asctime)s %(filename)s %(lineno)d :  %(levelname)s, %(message)s'
)
LOG_LEVEL_CHOICE = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

log_config = load_yaml(os.path.join(ROOT_PATH, 'Config.yaml')).get('Log', dict())
DEFAULT_LOG_DIR = log_config.get('path', 'log')
DEFAULT_LOG_CONSOLE_ENABLED = log_config.get('console_print', False)
DEFAULT_LOG_LEVEL = LOG_LEVEL_CHOICE.get(log_config.get('level', 'info'), logging.INFO)
if os.path.exists(DEFAULT_LOG_DIR) is False:
    os.makedirs(DEFAULT_LOG_DIR)
if log_config.get('keep_history', False) is False:
    os.removedirs(DEFAULT_LOG_DIR)
    os.makedirs(DEFAULT_LOG_DIR)


class LogWrapper(logging.Logger):

    def __init__(self, name: str, level=logging.NOTSET):
        super(LogWrapper, self).__init__(name, level)

    def debug_if(self, check: bool, msg: str, *args, **kwargs):
        if check is True and self.isEnabledFor(logging.DEBUG):
            self._log(logging.DEBUG, msg, args, **kwargs)

    # def debug_running(self, running: str, stage: str, *args, **kwargs):
    #     self._log(logging.DEBUG, '[running] {} at stage {}.'.format(running, stage), args, **kwargs)

    def info_if(self, check: bool, msg: str, *args, **kwargs):
        if check is True and self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, msg, args, **kwargs)

    def warning_if(self, check: bool, msg: str, *args, **kwargs):
        if check is True and self.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, msg, args, **kwargs)


def get_logger(module_name, file_name: str, console_print=DEFAULT_LOG_CONSOLE_ENABLED):
    """

    :param module_name: str / object(instance of a class)
    :param file_name: the name of log filename
    :param console_print: whether show logging info in console
    :return: :class:`~logging.Logger`
    """
    import time

    log_path = os.path.join(ROOT_PATH, DEFAULT_LOG_DIR)

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    if isinstance(module_name, str):
        log_name = module_name
    elif isinstance(module_name, object):
        log_name = module_name.__class__.__name__
    else:
        from utils.Exceptions import ParamTypeError
        raise ParamTypeError('module_name', 'str/object', module_name)

    # logger = logging.getLogger(log_name)
    logger = LogWrapper(log_name)
    logger.setLevel(DEFAULT_LOG_LEVEL)

    log_file_name = file_name + time.strftime("%Y%m%d") + ".log"
    file_handler = logging.FileHandler(os.path.join(log_path, log_file_name))  # 本地测试
    file_handler.setFormatter(LOG_FORMATTER)
    # logger.addHandler(file_handler)

    if console_print is True:
        screen_handler = logging.StreamHandler()
        screen_handler.setFormatter(LOG_FORMATTER)
        logger.addHandler(screen_handler)

    # return LogWrapper(logger)
    return logger
