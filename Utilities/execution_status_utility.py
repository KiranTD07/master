""" This module contains the methods to conclude the execution status. """

import logging

import allure
import pytest

import Utilities.logger_utility as log_utils


class ExecutionStatus:

    log = log_utils.custom_logger(logging.INFO)

    def __init__(self,driver =None ):
        super().__init__(driver)
        self.result_list = []

    def set_result(self, result, test_name):



        try:
            if result is not None:

                if result:
                    self.result_list.append("PASS")
                    self.log.info("### STEP SUCCESSFUL :: " + test_name)
                else:
                    image = self.take_screenshots(test_name)
                    error = "### STEP FAILED :: " + test_name
                    self.result_list.append("FAIL")
                    self.log.error(error)
                    allure.attach.file(image, attachment_type=allure.attachment_type.PNG)

            else:
                error = "### STEP FAILED :: " + test_name
                self.result_list.append("FAIL")
                self.log.error(error)

        except Exception as ex:
            self.result_list.append("FAIL")
            self.log.error("### EXCEPTION OCCURRED :: {}".format(ex))

    def mark(self, test_step, result):



        self.set_result(result=result, test_name=test_step)

    def mark_final(self, result, test_step):


        self.set_result(result, test_step)


        try:
            if "FAIL" in self.result_list:
                self.result_list.clear()
                assert True is False

            else:
                self.result_list.clear()
                assert True is True, "### TEST SUCCESSFUL :: " + test_step

        except Exception:
            pytest.fail("### TEST FAILED :: " + test_step, pytrace=False)
