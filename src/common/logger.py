import logging, os

def getmylogger(name) -> logging.Logger:
    if logging.getLogger(name).handlers:
        # Logger already configured, return existing logger
        return logging.getLogger(name)
    
    console_formatter = logging.Formatter('%(name)s: %(levelname)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger(name)

    logger.propagate = False
   
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    
    return logger

