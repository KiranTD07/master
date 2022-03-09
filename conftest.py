import re
from datetime import datetime

from py.xml import html

import pytest

from Source.BaseClass.driver_factory import DriverFactory
from Utilities.report_utility import HTML_Report


@pytest.fixture(scope="session")
def get_driver(request, environment):
    df = DriverFactory(environment)

    session = request.node


def pytest_addoption(parser):
    parser.addoption("--platform", help="Operating System Type")
    parser.addoption("--environment", help="Application Environment")


@pytest.fixture(scope="session")
def environment(request):
    return request.config.getoption("--environment")


def pytest_cmdline_preparse(config, args):
    html_file = HTML_Report()
    args.extend(['--html', html_file, '--self-contained-html'])
    # args.extend(['--excelreport', xml_file])


def pytest_html_report_title(report):
    report.title = "Exotel API Automation Report"


def pytest_configure(config):
    config._metadata['Project Name'] = "API Automation Report"


@pytest.mark.optionalhook
def pytest_metadata(metadata):
    metadata.pop("JAVA_HOME", None)
    metadata.pop("Plugins", None)
    metadata.pop("Packages", None)
    metadata.pop("Python", None)
