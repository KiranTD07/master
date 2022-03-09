import os
import pytest
from datetime import datetime
from Source.BaseClass import constants


class ReportPlugin:

    def pytest_sessionfinish(self):
        allure_report_folder = constants.ALLURE_REPORT + datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        command = "allure generate " + constants.ALLURE_RESULTS + " -o " + allure_report_folder
        os.popen(command)

arguments = ["-q","--alluredir", constants.ALLURE_RESULTS]

pytest.main(arguments, plugins=[ReportPlugin()])