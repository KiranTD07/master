"""
This module contains common reusable functions.
"""

from traceback import print_stack
from configparser import ConfigParser
#from Source.BaseClass.ui_helpers import UIHelpers


class BaseHelpers():


    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver

    def load_properties_file(self):


        config = None
        try:

            config = ConfigParser()
            config.read('pytest.ini')

        except Exception as ex:
            raise Exception("Failed to load ini/properties file.", ex)

        return config
