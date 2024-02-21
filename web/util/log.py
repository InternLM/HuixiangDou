import logging


def log(name):
    """
    @param name: python file name
    @return: Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(levelname)s:     %(asctime)s - %(module)s-%(funcName)s-line:%(lineno)d - %(message)s"
    )
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def clear_other_log():
    for name, item in logging.Logger.manager.loggerDict.items():
        if not isinstance(item, logging.Logger):
            continue
        if "aoe" not in name:
            item.setLevel(logging.CRITICAL)


clear_other_log()
logger = log("util")
