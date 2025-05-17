#!/usr/bin/env python3
import coloredlogs
import logging
import sys
import os
import inspect
import datetime

class Logger:
    def __init__(self, enable_log_file=False, log_level='INFO'):
        self.log_name = os.path.basename(inspect.stack()[1].filename)
        self.log_level = log_level
        self.enable_log_file = enable_log_file

    def __logging(self):
        datestamp = datetime.datetime.today().strftime("%m-%d-%Y")
        logger = logging.getLogger(self.log_name)
        logging.captureWarnings(True)
        coloredlogs.install(level=self.log_level)
        if self.enable_log_file:
            formatter = logging.Formatter(fmt="[%(asctime)s] - [%(levelname)s] - [%(name)s.%(funcName)s:%(lineno)d] - [%(message)s]")
            file_handler = logging.FileHandler(
                filename=f"{self.log_name}-{datestamp}.log",
                mode="a")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def create_logger(self):
        return self.__logging()