import logging

def getmylogger(name) -> logging.Logger:
    if logging.getLogger(name).handlers:
        # Logger already configured, return existing logger
        return logging.getLogger(name)
    file_formatter = logging.Formatter('%(asctime)s~%(levelname)s~%(message)s~module:%(module)s~function:%(module)s')
    console_formatter = logging.Formatter('%(levelname)s -- %(message)s')
    
    file_handler = logging.FileHandler("logfile.log", mode='w')
    file_handler.setLevel(logging.WARN)
    file_handler.setFormatter(file_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    
    return logger

