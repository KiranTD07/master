import os
import logging
import inspect
from datetime import datetime

from Source.BaseClass.constants import current_time, xls_file


def HTML_Report():
    report_filename = None

    cur_path = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.join(cur_path, r"../Reports/")
    if not os.path.exists(report_dir):
        os.mkdir(report_dir)
    date_dir = os.path.join(report_dir, str(datetime.strftime(datetime.now(), '%d%m%Y')))
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    if report_filename is None:
        temp_file = "RAFT_" + current_time + "_Automation_Test_Report.html"
        report_filename = os.path.join(date_dir, temp_file)

    return report_filename


def xls_Report():
    report_filename = None

    cur_path = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.join(cur_path, r"../Reports/")
    if not os.path.exists(report_dir):
        os.mkdir(report_dir)
    date_dir = os.path.join(report_dir, str(datetime.strftime(datetime.now(), '%d%m%Y')))
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    if report_filename is None:
        temp_file = xls_file
        report_filename = os.path.join(date_dir, temp_file)

    return report_filename

