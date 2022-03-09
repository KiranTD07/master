import json
import logging
import os
import time
import pjsua
import Utilities.logger_utility as log_utils
from Source.BaseClass.API_Request import APIRequest
from Source.BaseClass.constants import digit_path, call_path
from Source.Pages.reusable_methods import reusable_methods
from Utilities.config_utility import ConfigUtility
from Utilities.data_reader_utility import DataReader

data_reader = DataReader()
cur_path = os.path.abspath(os.path.dirname(__file__))
path = '/home/rbt/API_automation/Exotel_master/TestData/CallStatus.txt'


class Connect_Applet(reusable_methods):
    config = ConfigUtility()
    log = log_utils.custom_logger(logging.INFO)
    call = None

    def __init__(self):
        prop = self.config.load_properties_file()
        base_test_data = prop.get('RAFT', 'base_test_data')
        self.ui_file_path = os.path.join(cur_path, r"../TestData/{}.csv".format(base_test_data))
        self.request = APIRequest()
        self.api_key = prop.get('API_credentials', 'api_key')
        self.api_token = prop.get('API_credentials', 'api_token')
        self.subdomain = prop.get('Domain', 'Subdomain')
        self.callerId = prop.get('Domain', 'CallerId')
        self.account_sid = prop.get('Domain', 'Account_sid')
        self.aws_url = prop.get('Domain', 'AWS_Link')

    def connectApplet_01(self):
        try:
            method = data_reader.get_cell_data("EXTC_CON_001", "Method")
            From = data_reader.get_cell_data("EXTC_CON_001", "From")
            apiName = data_reader.get_cell_data("EXTC_CON_001", "ApiName")
            app_id = data_reader.get_cell_data("EXTC_CON_001", "app_id")
            DialWhomNumber = data_reader.get_cell_data("EXTC_CON_001", "DialWhomNumber")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, app_id)
            self.log.info(Url)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "answer")
            time.sleep(2)

            status_Call_back = self.aws_url + "/status_callback"

            # URL creation
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"

            self.log.info(API_URL)
            # Truncate the previous data from the#

            truncate_URL1 = self.aws_url + "/truncate_response_data?filename=Tc_connect01"

            self.log.info(truncate_URL1)

            self.request.post(truncate_URL1)

            truncate_URL2 = self.aws_url + "/truncate_response_data?filename=passthru_applet"

            self.log.info(truncate_URL2)

            self.request.post(truncate_URL2)

            self.log.info("truncated data_URL1")

            # Post response outbound call
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)

            # Extracting the Response and validating
            self.log.info(response)
            self.log.info("immediate response")
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            # from_json = call["From"]
            # caller_json = call["PhoneNumberSid"]
            # sid = '0ac43c72f8230d1ca68371c58a86162f'
            self.log.info(sid)
            for i in range(4):
                call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                    sid)
                self.log.info(call_details)
                res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                            api_token=self.api_token).text
                cd_response = json.loads(res3)["Call"]
                self.log.info(cd_response)
                self.verify_text_match(cd_response["Sid"], sid, "CallSid")
                self.log.info(cd_response["Status"])
                if cd_response["Status"] != 'in-progress':
                    break
                else:
                    time.sleep(100)

            else:
                raise Exception
            # URL creation using sid value
            URL1 = self.aws_url + "/" + sid + ".json"

            self.log.info(URL1)
            self.log.info("Status call back get request...")

            # GET using to get the Call completed details
            res1 = self.request.get(URL1)
            self.log.info(res1)

            status_Call_back_res = json.loads(res1.text)

            self.log.info(status_Call_back_res)

            sid = status_Call_back_res["CallSid"]
            self.verify_text_match(sid, sid, "sid")

            Status = status_Call_back_res["Status"]
            self.verify_text_match("completed", Status, "Status")

            self.log.info("Connect applet call details response validation in progress")

            connect_res = self.aws_url + '/Tc_connect01.json'

            res2 = self.request.get(connect_res).text
            self.log.info(connect_res)

            c_response = res2.split("\n")[0]
            connect_response = json.loads(c_response)

            self.log.info(connect_response)
            self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Dial')

            con_response1 = res2.split("\n")[1]
            connect_response1 = json.loads(con_response1)

            self.log.info(connect_response1)
            self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              "busy", "Answered")

            con_response1 = res2.split("\n")[2]
            connect_response1 = json.loads(con_response1)

            self.log.info(connect_response1)
            self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'free', 'Terminal')
            self.log.info("Connect applet call details response validation in progress")

            ###########  passthru applet #################

            self.log.info("passthru_applet response validation in progress")

            passthru_res = self.aws_url + '/passthru_applet.json'

            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)

            pa_response = json.loads(res2)
            self.log.info(pa_response)

            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')

            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')

            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, self.callerId, 'CallTo')

            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')

            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "incomplete", 'CallType')

            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(app_id), 'flow_id')

            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')

            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            DialWhomNumber_actual = pa_response["DialWhomNumber"]
            self.verify_text_match(DialWhomNumber_actual, DialWhomNumber, 'DialWhomNumber')

            OutgoingPhoneNumber = pa_response["OutgoingPhoneNumber"]
            self.verify_text_match(OutgoingPhoneNumber, self.callerId, 'OutgoingPhoneNumber')

            pa_response_details = pa_response["Legs"]
            self.log.info(pa_response_details["0"])

            pa_response_leg_details = pa_response_details["0"]
            self.log.info(pa_response_leg_details)

            self.log.info(pa_response_leg_details["Number"])
            Number_actual = pa_response_leg_details["Number"]
            self.verify_text_match(Number_actual, DialWhomNumber, 'DialWhomNumber')

            Type_actual = pa_response_leg_details["Type"]
            self.verify_text_match(Type_actual, 'single', 'Type')

            CallerId_actual = pa_response_leg_details["CallerId"]
            self.verify_text_match(CallerId_actual, self.callerId, 'CallerId')

            CauseCode_actual = pa_response_leg_details["CauseCode"]
            self.verify_text_match(CauseCode_actual, 'NORMAL_CLEARING', 'CauseCode')

            Cause_actual = pa_response_leg_details["Cause"]
            self.verify_text_match(Cause_actual, '16', 'Cause')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            cd_response1 = json.loads(res3)["Call"]
            self.log.info(cd_response1)

            sid_1 = cd_response1["Sid"]
            self.verify_text_match(sid_1, sid, "CallSid")

            accountSid_1 = cd_response1["AccountSid"]
            self.verify_text_match(accountSid_1, self.account_sid, "AccountSid")

            to_1 = cd_response1["To"]
            self.verify_text_match(to_1, self.callerId, "To")

            from_1 = cd_response1["From"]
            self.verify_text_match(from_1, From, "From")

            phonenumberSid_1 = cd_response1["PhoneNumberSid"]
            self.verify_text_match(phonenumberSid_1, self.callerId, "PhoneNumberSid")

            status_1 = cd_response1["Status"]
            self.verify_text_match(status_1, "completed", "PhoneNumberSid")

            direction_1 = cd_response1["Direction"]
            self.verify_text_match(direction_1, "outbound-api", "Direction")

            cd_response_details = cd_response1["Details"]
            self.log.info(cd_response_details)
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")

            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")
            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info(cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])

        except Exception as e:
            self.log.info(e)
            raise Exception

    def connectApplet_02(self):

        try:
            From = data_reader.get_cell_data("EXTC_CON_002", "From")
            apiName = data_reader.get_cell_data("EXTC_CON_002", "ApiName")
            app_id = data_reader.get_cell_data("EXTC_CON_002", "app_id")
            Input_digits = data_reader.get_cell_data("EXTC_CON_002", "Digits")
            DialWhomNumber = data_reader.get_cell_data("EXTC_CON_002", "DialWhomNumber")

            # Splitting the credentials
            appid = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, app_id)
            self.log.info(appid)
            # Splitting the credentials
            status_Call_back = self.aws_url + "/status_callback"
            self.log.info(status_Call_back)

            # URL creation
            API_URL = "https://" + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/" + self.account_sid + "/Calls/connect.json"

            self.log.info(API_URL)
            self.log.info(Input_digits)
            self.write_digit(digit_path, str(Input_digits))
            self.second_call_Status(call_path, "answer")

            self.log.info(API_URL)
            # Truncate the previous data from the#

            truncate_URL1 = self.aws_url + "truncate_response_data?filename=Tc_connect01"

            self.log.info(truncate_URL1)

            Response_connect = self.request.post(truncate_URL1)

            truncate_URL2 = self.aws_url + "truncate_response_data?filename=gather_applet"

            self.log.info(truncate_URL2)

            Response_gather = self.request.post(truncate_URL2)

            self.log.info("truncated data_URL1")

            # Post response outbound call
            self.log.info("Outgoing call sent...")
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, appid, self.callerId,
                                                 status_Call_back)
            assert response.status_code, 200
            self.log.info(response)
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            for i in range(4):
                call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                    sid)
                self.log.info(call_details)
                res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                            api_token=self.api_token).text
                cd_response = json.loads(res3)["Call"]
                self.log.info(cd_response)
                self.verify_text_match(cd_response["Sid"], sid, "CallSid")
                self.log.info(cd_response["Status"])
                if cd_response["Status"] != 'in-progress':
                    break
                else:
                    time.sleep(100)

            else:
                raise Exception
            # URL creation using sid value

            # URL creation using sid value
            URL1 = self.aws_url + "/" + sid + ".json"

            self.log.info(URL1)
            self.log.info("Status call back get request...")

            # GET using to get the Call completed details
            res1 = self.request.get(URL1)
            self.log.info(res1)

            status_Call_back_res = json.loads(res1.text)

            self.log.info(status_Call_back_res)

            sid = status_Call_back_res["CallSid"]
            self.verify_text_match(sid, sid, "sid")

            Status = status_Call_back_res["Status"]
            self.verify_text_match("completed", Status, "Status")

            self.log.info("Connect applet call details response validation in progress")

            connect_res = self.aws_url + '/Tc_connect01.json'

            res2 = self.request.get(connect_res).text
            self.log.info(connect_res)

            c_response = res2.split("\n")[0]
            connect_response = json.loads(c_response)

            self.log.info(connect_response)
            self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Dial')

            con_response1 = res2.split("\n")[1]
            self.log.info(con_response1)
            self.validation_dial_whom_details(con_response1, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'free', 'Terminal')
            self.log.info("Connect applet call details response validation in progress")

            get_value1 = self.aws_url + "gather_applet.json"

            self.log.info("Gather_Applet response validation in progress")
            gather_res = self.aws_url + '/gather_applet.json'
            gather_res2 = self.request.get(gather_res).text
            self.log.info(gather_res)
            sid_2 = gather_res2["CallSid"]
            CallSid11 = gather_res2("CallSid")
            self.verify_text_match(sid, CallSid11, "CallSid")

            CallFrom = gather_res2["CallFrom"]
            self.verify_text_match(From, CallFrom, "CallFrom")

            CallTo = gather_res2["CallTo"]
            self.verify_text_match(self.callerId, CallTo, "CallTo")

            Direction = gather_res2["Direction"]
            self.verify_text_match("outbound-dial", Direction, "Direction")

            CallType = gather_res2["CallType"]
            self.verify_text_match("incomplete", CallType, "CallType")

            flow_id = gather_res2["flow_id"]
            self.verify_text_match(str(app_id), flow_id, "flow_id")

            From_actual = gather_res2["From"]
            self.verify_text_match(From, From_actual, "From")
            To_actual = gather_res2("To")
            self.verify_text_match(self.callerId, To_actual, "To")

            Legs_output = gather_res2["Legs"]
            Leg0_output = Legs_output["0"]
            Number_actual = Leg0_output["Number"]
            self.verify_text_match(DialWhomNumber, Number_actual, "Number")

            Type_actual = Leg0_output["Type"]
            self.verify_text_match("single", Type_actual, "Type")
            OnCallDuration = Leg0_output["OnCallDuration"]

            CauseCode_actual = Leg0_output["CauseCode"]
            self.verify_text_match("NO_ANSWER", CauseCode_actual, "CauseCode")
            Cause_actual = Leg0_output["Cause"]
            self.verify_text_match("19", Cause_actual, "Cause")

            calldetails = Leg0_output["Insights"]

            Statuss = calldetails["Status"]
            self.verify_text_match("failed", Statuss, "Status")

            DetailedStatus = calldetails["DetailedStatus"]
            self.verify_text_match("FAILED_UNKNOWN_ERROR", DetailedStatus, "DetailedStatus")

            self.log.info("Exotel Call detail response validation in progress")

            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text
            self.log.info(res3)
            cd_response1 = json.loads(res3)["Call"]
            self.log.info(cd_response1)
            CallSid_1 = cd_response1["Sid"]
            self.verify_text_match(sid, CallSid_1, "Sid")

            self.log.info("Call details response validation completed")

            AccountSid_1 = cd_response1["AccountSid"]
            self.verify_text_match(self.account_sid, AccountSid_1, "AccountSid")

            From_1 = cd_response1["From"]
            self.verify_text_match(From, From_1, "From")

            # To_1 = call_2["To"]
            # self.verify_text_match(DialWhomNumber, To_1, "To");

            PhoneNumberSid_1 = cd_response1["PhoneNumberSid"]
            self.verify_text_match(self.callerId, PhoneNumberSid_1, "PhoneNumberSid")

            Status_1 = cd_response1["Status"]
            self.verify_text_match("completed", Status_1, "Status")

            Direction_1 = cd_response1["Direction"]
            self.verify_text_match("outbound-api", Direction_1, "Direction")

            AnsweredBy_1 = cd_response1["AnsweredBy"]
            self.verify_text_match("human", AnsweredBy_1, "AnsweredBy")

            Duration_1 = cd_response1["Duration"]
            # self.log.info("Duration", LogAs.PASSED, true, Duration_1);
            self.log.info("Duration:" + Duration_1)

            RecordingUrl_1 = cd_response1["RecordingUrl"]
            self.log.info("RecordingUrl:" + str(RecordingUrl_1))

            cd_response3 = cd_response1["Details"]
            Leg1Status_1 = cd_response3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = cd_response3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""
            self.verify_text_match("", Leg2Status_1, "Leg2Status")

        except Exception as e:
            raise Exception

    def connect_applet_05(self, test_name, file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_001", "ApiName")
            From = data_reader.get_cell_data("EXTC_PASS_001", "From")
            api_URL = data_reader.get_cell_data("EXTC_PASS_001", "app_id")
            DialWhomNumber = data_reader.get_cell_data("EXTC_PASS_001", "DialWhomNumber")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(Url)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "answer")
            time.sleep(2)

            status_Call_back = self.aws_url + "/status_callback"
            # Truncate the previous data from the#

            truncate_URL1 = self.aws_url + "truncate_response_data?filename=Tc_connect01"

            self.log.info(truncate_URL1)

            Response_connect = self.request.post(truncate_URL1)

            truncate_URL2 = self.aws_url + "truncate_response_data?filename=gather_applet"

            self.log.info(truncate_URL2)

            Response_gather = self.request.post(truncate_URL2)

            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)

            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            for i in range(4):
                call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                    sid)
                self.log.info(call_details)
                res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                            api_token=self.api_token).text
                cd_response = json.loads(res3)["Call"]
                self.log.info(cd_response)
                self.verify_text_match(cd_response["Sid"], sid, "CallSid")
                self.log.info(cd_response["Status"])
                if cd_response["Status"] != 'in-progress':
                    break
                else:
                    time.sleep(100)

            else:
                raise Exception

            # Status call back response  ---------------

            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            Call_Sid = callback_response["CallSid"]
            self.verify_text_match(Call_Sid, sid, 'CallSid')
            call_status = callback_response["Status"]
            self.verify_text_match("completed", call_status, 'Status')
            time.sleep(10)
            try:
                get_value_2 = self.aws_url + "/Tc_connect01.json"
                self.log.info("Dial Whom response call details response validation in progress")

                connect_res = self.aws_url + '/Tc_connect01.json'
                connect_res2 = self.request.get(connect_res).text
                self.log.info(connect_res)
                data_reader.write_data_file(file_name, row, 6, str(connect_res2))
                c_response = connect_res2.split("\n")[0]
                connect_response = json.loads(c_response)
                self.log.info(connect_response)
                self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial',
                                                  DialWhomNumber,
                                                  'busy', 'Dial')

                con_response1 = connect_res2.split("\n")[1]
                connect_response1 = json.loads(con_response1)
                self.log.info(connect_response1)
                self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial',
                                                  DialWhomNumber,
                                                  "busy", "Answered")

                con_response1 = connect_res2.split("\n")[2]
                connect_response1 = json.loads(con_response1)
                self.log.info(connect_response1)
                self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial',
                                                  DialWhomNumber,
                                                  'free', 'Terminal')
                self.log.info("Connect applet call details response validation completed")
            except Exception as e:
                self.log.info("Exception occurred connect applet call details response validation")
                self.log.info(e)
                raise Exception

            get_value1 = self.aws_url + "gather_applet.json"

            gather_response = self.request.get(get_value1)


        except Exception as e:
            self.log.info(e)
            raise Exception
