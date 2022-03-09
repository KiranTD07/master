import os
import logging
from Utilities.config_utility import ConfigUtility
from Utilities.logger_utility import custom_logger


class DriverFactory:

    log = custom_logger(logging.INFO)
    config = ConfigUtility()

    def  __init__(self, environment):
        self.environment = environment
        self.cur_path = os.path.abspath(os.path.dirname(__file__))
        self.prop = self.config.load_properties_file()

    def get_driver_instance(self):

        if self.environment == "staging":
            execution_data = self.prop.get('RAFT', 'staging_test_data')
            self.config.change_properties_file('RAFT', 'base_test_data', execution_data)

            test_data = self.prop.get('RAFT', 'staging_execution_data')
            self.config.change_properties_file('RAFT', 'base_execution_data', test_data)

        elif self.environment == "prod":
            execution_data = self.prop.get('RAFT', 'prod_test_data')
            self.config.change_properties_file('RAFT', 'prod_execution_data', execution_data)

            test_data = self.prop.get('RAFT', 'base_execution_data')
            self.config.change_properties_file('RAFT', 'base_test_data', test_data)
        else:
            execution_data = self.prop.get('RAFT', 'staging_test_data')
            self.config.change_properties_file('RAFT', 'base_test_data', execution_data)

            test_data = self.prop.get('RAFT', 'staging_execution_data')
            self.config.change_properties_file('RAFT', 'base_execution_data', test_data)
