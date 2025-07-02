#!/usr/bin/env python3
"""
Logging module for Bitbucket environment manager.

This module provides a custom Logger class that extends the standard logging.Logger
to provide colored console output and optional file logging capabilities.
"""

import datetime
import inspect
import logging
import os

import coloredlogs  # type: ignore


class Logger(logging.Logger):
    """Build Logger"""
    def __init__(
        self,
        enable_log_file: bool = False,
        log_level: str = 'INFO'
    ):
        super().__init__(os.path.basename(inspect.stack()[1].filename))
        self.log_name: str = os.path.basename(inspect.stack()[1].filename)
        self.log_level: str = log_level
        self.enable_log_file: bool = enable_log_file

    def __logging(self) -> logging.Logger:
        """Create and configure the logger instance."""
        datestamp = datetime.datetime.today().strftime("%m-%d-%Y")
        logger = logging.getLogger(self.log_name)
        logging.captureWarnings(True)
        coloredlogs.install(level=self.log_level)  # type: ignore
        if self.enable_log_file:
            formatter = logging.Formatter(
                fmt="[%(asctime)s] - [%(levelname)s] - [%(name)s.%(funcName)s:%(lineno)d] - [%(message)s]"
            )
            file_handler = logging.FileHandler(
                filename=f"{self.log_name}-{datestamp}.log",
                mode="a"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def create_logger(self) -> logging.Logger:
        """Create and return a configured logger instance."""
        return self.__logging()