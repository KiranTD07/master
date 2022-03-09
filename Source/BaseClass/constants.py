import os
from datetime import datetime

cur_path = os.path.abspath(os.path.dirname(__file__))
digit_path = os.getcwd() + '/TestData/Digit.txt'
call_path = os.getcwd() + '/TestData/CallStatus.txt'
current_time = datetime.strftime(datetime.now(), '%d%m%Y-%H%M%S')
xls_file = "RAFT_" + current_time + "_Automation_Test_Report.xlsx"

