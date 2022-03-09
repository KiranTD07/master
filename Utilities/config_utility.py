"""
This module contains config utility functions.
"""

import os
import time
import logging
from traceback import print_stack
from configparser import ConfigParser
import Utilities.logger_utility as log_utils


class ConfigUtility:

    log = log_utils.custom_logger(logging.INFO)

    def __init__(self):
        self.cur_path = os.path.abspath(os.path.dirname(__file__))
        self.config_path = os.path.join(self.cur_path, r"../Config/config.ini")

    def load_properties_file(self):

        config = None
        try:

            config = ConfigParser()
            config.read(self.config_path)

        except Exception as ex:
            self.log.error("Failed to load ini/properties file.", ex)
            raise Exception ("Failed to load ini/properties file")

        return config

    def change_properties_file(self, section, property_name, property_value):

        flag = False
        try:
            config = self.load_properties_file()
            config[section][property_name] = property_value

            with open(self.config_path, 'w') as configfile:
                config.write(configfile)

            time.sleep(1)
            flag = True

        except Exception as ex:
            raise Exception ("Failed to change ini/properties file.", ex)

        return flag
