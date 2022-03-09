import json
import logging
import os
import time
import pjsua
import Utilities.logger_utility as log_utils
from Source.BaseClass.API_Request import APIRequest
from Source.BaseClass.constants import digit_path, call_path, xls_file
from Source.Pages.reusable_methods import reusable_methods
from Utilities.config_utility import ConfigUtility
from Utilities.data_reader_utility import DataReader

data_reader = DataReader()
cur_path = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(cur_path, r'../TestData/CallStatus.txt')


class Passthru_Applet(reusable_methods):
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

    def verify_EXTC_PASS_001(self, test_name, file_name):
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

            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_connect_res = self.aws_url + '/truncate_response_data?filename=Tc_connect01'
            self.log.info(truncate_connect_res)
            self.log.info(truncate_passthru_res)
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_connect_res)
            time.sleep(4)
            self.log.info("Outgoing call sent...")

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
            self.log.info("")

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

            ###########  passthru applet #################
            try:
                self.log.info("Passthru validation in progress")
                passthru_res = self.aws_url + '/passthru_applet.json'
                res2 = self.request.get(passthru_res).text
                self.log.info(passthru_res)
                pa_response = json.loads(res2)
                self.log.info(pa_response)
                data_reader.write_data_file(file_name, row, 4, str(res2))
                self.verify_text_match(pa_response["CallSid"], sid, 'CallSid')
                self.log.info(pa_response["CallFrom"])
                self.verify_text_match(pa_response["CallFrom"], From, 'CallFrom')
                self.log.info(pa_response["CallTo"])
                self.verify_text_match(pa_response["CallTo"], self.callerId, 'CallTo')
                self.log.info(pa_response["Direction"])
                self.verify_text_match(pa_response["Direction"], "outbound-dial", 'Direction')

                self.log.info(pa_response["CallType"])
                self.verify_text_match(pa_response["CallType"], "call-attempt", 'CallType')
                self.log.info(pa_response["flow_id"])
                self.verify_text_match(str(pa_response["flow_id"]), str(api_URL), 'text')
                # self.log.info(pa_response["tenant_id"])
                # self.verify_text_match(pa_response["tenant_id"], sid, 'text')
                self.log.info(pa_response["From"])
                self.verify_text_match(pa_response["From"], From, 'From')
                self.log.info(pa_response["To"])
                self.verify_text_match(pa_response["To"], self.callerId, 'To')
                # self.log.info(pa_response["digits"])
                self.log.info("Passthru response validation completed ")

            except Exception as e:
                self.log.info(" Exception occured while validatin Passthru response. ")
                self.log.info(e)

            try:
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
                self.log.info("Exception occured connect applet call details response validation")
                self.log.info(e)
                raise Exception

            #################  call details verification ##########################
            self.log.info("Over all call details response validation in progress")

            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text
            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
            cd_response1 = json.loads(res3)["Call"]
            self.log.info(cd_response1)
            self.verify_text_match(cd_response1["Sid"], sid, "CallSid")
            self.verify_text_match(cd_response1["AccountSid"], self.account_sid, "AccountSid")
            self.log.info(cd_response1["To"])
            self.verify_text_match(cd_response1["To"], self.callerId, "AccountSid")
            self.log.info(cd_response1["From"])
            self.verify_text_match(cd_response1["From"], From, "AccountSid")
            self.log.info(cd_response1["PhoneNumberSid"])
            self.verify_text_match(cd_response1["PhoneNumberSid"], self.callerId, "AccountSid")
            self.log.info(cd_response1["Status"])
            self.verify_text_match(cd_response1["Status"], "completed", "Status")
            self.log.info(cd_response1["Direction"])
            self.verify_text_match(cd_response1["Direction"], "outbound-api", "Direction")

            cd_response_details = cd_response1["Details"]
            self.log.info(cd_response_details["Leg1Status"])
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")
            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info(cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])
            self.verify_text_match(cd_response_leg_details["Leg"]["Id"], 1, "leg1")
            self.log.info(cd_response_leg_details["Leg"]["OnCallDuration"])

            self.log.info("Over all call details response validation completed")
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_002(self, test_name, file_name):
        row, count = data_reader.get_row_count(file_name)
        try:


            data_reader.write_data_file(file_name, row, 1, str(test_name))
            ApiName = data_reader.get_cell_data("EXTC_PASS_002", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_002", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_002", "app_id")
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_002", "Digit")

            self.log.info(api_URL)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(Url)
            self.write_digit(digit_path, IVR_Digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)


            status_Call_back = self.aws_url + "/status_callback"

            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'

            self.request.post(truncate_passthru_res)
            time.sleep(4)

            self.log.info("Outgoing call sent...")

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
                pjsua.CallCallback(pjsua.Call).on_dtmf_digit('#')
                if cd_response["Status"] != 'in-progress':
                    break
                else:
                    time.sleep(100)

            else:
                raise Exception

            self.log.info("Status callback response validation in progress")

            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            Call_Sid = callback_response["CallSid"]
            self.verify_text_match(Call_Sid, sid, 'CallSid')
            call_status = callback_response["Status"]
            self.verify_text_match("completed", call_status, 'Status')
            self.log.info("Status callback response validation completed")

            # sid = '0a2638d6b1cd6d49f03c340845dc162k'
            ########### passthru applet #################
            self.log.info("Passthru response validation in progress ")
            passthru_res = self.aws_url + '/passthru_applet.json'
            self.log.info(passthru_res)
            res2 = self.request.get(passthru_res).text
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            self.verify_text_match(pa_response["CallSid"], sid, 'CallSid')
            self.log.info(pa_response["CallFrom"])
            self.verify_text_match(pa_response["CallFrom"], From, 'CallFrom')
            self.log.info(pa_response["CallTo"])
            self.verify_text_match(pa_response["CallTo"], self.callerId, 'CallTo')
            self.log.info(pa_response["Direction"])
            self.verify_text_match(pa_response["Direction"], "outbound-dial", 'Direction')

            self.log.info(pa_response["CallType"])
            self.verify_text_match(pa_response["CallType"], "call-attempt", 'CallType')
            self.log.info(pa_response["flow_id"])
            self.verify_text_match(str(pa_response["flow_id"]), str(api_URL), 'text')
            # self.log.info(pa_response["tenant_id"])
            # self.verify_text_match(pa_response["tenant_id"], sid, 'text')
            self.log.info(pa_response["From"])
            self.verify_text_match(pa_response["From"], (From), 'From')
            self.log.info(pa_response["To"])
            self.verify_text_match(pa_response["To"], self.callerId, 'To')
            # self.log.info(pa_response["digits"])
            self.log.info("Passthru response validation completed ")

            self.log.info("Over all call details response validation in progress")
            #################  call details verification ##########################
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)

            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            data_reader.write_data_file(file_name, row, 8, str(res3))
            cd_response1 = json.loads(res3)["Call"]
            self.log.info(cd_response1)
            self.verify_text_match(cd_response1["Sid"], sid, "CallSid")
            self.verify_text_match(cd_response1["AccountSid"], self.account_sid, "AccountSid")
            self.log.info(cd_response1["To"])
            self.verify_text_match(cd_response1["To"], self.callerId, "To")
            self.log.info(cd_response1["From"])
            self.verify_text_match(cd_response1["From"], From, "From")
            self.log.info(cd_response1["PhoneNumberSid"])
            self.verify_text_match(cd_response1["PhoneNumberSid"], self.callerId, "PhoneNumberSid")
            self.log.info(cd_response1["Status"])
            self.verify_text_match(cd_response1["Status"], "completed", "Status")
            self.log.info(cd_response1["Direction"])
            self.verify_text_match(cd_response1["Direction"], "outbound-api", "Direction")

            cd_response_details = cd_response1["Details"]
            self.log.info(cd_response_details["Leg1Status"])
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")
            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info(cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])
            # self.verify_text_match(cd_response_leg_details["Leg"]["Id"], 1, "leg1")
            # self.log.info(cd_response_leg_details["Leg"]["OnCallDuration"])
            self.log.info("Over all call details response validation in progress")
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_003(self, test_name, file_name):
        row, col = data_reader.get_row_count(file_name)
        self.log.info(row)
        self.log.info(col)
        try:

            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_003", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_003", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_003", "app_id")
            self.log.info(api_URL)
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_003", "Digit")
            self.log.info(IVR_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.write_digit(digit_path, str(IVR_Digit))
            self.second_call_Status(call_path, "")
            time.sleep(3)

            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(5)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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
            self.log.info("Status callback response validation inprogress")

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
            self.log.info("Status callback response validation completed")

            self.log.info("passthru applet response validation in progress")

            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(res2)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(str(flow_id), str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            self.log.info("passthru_applet response validation completed")

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)

            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
            cd_response1 = json.loads(res3)["Call"]
            self.log.info(cd_response1)

            sid_1 = cd_response1["Sid"]
            self.verify_text_match(sid_1, sid, "CallSid")
            accountSid_1 = cd_response1["AccountSid"]
            self.verify_text_match(accountSid_1, self.account_sid, "AccountSid")
            to_1 = cd_response1["To"]
            self.verify_text_match(to_1, self.callerId, "To")
            from_1 = cd_response1["From"]
            self.verify_text_match(from_1, str(From), "From")
            phonenumberSid_1 = cd_response1["PhoneNumberSid"]
            self.verify_text_match(phonenumberSid_1, self.callerId, "PhoneNumberSid")
            status_1 = cd_response1["Status"]
            self.verify_text_match(status_1, "completed", "PhoneNumberSid")
            direction_1 = cd_response1["Direction"]
            self.verify_text_match(direction_1, "outbound-api", "Direction")

            cd_response_details = cd_response1["Details"]
            self.log.info(cd_response_details["Leg1Status"])
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")
            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info(cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])
            # self.verify_text_match(cd_response_leg_details["Leg"]["Id"], 1, "leg1")
            # self.log.info(cd_response_leg_details["Leg"]["OnCallDuration"])
            self.log.info("Exotel Call detail response validation in completed")
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))
        except Exception as e:
            self.log.info(e)
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            raise Exception

    def verify_EXTC_PASS_004(self, test_name, file_name):
        row, count = data_reader.get_row_count(file_name)
        try:

            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_004", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_004", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_004", "app_id")
            self.log.info(api_URL)
            Gat_Digit = data_reader.get_cell_data("EXTC_PASS_004", "Digit")
            self.log.info(Gat_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(From)
            self.write_digit(digit_path, str(Gat_Digit))
            self.second_call_Status(call_path, "")

            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_gather_res = self.aws_url + '/truncate_response_data?filename=gather_applet'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_gather_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'

            self.log.info(passthru_res)

            res2 = self.request.get(passthru_res).text
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)

            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(str(flow_id), str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, str(From), 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Gather_Applet response validation in progress")

            self.log.info("Gather_Applet response validation in progress")
            gather_res = self.aws_url + '/gather_applet.json'
            gather_res_2 = self.request.get(gather_res).text
            self.log.info(gather_res)
            data_reader.write_data_file(file_name, row, 7, str(gather_res_2))
            gather_response = json.loads(gather_res_2)
            self.log.info(gather_response)
            CallSid = gather_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = gather_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = gather_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = gather_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = gather_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = gather_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = gather_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = gather_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            self.log.info(cd_response_details["Leg1Status"])
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")
            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info(cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:
            self.log.info(e)
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            raise Exception

    def verify_EXTC_PASS_005(self, test_name, file_name):
        row, count = data_reader.get_row_count(file_name)
        try:

            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_005", "ApiName")
            From = data_reader.get_cell_data("EXTC_PASS_005", "From")
            api_URL = str(data_reader.get_cell_data("EXTC_PASS_005", "app_id"))
            DialWhomNumber = data_reader.get_cell_data("EXTC_PASS_005", "DialWhomNumber")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "No_answer")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_connect_res = self.aws_url + '/truncate_response_data?filename=Tc_connect01'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_connect_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response.text)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts" \
                                                                                                     "/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            # sid = '01fb96ac13ff17dd89a2b815500e162k'
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

            connect_res = self.aws_url + '/Tc_connect01.json'
            connect_res2 = self.request.get(connect_res).text
            self.log.info(connect_res2)
            data_reader.write_data_file(file_name, row, 4, str(connect_res2))
            c_response = connect_res2.split("\n")[0]
            connect_response = json.loads(c_response)
            self.log.info(connect_response)
            self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Dial')

            con_response1 = connect_res2.split("\n")[1]
            connect_response1 = json.loads(con_response1)
            self.log.info(connect_response1)
            self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'free', 'Terminal')

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
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
            self.verify_text_match(flow_id, api_URL, 'flow_id')
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
            # self.verify_text_match(pa_response_details["Leg1Status"], "completed", "Leg1Status")
            # self.log.info(pa_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

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

            self.log.info("CONNECT response validation in progress")

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:
            self.log.info(e)
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            raise Exception

    def verify_EXTC_PASS_006(self, test_name, file_name):
        row, col = data_reader.get_row_count(file_name)

        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_006", "ApiName")
            From = data_reader.get_cell_data("EXTC_PASS_006", "From")
            api_URL = str(data_reader.get_cell_data("EXTC_PASS_006", "app_id"))
            DialWhomNumber = data_reader.get_cell_data("EXTC_PASS_006", "DialWhomNumber")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "No_answer")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_connect_res = self.aws_url + '/truncate_response_data?filename=Tc_connect01'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_connect_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            # sid = '01fb96ac13ff17dd89a2b815500e162k'
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

            connect_res = self.aws_url + '/Tc_connect01.json'
            connect_res2 = self.request.get(connect_res).text
            self.log.info(connect_res)
            data_reader.write_data_file(file_name, row, 4, str(connect_res2))
            c_response = connect_res2.split("\n")[0]
            connect_response = json.loads(c_response)
            self.log.info(connect_response)
            self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Dial')

            con_response1 = connect_res2.split("\n")[1]
            connect_response1 = json.loads(con_response1)
            self.log.info(connect_response1)
            self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'free', 'Terminal')

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(res2)
            data_reader.write_data_file(file_name, row, 4, str(res2))
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
            self.verify_text_match(flow_id, api_URL, 'flow_id')
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
            # self.verify_text_match(pa_response_details["Leg1Status"], "completed", "Leg1Status")
            # self.log.info(pa_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

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

            self.log.info("CONNECT response validation in progress")

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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

            data_reader.write_data_file(file_name, row, 9, "PASSED")


        except Exception as e:
            data_reader.write_data_file(file_name, row, 9, "FAILED")
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_007(self, test_name, file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_007", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_007", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_007", "app_id")
            self.log.info(api_URL)
            Gat_Digit = data_reader.get_cell_data("EXTC_PASS_007", "Digit")
            self.log.info(Gat_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, Gat_Digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
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
            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            callback_response = json.loads(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(callback_response))
            self.log.info(callback_response)
            Call_Sid = callback_response["CallSid"]
            self.verify_text_match(Call_Sid, sid, 'CallSid')
            call_status = callback_response["Status"]
            self.verify_text_match("completed", call_status, 'Status')
            time.sleep(10)


            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            data_reader.write_data_file(file_name, row, 4, str(res2))
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
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            digits_2 = pa_response["digits"]
            self.log.info(digits_2)
            pass_text = digits_2.replace('"', "")
            pass_text_1 = Gat_Digit.replace(',', '').replace('#', '').replace('"', "")
            self.verify_text_match(pass_text, str(pass_text_1), 'To')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_008(self, test_name, file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_008", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_008", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_008", "app_id")
            self.log.info(api_URL)
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_008", "Digit")
            self.log.info(IVR_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, IVR_Digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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
            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            callback_response = json.loads(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            self.log.info(callback_response)
            Call_Sid = callback_response["CallSid"]
            self.verify_text_match(Call_Sid, sid, 'CallSid')
            call_status = callback_response["Status"]
            self.verify_text_match("completed", call_status, 'Status')
            time.sleep(10)

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_009(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_009", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_009", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_009", "app_id")
            self.log.info(api_URL)
            Gat_Digit = data_reader.get_cell_data("EXTC_PASS_009", "Digit")
            self.log.info(Gat_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, Gat_Digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_gather_res = self.aws_url + '/truncate_response_data?filename=gather_applet'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_gather_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Gather_Applet response validation in progress")

            gather_res = self.aws_url + '/gather_applet.json'
            gather_res2 = self.request.get(gather_res).text
            data_reader.write_data_file(file_name, row, 7, str(gather_res2))
            self.log.info(gather_res)
            gather_response = json.loads(gather_res2)
            self.log.info(gather_response)
            CallSid = gather_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = gather_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = gather_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = gather_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = gather_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = gather_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = gather_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = gather_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")
            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_010(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_010", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_010", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_010", "app_id")
            self.log.info(api_URL)
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_010", "Digit")
            self.log.info(IVR_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, IVR_Digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_011(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_011", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_011", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_011", "app_id")
            self.log.info(api_URL)
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_011", "Digit")
            self.log.info(IVR_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, IVR_Digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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
            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            time.sleep(10)

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Gather_Applet response validation in progress")

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_012(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_012", "ApiName")
            From = data_reader.get_cell_data("EXTC_PASS_012", "From")
            api_URL = str(data_reader.get_cell_data("EXTC_PASS_012", "app_id"))
            DialWhomNumber = data_reader.get_cell_data("EXTC_PASS_012", "DialWhomNumber").split(',')

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "failed")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_connect_res = self.aws_url + '/truncate_response_data?filename=Tc_connect02'
            truncate_pro_connect_res = self.aws_url + '/truncate_response_data?filename=programmable_connect'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_connect_res)
            self.request.post(truncate_pro_connect_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            sid = 'b729efcf4be775ad6fc58496de931637'
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

            connect_res = self.aws_url + '/Tc_connect02.json'
            connect_res2 = self.request.get(connect_res).text
            self.log.info(connect_res2)
            c_response = connect_res2.split("\n")[0]
            connect_response = json.loads(c_response)
            self.log.info(connect_res2)
            self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber[0],
                                              'busy', 'Dial')

            con_response1 = connect_res2.split("\n")[1]
            connect_response1 = json.loads(con_response1)
            self.log.info(connect_response1)
            self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial',  DialWhomNumber[0],
                                              'free', 'Terminal')

            pro_connect_url = self.aws_url + '/programmable_connect.json'
            pro_con_res = self.request.get(pro_connect_url).text
            self.log.info(pro_con_res)
            data_reader.write_data_file(file_name, row, 5, str(pro_con_res))
            pro_connect_response = json.loads(pro_con_res.split("\n")[0])
            self.log.info(pro_con_res)

            CallSid = pro_connect_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')

            CallFrom = pro_connect_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')

            CallTo = pro_connect_response["CallTo"]
            self.verify_text_match(CallTo, self.callerId, 'CallTo')

            CallStatus = pro_connect_response["CallStatus"]
            self.verify_text_match(CallStatus, 'ringing', 'CallStatus')



            Direction = pro_connect_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')

            CallType = pro_connect_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')

            flow_id = pro_connect_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')

            From_actual = pro_connect_response["From"]
            self.verify_text_match(From_actual, From, 'From')

            To_actual = pro_connect_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')




            self.log.info("passthru_applet response validation in progress")

            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
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
            self.verify_text_match(flow_id, api_URL, 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            DialWhomNumber_actual = pa_response["DialWhomNumber"]
            self.verify_text_match(DialWhomNumber_actual, DialWhomNumber[0], 'DialWhomNumber')

            OutgoingPhoneNumber = pa_response["OutgoingPhoneNumber"]
            self.verify_text_match(OutgoingPhoneNumber, self.callerId, 'OutgoingPhoneNumber')

            pa_response_details = pa_response["Legs"]
            self.log.info(pa_response_details["0"])
            # self.verify_text_match(pa_response_details["Leg1Status"], "completed", "Leg1Status")
            # self.log.info(pa_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            pa_response_leg_details = pa_response_details["0"]
            self.log.info(pa_response_leg_details)
            self.log.info(pa_response_leg_details["Number"])
            Number_actual = pa_response_leg_details["Number"]
            self.verify_text_match(Number_actual, DialWhomNumber[0], 'DialWhomNumber')
            Type_actual = pa_response_leg_details["Type"]
            self.verify_text_match(Type_actual, 'single', 'Type')

            CallerId_actual = pa_response_leg_details["CallerId"]
            self.verify_text_match(CallerId_actual, self.callerId, 'CallerId')

            CauseCode_actual = pa_response_leg_details["CauseCode"]
            self.verify_text_match(CauseCode_actual, 'UNALLOCATED_NUMBER', 'CauseCode')

            Cause_actual = pa_response_leg_details["Cause"]
            self.verify_text_match(Cause_actual, '1', 'Cause')

            self.log.info("Passthru response validation in progress")

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_013(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_013", "ApiName")
            From = data_reader.get_cell_data("EXTC_PASS_013", "From")
            api_URL = str(data_reader.get_cell_data("EXTC_PASS_013", "app_id"))
            DialWhomNumber = data_reader.get_cell_data("EXTC_PASS_013", "DialWhomNumber")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "failed")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_connect_res = self.aws_url + '/truncate_response_data?filename=Tc_connect02'
            truncate_pro_connect_res = self.aws_url + '/truncate_response_data?filename=programmable_connect'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_connect_res)
            self.request.post(truncate_pro_connect_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            # sid = '01fb96ac13ff17dd89a2b815500e162k'
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

            # connect_res = self.aws_url + '/Tc_connect02.json'
            # connect_res2 = self.request.get(connect_res).text
            # self.log.info(connect_res)
            # c_response = connect_res2.split("\n")[0]
            # connect_response = json.loads(c_response)
            # self.log.info(connect_response)
            # self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber,
            #                                   'busy', 'Dial')
            #
            # con_response1 = connect_res2.split("\n")[1]
            # connect_response1 = json.loads(con_response1)
            # self.log.info(connect_response1)
            # self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial', DialWhomNumber,
            #                                   'free', 'Terminal')

            pro_connect_url = self.aws_url + '/programmable_connect.json'
            pro_con_res = self.request.get(pro_connect_url).text
            self.log.info(pro_con_res)
            data_reader.write_data_file(file_name, row, 5, str(pro_con_res))
            pro_connect_response = json.loads(pro_con_res)
            self.log.info(pro_con_res)
            CallSid = pro_connect_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pro_connect_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pro_connect_response["CallTo"]
            self.verify_text_match(CallTo, self.callerId, 'CallTo')
            Direction = pro_connect_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pro_connect_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pro_connect_response["flow_id"]
            self.verify_text_match(flow_id, api_URL, 'flow_id')
            From_actual = pro_connect_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pro_connect_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
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
            self.verify_text_match(flow_id, api_URL, 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            self.log.info("CONNECT response validation in progress")

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:
            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_014(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_014", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_014", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_014", "app_id")
            self.log.info(api_URL)
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_014", "Digit")
            self.log.info(IVR_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, str(IVR_Digit))
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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


            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            time.sleep(10)

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Gather_Applet response validation in progress")
            gather_res = self.aws_url + '/gather_applet.json'
            gather_res2 = self.request.get(gather_res).text
            self.log.info(gather_res)
            data_reader.write_data_file(file_name, row, 7, str(gather_res2))
            sid_2 = pa_response["CallSid"]
            self.verify_text_match(sid_2, sid, 'CallSid')
            callFrom_2 = pa_response["CallFrom"]
            self.verify_text_match(callFrom_2, From, 'From')
            callTo_2 = pa_response["CallTo"]
            self.verify_text_match(callTo_2, self.callerId, 'CallTo')
            direction_2 = pa_response["Direction"]
            self.verify_text_match(direction_2, "outbound-dial", 'Direction')
            callType_2 = pa_response["CallType"]
            self.verify_text_match(callType_2, "call-attempt", 'CallType')
            flow_id_2 = pa_response["flow_id"]
            self.verify_text_match(flow_id_2, str(api_URL), 'flow_id')
            from_2 = pa_response["From"]
            self.verify_text_match(from_2, From, 'flow_id')
            to_2 = pa_response["To"]
            self.verify_text_match(to_2, self.callerId, 'To')
            digits_2 = pa_response["digits"]
            self.log.info(digits_2)
            # gathered_text = digits_2.replace('"', "")
            # gathered_text_1 = Gat_Digit.replace(',', '').replace('#', '')
            # self.verify_text_match(digits_2, gathered_text_1, 'To')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_015(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_015", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_015", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_015", "app_id")
            self.log.info(api_URL)
            Gat_Digit = data_reader.get_cell_data("EXTC_PASS_015", "Digit")
            self.log.info(Gat_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(From)
            self.write_digit(digit_path, str(Gat_Digit))
            self.second_call_Status(call_path, "")

            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)

            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'

            self.log.info(passthru_res)

            res2 = self.request.get(passthru_res).text
            data_reader.write_data_file(file_name, row, 4, str(res2))
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
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(str(flow_id), str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, str(From), 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            digits_2 = pa_response["digits"]
            gathered_text = digits_2.replace('"', "")
            gathered_text_1 = Gat_Digit.replace(',', '').replace('*', '')
            self.verify_text_match(gathered_text, gathered_text_1,'digits')

            self.log.info("Gather_Applet response validation in progress")

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            self.log.info(cd_response_details["Leg1Status"])
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")
            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info(cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_016(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_016", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_016", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_016", "app_id")
            self.log.info(api_URL)
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_016", "Digit")
            self.log.info(IVR_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, str(IVR_Digit))
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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
            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            time.sleep(10)

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            passthru_res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(passthru_res2))
            pa_response = json.loads(passthru_res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')

            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')

            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')

            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')

            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')

            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')

            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')

            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')



            self.log.info("Exotel Call detail response validation in progress")


            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_017(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_017", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_017", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_017", "app_id")
            self.log.info(api_URL)
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_017", "Digit")
            self.log.info(IVR_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, IVR_Digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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
            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            time.sleep(10)

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            data_reader.write_data_file(file_name, row, 4, str(res2))
            self.log.info(passthru_res)
            c_response = res2.split("\n")[0]
            pa_response = json.loads(c_response)
            self.log.info(c_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            switch_response = res2.split("\n")[1]
            switchcase_response = json.loads(switch_response)
            self.log.info(switchcase_response)
            CallSid = switchcase_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = switchcase_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = switchcase_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = switchcase_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = switchcase_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = switchcase_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = switchcase_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = switchcase_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_018(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_018", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_018", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_018", "app_id")
            self.log.info(api_URL)
            Gat_Digit = data_reader.get_cell_data("EXTC_PASS_018", "Digit")
            self.log.info(Gat_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(From)
            self.write_digit(digit_path, str(Gat_Digit))
            self.second_call_Status(call_path, "")

            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_gather_res = self.aws_url + '/truncate_response_data?filename=gather_applet'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_gather_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'

            self.log.info(passthru_res)
            res2 = self.request.get(passthru_res).text
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)

            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(str(flow_id), str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, str(From), 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Gather_Applet response validation in progress")

            self.log.info("Gather_Applet response validation in progress")
            gather_res = self.aws_url + '/gather_applet.json'
            gather_res2 = self.request.get(gather_res).text
            self.log.info(gather_res)
            data_reader.write_data_file(file_name, row, 7, str(gather_res2))
            gather_response = json.loads(gather_res2)
            self.log.info(gather_response)
            CallSid = gather_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = gather_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = gather_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = gather_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = gather_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = gather_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = gather_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = gather_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            self.log.info(cd_response_details["Leg1Status"])
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")
            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info \
                (cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_019(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_019", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_019", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_019", "app_id")
            self.log.info(api_URL)

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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
            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            time.sleep(10)

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_020(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_020", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_020", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_020", "app_id")
            self.log.info(api_URL)
            Gat_Digit = data_reader.get_cell_data("EXTC_PASS_020", "Digit")
            self.log.info(Gat_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(From)
            self.write_digit(digit_path, str(Gat_Digit))
            self.second_call_Status(call_path, "")

            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_gather_res = self.aws_url + '/truncate_response_data?filename=gather_applet'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_gather_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            self.log.info("Gather_Applet response validation in progress")
            gather_res = self.aws_url + '/gather_applet.json'
            gather_res2 = self.request.get(gather_res).text
            self.log.info(gather_res)
            data_reader.write_data_file(file_name, row, 7, str(gather_res2))
            gather_response = json.loads(gather_res2)
            self.log.info(gather_response)
            CallSid = gather_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = gather_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = gather_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = gather_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = gather_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = gather_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = gather_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = gather_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            self.log.info(cd_response_details["Leg1Status"])
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")
            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info(cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_021(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_021", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_021", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_021", "app_id")
            self.log.info(api_URL)
            IVR_Digit = data_reader.get_cell_data("EXTC_PASS_021", "Digit")
            self.log.info(IVR_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.log.info(Url)
            self.write_digit(digit_path, IVR_Digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
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


            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            time.sleep(10)

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            RecordingUrl = pa_response["RecordingUrl"]
            self.log.info(RecordingUrl)
            self.log.info(RecordingUrl)
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "voicemail", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')


            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            call_3 = cd_response1["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            # self.log.info("Leg2Status"+ str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_022(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_022", "ApiName")
            self.log.info(ApiName)
            From = data_reader.get_cell_data("EXTC_PASS_022", "From")
            self.log.info(From)
            api_URL = data_reader.get_cell_data("EXTC_PASS_022", "app_id")
            self.log.info(api_URL)
            Gat_Digit = data_reader.get_cell_data("EXTC_PASS_022", "Digit")
            self.log.info(Gat_Digit)
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(From)
            self.write_digit(digit_path, str(Gat_Digit))
            self.second_call_Status(call_path, "")

            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_gather_res = self.aws_url + '/truncate_response_data?filename=gather_applet'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_gather_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'

            self.log.info(passthru_res)
            res2 = self.request.get(passthru_res).text
            data_reader.write_data_file(file_name, row, 4, str(res2))

            pa_response = json.loads(res2)
            self.log.info(pa_response)

            CallSid = pa_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(str(flow_id), str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, str(From), 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Gather_Applet response validation in progress")

            self.log.info("Gather_Applet response validation in progress")
            gather_res = self.aws_url + '/gather_applet.json'
            gather_res2 = self.request.get(gather_res).text
            self.log.info(gather_res)
            data_reader.write_data_file(file_name, row, 7, str(gather_res2))
            gather_response = json.loads(gather_res2)
            self.log.info(gather_response)
            CallSid = gather_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = gather_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = gather_response["CallTo"]
            self.verify_text_match(CallTo, to_json, 'CallTo')
            Direction = gather_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = gather_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = gather_response["flow_id"]
            self.verify_text_match(flow_id, str(api_URL), 'flow_id')
            From_actual = gather_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = gather_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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
            self.log.info(cd_response_details["Leg1Status"])
            self.verify_text_match(cd_response_details["Leg1Status"], "completed", "Leg1Status")
            self.log.info(cd_response_details["Leg2Status"])
            # self.verify_text_match(cd_response_details["Leg2Status"], "None", "Leg2Status")

            cd_response_leg_details = cd_response_details["Legs"][0]
            self.log.info(cd_response_leg_details)
            self.log.info(cd_response_leg_details["Leg"]["Id"])

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_PASS_023(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            ApiName = data_reader.get_cell_data("EXTC_PASS_023", "ApiName")
            From = data_reader.get_cell_data("EXTC_PASS_023", "From")
            api_URL = str(data_reader.get_cell_data("EXTC_PASS_023", "app_id"))
            DialWhomNumber = data_reader.get_cell_data("EXTC_PASS_023", "DialWhomNumber")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "answer")

            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            truncate_connect_res = self.aws_url + '/truncate_response_data?filename=Tc_connect02'
            truncate_pro_connect_res = self.aws_url + '/truncate_response_data?filename=programmable_connect'
            self.request.post(truncate_passthru_res)
            self.request.post(truncate_connect_res)
            self.request.post(truncate_pro_connect_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            self.log.info("immediate response")
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
            self.log.info(call)
            sid = call["Sid"]
            self.log.info(sid)
            from_json = call["From"]
            to_json = call["To"]
            caller_json = call["PhoneNumberSid"]
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)

            for i in range(4):
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

            #sid = '0c25bb880469814bd1f342327c291637'
            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            time.sleep(10)

            connect_res = self.aws_url + '/Tc_connect02.json'
            connect_res2 = self.request.get(connect_res).text
            self.log.info(connect_res2)
            c_response = connect_res2.split("\n")[0]
            connect_response = json.loads(c_response)
            self.log.info(connect_response)
            self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Dial')

            con_response1 = connect_res2.split("\n")[1]
            connect_response1 = json.loads(con_response1)
            self.log.info(con_response1)
            self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Answered')

            con_response2 = connect_res2.split("\n")[2]
            connect_response2 = json.loads(con_response2)
            self.log.info(connect_response2)
            self.validation_dial_whom_details(connect_response2, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'free', 'Terminal')

            pro_connect_url = self.aws_url + '/programmable_connect.json'
            pro_con_res = self.request.get(pro_connect_url).text
            self.log.info(pro_con_res)
            data_reader.write_data_file(file_name, row, 5, str(pro_con_res))
            pro_connect_response = json.loads(pro_con_res)
            self.log.info(pro_con_res)
            CallSid = pro_connect_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = pro_connect_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = pro_connect_response["CallTo"]
            self.verify_text_match(CallTo, self.callerId, 'CallTo')
            Direction = pro_connect_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = pro_connect_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pro_connect_response["flow_id"]
            self.verify_text_match(flow_id, api_URL, 'flow_id')
            From_actual = pro_connect_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pro_connect_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            self.log.info("passthru_applet response validation in progress")
            passthru_res = self.aws_url + '/passthru_applet.json'
            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
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
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = pa_response["flow_id"]
            self.verify_text_match(flow_id, api_URL, 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            self.log.info("CONNECT response validation in progress")

            self.log.info("Exotel Call detail response validation in progress")
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
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

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception
