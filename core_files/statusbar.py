'''
This module will be used for showing messages to the statusbar of the GUI, as
well as log
'''
import logging

global bar
LOG_FILE = "output.log"


# The StatusBar in QtApplication
def initBar(qtbar):
    global bar
    bar = qtbar


def show(msg):
    global bar
    bar.showMessage(msg)


def get_logger(name):
    logFormatter = logging.Formatter(
        "%(name)s (%(lineno)d): %(message)s")
    logger = logging.getLogger(name)

    # Write to file handler
    fileHandler = logging.FileHandler(LOG_FILE)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    # Write to console handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger

# def get_logger(name):
#     return logging.getLogger(name)
