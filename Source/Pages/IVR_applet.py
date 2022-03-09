import json
import os
import time
from Source.BaseClass.API_Request import APIRequest
from Source.BaseClass.constants import digit_path, call_path
from Source.Pages.reusable_methods import reusable_methods
from Utilities.data_reader_utility import DataReader

data_reader = DataReader()
cur_path = os.path.abspath(os.path.dirname(__file__))


class IVR_applet(reusable_methods):
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

    def verify_EXTC_IVR_001(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            From = data_reader.get_cell_data("EXTC_IVR_001", "From")
            self.log.info(From)
            app_id = data_reader.get_cell_data("EXTC_IVR_001", "app_id")
            self.log.info(app_id)
            Input_digits = data_reader.get_cell_data("EXTC_IVR_001", "Digit")
            self.log.info(Input_digits)
            DialWhomNumber = data_reader.get_cell_data("EXTC_IVR_001", "DialWhomNumber")
            self.log.info(DialWhomNumber)
            StatusCode = data_reader.get_cell_data("EXTC_IVR_001", "StatusCode")
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

            # Truncate the previous data from the

            truncate_data_URL1 = self.aws_url + "/truncate_response_data?filename=connect_applet"

            truncate_data_URL2 = self.aws_url + "/truncate_response_data?filename=Tc_connect01"
            # Tc_connect01.json
            self.log.info(truncate_data_URL1)
            self.request.post(truncate_data_URL1)
            self.request.post(truncate_data_URL2)

            self.log.info(truncate_data_URL2)

            time.sleep(7)
            # Post outbound call
            self.log.info("Outgoing call sent...")
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, appid, self.callerId,
                                                 status_Call_back)
            assert response.status_code == StatusCode
            self.log.info(response.text)
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

            # Extracting the and validating

            #  sid_value = "d8fd3009c3da0baa8a7bf7c5202215br";

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

            # *********************************************************

            self.log.info("Connect applet response ...")
            connect_applet_response = self.aws_url + '/connect_applet.json'
            con_res = self.request.get(connect_applet_response).text
            self.log.info(con_res)
            data_reader.write_data_file(file_name, row, 5, str(con_res))
            connect_response = json.loads(con_res)
            self.log.info(con_res)
            CallSid = connect_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            CallFrom = connect_response["CallFrom"]
            self.verify_text_match(CallFrom, From, 'CallFrom')
            CallTo = connect_response["CallTo"]
            self.verify_text_match(CallTo, self.callerId, 'CallTo')
            Direction = connect_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", 'Direction')
            CallType = connect_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", 'CallType')
            flow_id = connect_response["flow_id"]
            self.verify_text_match(flow_id, str(app_id), 'flow_id')
            From_actual = connect_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = connect_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')
            digits_actual = connect_response["digits"]
            digits_2 = connect_response["digits"]
            digit_text = digits_actual.replace('"', "")
            digit_text_1 = Input_digits.replace(' ,', '').replace('#', '')
            print(digit_text, digit_text_1)

            # *********************************************************
            #

            self.log.info("Dial Whom response ...")
            # GET using the call details for connect applet #
            connect_res = self.aws_url + '/Tc_connect01.json'
            connect_res2 = self.request.get(connect_res).text
            self.log.info(connect_res2)
            data_reader.write_data_file(file_name, row, 6, str(connect_res2))
            c_response = connect_res2.split("\n")[0]
            connect_response = json.loads(c_response)
            self.log.info(connect_response)
            self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Dial')

            con_response1 = connect_res2.split("\n")[1]
            connect_response1 = json.loads(con_response1)
            self.log.info(connect_response1)
            self.validation_dial_whom_details(connect_response1, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Answered')

            con_response2 = connect_res2.split("\n")[2]
            connect_response2 = json.loads(con_response2)
            self.log.info(connect_response2)
            self.validation_dial_whom_details(connect_response2, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'free', 'Terminal')

            # over all call details #
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text

            self.log.info(res3)
            data_reader.write_data_file(file_name, row, 8, str(res3))
            call_2 = json.loads(res3)["Call"]
            self.log.info(call_2)

            self.log.info(call_2)

            CallSid_1 = call_2["Sid"]
            self.verify_text_match(sid, CallSid_1, "Sid")

            self.log.info("Call details validation completed")
            AccountSid_1 = call_2["AccountSid"]
            self.verify_text_match(self.account_sid, AccountSid_1, "AccountSid")

            To_1 = call_2["To"]
            self.verify_text_match(self.callerId, To_1, "To")

            From_1 = call_2["From"]
            self.verify_text_match(From, From_1, "From")

            PhoneNumberSid_1 = call_2["PhoneNumberSid"]
            self.verify_text_match(self.callerId, PhoneNumberSid_1, "PhoneNumberSid")

            Status_1 = call_2["Status"]
            self.verify_text_match("completed", Status_1, "Status")

            Direction_1 = call_2["Direction"]
            self.verify_text_match("outbound-api", Direction_1, "Direction")

            call_3 = call_2["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            # Leg2Status_1 = call_3["Leg2Status"]
            # if Leg2Status_1 is None:
            #     Leg2Status_1 = ""
            #
            # self.log.info("Leg2Status", str(Leg2Status_1))
            # self.log.info("Leg2Status:" + Leg2Status_1)
            # self.verify_text_match("completed", Leg2Status_1, "Leg2Status")
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))
        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_IVR_002(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            From = data_reader.get_cell_data("EXTC_IVR_002", "From")
            self.log.info(From)
            app_id = data_reader.get_cell_data("EXTC_IVR_002", "app_id")
            self.log.info(app_id)
            Input_digits = data_reader.get_cell_data("EXTC_IVR_002", "Digit")
            self.log.info(Input_digits)
            StatusCode = data_reader.get_cell_data("EXTC_IVR_002", "StatusCode")
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
            self.second_call_Status(call_path, "")

            # Truncate the previous data from the

            truncate_data_URL1 = self.aws_url + "/truncate_response_data?filename=passthru_applet"
            self.log.info(truncate_data_URL1)
            self.request.post(truncate_data_URL1)

            time.sleep(7)
            # Post outbound call
            self.log.info("Outgoing call sent...")
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, appid, self.callerId,
                                                 status_Call_back)
            time.sleep(7)
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            self.log.info(response)
            call = json.loads(response.content)["Call"]
            time.sleep(60)
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

            #  passthru applet response

            passthru_res = self.aws_url + "/passthru_applet.json"

            self.log.info("passthru_applet validation in progress")

            self.log.info(passthru_res)

            res2 = self.request.get(passthru_res).text
            pa_response = json.loads(res2)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            self.log.info(pa_response)

            # Extracting the and validating
            CallSid11 = pa_response["CallSid"]
            self.verify_text_match(sid, CallSid11, "CallSid")

            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, "CallFrom")

            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, self.callerId, "CallTo")

            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", "Direction")
            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", "CallType")

            flow_id = pa_response["flow_id"]
            self.verify_text_match(str(app_id), str(flow_id), "flow_id")

            From_actual = pa_response["From"]
            self.verify_text_match(str(From), str(From_actual), "From")
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, "To")

            digits = pa_response["digits"]
            self.verify_text_match(digits.replace("\"", ""), "", "digits")

            #################  call details verification ##########################
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

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))
        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_IVR_003(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            From = data_reader.get_cell_data("EXTC_IVR_003", "From")
            apiName = data_reader.get_cell_data("EXTC_IVR_003", "ApiName")
            api_URL = data_reader.get_cell_data("EXTC_IVR_003", "app_id")
            Input_digit = data_reader.get_cell_data("EXTC_IVR_003", "Digit")
            status = data_reader.get_cell_data("EXTC_PASS_003", "StatusCode")

            app_id = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(app_id)
            self.write_digit(digit_path, Input_digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)
            status_Call_back = self.aws_url + "/status_callback"

            # URL creation
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"

            self.log.info(API_URL)
            # Truncate the previous data from the

            truncate_data_URL2 = self.aws_url + "/truncate_response_data?filename=passthru_applet"

            # Tc_connect01.json
            self.log.info(truncate_data_URL2)

            status_Call_back = self.aws_url + "/status_callback"
            self.log.info(status_Call_back)
            res5 = self.request.post(truncate_data_URL2)

            # Post outbound call

            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, app_id, self.callerId,
                                                 status_Call_back)

            # Extracting the and validating
            self.log.info(response)
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            call = json.loads(response.content)["Call"]
            time.sleep(100)
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

            #  sid = "f3a181fe13bca3df165434f366bd15b5";

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

            self.log.info("Passthru applet validation in progress")

            passthru_res = self.aws_url + '/passthru_applet.json'

            res2 = self.request.get(passthru_res).text
            self.log.info(passthru_res)
            data_reader.write_data_file(file_name, row, 4, str(res2))
            pa_response = json.loads(res2)
            self.log.info(pa_response)
            # Extracting the and validating

            CallSid11 = pa_response["CallSid"]
            self.verify_text_match(CallSid11, sid, "CallSid")

            CallFrom = pa_response["CallFrom"]
            self.verify_text_match(CallFrom, From, "CallFrom")

            CallTo = pa_response["CallTo"]
            self.verify_text_match(CallTo, self.callerId, "CallTo")

            Direction = pa_response["Direction"]
            self.verify_text_match(Direction, "outbound-dial", "Direction")

            CallType = pa_response["CallType"]
            self.verify_text_match(CallType, "call-attempt", "CallType")

            flow_id = pa_response["flow_id"]
            self.verify_text_match(str(flow_id), str(api_URL), "flow_id")

            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, "From")

            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, "To")

            digits = pa_response["digits"]
            self.verify_text_match("7", digits.replace("\"", ""), "digits")

            self.log.info("Passthru applet validation completed")

            self.log.info("********************************************************")

            self.log.info("Exotel Call detail validation in progress")

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

            CallSid_1 = cd_response1["Sid"]
            self.verify_text_match(sid, CallSid_1, "Sid")

            self.log.info("Call details validation completed")

            AccountSid_1 = cd_response1["AccountSid"]
            self.verify_text_match(AccountSid_1, self.account_sid, "AccountSid")

            To_1 = cd_response1.get("To")
            self.verify_text_match(To_1, self.callerId, "To")

            From_1 = cd_response1["From"]
            self.verify_text_match(From, From_1, "From")

            PhoneNumberSid_1 = cd_response1["PhoneNumberSid"]
            self.verify_text_match(PhoneNumberSid_1, self.callerId, "PhoneNumberSid")

            Status_1 = cd_response1["Status"]
            self.verify_text_match("completed", Status_1, "Status")

            Direction_1 = cd_response1["Direction"]
            self.verify_text_match("outbound-api", Direction_1, "Direction")

            # AnsweredBy_1 = cd_response1["AnsweredBy"]
            # self.verify_text_match(AnsweredBy_1, "human", "AnsweredBy")

            RecordingUrl_1 = cd_response1["RecordingUrl"]
            self.log.info("RecordingUrl:" + RecordingUrl_1)

            #  ConversationDuration_1 = call_2.get("ConversationDuration").to();
            # add1("ConversationDuration", LogAs.PASSED, true, ConversationDuration_1);
            # self.log.info("ConversationDuration:" + ConversationDuration_1);

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

    def verify_EXTC_IVR_004(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)

            From = data_reader.get_cell_data("EXTC_IVR_004", "From")
            apiName = data_reader.get_cell_data("EXTC_IVR_004", "ApiName")
            api_URL = data_reader.get_cell_data("EXTC_IVR_004", "app_id")
            Input_digit = data_reader.get_cell_data("EXTC_IVR_004", "Digit")
            status = data_reader.get_cell_data("EXTC_IVR_004", "StatusCode")

            status_value = "200"  # data_reader.get_cell_data("EXTC_PASS_001", "StatusCode");
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            appid = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(api_URL)
            self.write_digit(digit_path, Input_digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)

            # Splitting the credentials
            StatusCallback = self.aws_url + "/status_callback"
            self.log.info(StatusCallback)

            # URL creation
            API_URL = "https://" + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/" + self.account_sid + "/Calls/connect.json"

            self.log.info(API_URL)

            # Truncate the previous data from the

            truncate_data_URL2 = self.aws_url + "/truncate_response_data?filename=gather_applet"

            # Tc_connect01.json
            self.log.info(truncate_data_URL2)

            res5 = self.request.post(truncate_data_URL2)

            self.log.info("truncated data_URL2")
            API_URL = "https://" + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/" + self.account_sid + "/Calls/connect.json"

            self.log.info(API_URL)

            status_Call_back = self.aws_url + "/status_callback"
            self.log.info(status_Call_back)
            # Post outbound call

            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, appid, self.callerId,
                                                 status_Call_back)
            # Extracting the and validating
            assert response.status_code, 200
            self.log.info(response)
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

            # URL creation using sid value

            # sid_value = "f3a181fe13bca3df165434f366bd15b5";

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

            # To get the call details for Programmable Gather Applet #
            get_value2 = self.aws_url + "/gather_applet.json"

            gather_res2 = self.request.get(get_value2).text
            data_reader.write_data_file(file_name, row, 7, str(gather_res2))
            ga_response = json.loads(gather_res2)

            # Extracting the and validating
            CallSid12 = ga_response["CallSid"]
            self.verify_text_match(sid, CallSid12, "CallSid")

            CallFrom12 = ga_response["CallFrom"]
            self.verify_text_match(From, CallFrom12, "CallFrom")

            CallTo12 = ga_response["CallTo"]
            self.verify_text_match(self.callerId, CallTo12, "CallTo")

            Direction12 = ga_response["Direction"]
            self.verify_text_match("outbound-dial", Direction12, "Direction")

            CallType12 = ga_response["CallType"]
            self.verify_text_match("call-attempt", CallType12, "CallType")

            flow_id12 = ga_response["flow_id"]
            self.verify_text_match(str(api_URL), flow_id12, "flow_id")

            From_actual12 = ga_response["From"]
            self.verify_text_match(From, From_actual12, "From")

            To_actual12 = ga_response["To"]
            self.verify_text_match(self.callerId, To_actual12, "To")

            digits = ga_response["digits"]
            Digitss = digits.replace("\"", "")
            self.verify_text_match(Input_digit.replace("#", "").replace(",", ""), Digitss, "digits")

            self.log.info("********************************************************")

            self.log.info("Exotel Call detail validation in progress")

            #################  call details verification ##########################
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text
            call_2 = json.loads(res3)["Call"]
            self.log.info(call_2)
            data_reader.write_data_file(file_name, row, 8, str(res3))
            CallSid_1 = call_2["Sid"]
            self.verify_text_match(sid, CallSid_1, "Sid")

            self.log.info("Call details validation completed")

            AccountSid_1 = call_2["AccountSid"]
            self.verify_text_match(self.account_sid, AccountSid_1, "AccountSid")

            To_1 = call_2["To"]
            self.verify_text_match(self.callerId, To_1, "To")

            From_1 = call_2["From"]
            self.verify_text_match(From, From_1, "From")

            PhoneNumberSid_1 = call_2["PhoneNumberSid"]
            self.verify_text_match(self.callerId, PhoneNumberSid_1, "PhoneNumberSid")

            Status_1 = call_2["Status"]
            self.verify_text_match("completed", Status_1, "Status")

            Direction_1 = call_2["Direction"]
            self.verify_text_match("outbound-api", Direction_1, "Direction")

            AnsweredBy_1 = call_2["AnsweredBy"]
            self.verify_text_match("human", AnsweredBy_1, "AnsweredBy")


            RecordingUrl_1 = call_2["RecordingUrl"]
            self.log.info("RecordingUrl:" + RecordingUrl_1)

            #		 ConversationDuration_1 = call_2["ConversationDuration"]
            #		self.log.info("ConversationDuration:" + ConversationDuration_1);

            call_3 = call_2["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            self.log.info("Leg2Status:" + Leg2Status_1)
            self.verify_text_match("", Leg2Status_1, "Leg2Status")
            data_reader.write_data_file(file_name, row, 9, str("PASSED"))


        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_IVR_005(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)

        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            From = data_reader.get_cell_data("EXTC_IVR_005", "From")
            apiName = data_reader.get_cell_data("EXTC_IVR_005", "ApiName")
            api_URL = data_reader.get_cell_data("EXTC_IVR_005", "app_id")
            status = data_reader.get_cell_data("EXTC_IVR_005", "StatusCode")
            Input_digits = data_reader.get_cell_data("EXTC_IVR_005", "Digit")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.write_digit(digit_path, Input_digits)

            self.second_call_Status(call_path, "")

            time.sleep(2)

            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
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
            # sid = '679360b299efd95d2e69d82cbaf6162p'

            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            CallSid = callback_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            call_status = callback_response["Status"]
            self.verify_text_match("completed", call_status, 'Status')


            # URL creation using sid value
            self.log.info("Passthru applet validation in progress")

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
            self.verify_text_match(str(flow_id), str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            digits_2 = pa_response["digits"]
            gathered_text = digits_2.replace('"', "")
            gathered_text_1 = Input_digits.replace(',', '').replace('#', '').replace(' ', '')
            self.verify_text_match(gathered_text, gathered_text_1, 'To')

            self.log.info("Passthru applet validation completed")

            self.log.info("********************************************************")

            self.log.info("Exotel Call detail validation in progress")

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
            self.verify_text_match(status_1, "completed", "Status")
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

    def verify_EXTC_IVR_006(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)

        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            From = data_reader.get_cell_data("EXTC_IVR_006", "From")
            apiName = data_reader.get_cell_data("EXTC_IVR_006", "ApiName")
            api_URL = data_reader.get_cell_data("EXTC_IVR_006", "app_id")
            status = data_reader.get_cell_data("EXTC_IVR_006", "StatusCode")
            Input_digits = data_reader.get_cell_data("EXTC_IVR_006", "Digit")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.write_digit(digit_path, Input_digits)

            self.second_call_Status(call_path, "")

            time.sleep(2)

            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
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
            # sid = '679360b299efd95d2e69d82cbaf6162p'

            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            CallSid = callback_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            call_status = callback_response["Status"]
            self.verify_text_match("completed", call_status, 'Status')

            self.log.info("********************************************************")

            self.log.info("Exotel Call detail validation in progress")

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
            self.verify_text_match(status_1, "completed", "Status")
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

    def verify_EXTC_IVR_007(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)

        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            From = data_reader.get_cell_data("EXTC_IVR_007", "From")
            apiName = data_reader.get_cell_data("EXTC_IVR_007", "ApiName")
            api_URL = data_reader.get_cell_data("EXTC_IVR_007", "app_id")
            status = data_reader.get_cell_data("EXTC_IVR_007", "StatusCode")
            Input_digits = data_reader.get_cell_data("EXTC_IVR_007", "Digit")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.write_digit(digit_path, Input_digits)

            self.second_call_Status(call_path, "")

            time.sleep(2)

            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
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
            # sid = '679360b299efd95d2e69d82cbaf6162p'

            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            CallSid = callback_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            call_status = callback_response["Status"]
            self.verify_text_match("completed", call_status, 'Status')
            # URL creation using sid value
            self.log.info("Passthru applet validation in progress")

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
            self.verify_text_match(str(flow_id), str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            digits_2 = pa_response["digits"]
            gathered_text = digits_2.replace('"', "")
            gathered_text_1 = Input_digits.replace(',', '').replace('#', '').replace(' ', '')
            self.verify_text_match(gathered_text, gathered_text_1, 'To')

            self.log.info("Passthru applet validation completed")

            self.log.info("********************************************************")

            self.log.info("Exotel Call detail validation in progress")

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
            self.verify_text_match(status_1, "completed", "Status")
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

    def verify_EXTC_IVR_008(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)

        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            From = data_reader.get_cell_data("EXTC_IVR_008", "From")
            apiName = data_reader.get_cell_data("EXTC_IVR_008", "ApiName")
            api_URL = data_reader.get_cell_data("EXTC_IVR_008", "app_id")
            status = data_reader.get_cell_data("EXTC_IVR_008", "StatusCode")
            Input_digits = data_reader.get_cell_data("EXTC_IVR_008", "Digit")

            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)

            self.write_digit(digit_path, Input_digits)

            self.second_call_Status(call_path, "")

            time.sleep(2)

            status_Call_back = self.aws_url + "/status_callback"
            truncate_passthru_res = self.aws_url + '/truncate_response_data?filename=passthru_applet'
            self.request.post(truncate_passthru_res)
            time.sleep(4)
            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
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
            # sid = '679360b299efd95d2e69d82cbaf6162p'

            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            CallSid = callback_response["CallSid"]
            self.verify_text_match(CallSid, sid, 'CallSid')
            call_status = callback_response["Status"]
            self.verify_text_match("completed", call_status, 'Status')
            # URL creation using sid value
            self.log.info("Passthru applet validation in progress")

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
            self.verify_text_match(str(flow_id), str(api_URL), 'flow_id')
            From_actual = pa_response["From"]
            self.verify_text_match(From_actual, From, 'From')
            To_actual = pa_response["To"]
            self.verify_text_match(To_actual, self.callerId, 'To')

            # digits_2 = pa_response["digits"]
            # gathered_text = digits_2.replace('"', "")
            # gathered_text_1 = Input_digits.replace(',', '').replace('#', '').replace(' ', '')
            # self.verify_text_match(gathered_text, gathered_text_1, 'To')

            self.log.info("Passthru applet validation completed")

            self.log.info("********************************************************")

            self.log.info("Exotel Call detail validation in progress")

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
            self.verify_text_match(status_1, "completed", "Status")
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

    def verify_EXTC_IVR_009(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)
            From = data_reader.get_cell_data("EXTC_IVR_009", "From")
            apiName = data_reader.get_cell_data("EXTC_IVR_009", "ApiName")
            api_URL = data_reader.get_cell_data("EXTC_IVR_009", "app_id")
            Input_digit = data_reader.get_cell_data("EXTC_IVR_009", "Digit")
            status = data_reader.get_cell_data("EXTC_IVR_009", "StatusCode")

            status_value = "200"  # data_reader.get_cell_data("EXTC_PASS_001", "StatusCode");
            API_URL = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/connect.json"
            appid = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(api_URL)
            self.write_digit(digit_path, Input_digit)
            self.second_call_Status(call_path, "")
            time.sleep(2)

            # Splitting the credentials
            StatusCallback = self.aws_url + "/status_callback"
            self.log.info(StatusCallback)

            # URL creation
            API_URL = "https://" + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/" + self.account_sid + "/Calls/connect.json"

            self.log.info(API_URL)

            # Truncate the previous data from the

            truncate_data_URL2 = self.aws_url + "/truncate_response_data?filename=gather_applet"

            # Tc_connect01.json
            self.log.info(truncate_data_URL2)

            res5 = self.request.post(truncate_data_URL2)

            self.log.info("truncated data_URL2")
            API_URL = "https://" + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/" + self.account_sid + "/Calls/connect.json"

            self.log.info(API_URL)

            status_Call_back = self.aws_url + "/status_callback"
            self.log.info(status_Call_back)
            # Post outbound call

            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, appid, self.callerId,
                                                 status_Call_back)
            # Extracting the and validating
            assert response.status_code, 200
            self.log.info(response)
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

            # URL creation using sid value

            # sid = "ca5f149ad3b33b70db0bf5e0cefc162p"

            URL_1 = self.aws_url + "/" + sid + ".json"
            Status_callback_res = self.request.get(URL_1).text
            self.log.info(Status_callback_res)
            data_reader.write_data_file(file_name, row, 3, str(Status_callback_res))
            callback_response = json.loads(Status_callback_res)
            self.log.info(callback_response)
            CallSid1 = callback_response["CallSid"]
            self.verify_text_match(sid, CallSid1, "CallSid")
            completed1 = callback_response["Status"]

            self.verify_text_match("completed", completed1, "Status")

            CallSid1 = callback_response["DateUpdated"]

            self.log.info(str(CallSid1))
            # To get the call details for Programmable Gather Applet #
            get_value2 = self.aws_url + "/gather_applet.json"

            res2 = self.request.get(get_value2).text

            ga_response = json.loads(res2)

            # Extracting the and validating
            CallSid12 = ga_response["CallSid"]
            self.verify_text_match(sid, CallSid12, "CallSid")

            CallFrom12 = ga_response["CallFrom"]
            self.verify_text_match(From, CallFrom12, "CallFrom")

            CallTo12 = ga_response["CallTo"]
            self.verify_text_match(self.callerId, CallTo12, "CallTo")

            Direction12 = ga_response["Direction"]
            self.verify_text_match("outbound-dial", Direction12, "Direction")

            CallType12 = ga_response["CallType"]
            self.verify_text_match("call-attempt", CallType12, "CallType")

            flow_id12 = ga_response["flow_id"]
            self.verify_text_match(str(api_URL), flow_id12, "flow_id")

            From_actual12 = ga_response["From"]
            self.verify_text_match(From, From_actual12, "From")

            To_actual12 = ga_response["To"]
            self.verify_text_match(self.callerId, To_actual12, "To")

            # digits = ga_response["digits"]
            # Digitss = digits.replace("\"", "")
            # self.verify_text_match(Input_digit.replace("#", "").replace(",", ""), Digitss, "digits")

            self.log.info("********************************************************")

            self.log.info("Exotel Call detail validation in progress")

            #################  call details verification ##########################
            call_details = 'https://' + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/exotest1m/Calls/{}.json?details=true".format(
                sid)
            self.log.info(call_details)
            res3 = self.request.call_details_get_exotel(call_details, api_key=self.api_key,
                                                        api_token=self.api_token).text
            call_2 = json.loads(res3)["Call"]
            self.log.info(call_2)
            data_reader.write_data_file(file_name, row, 8, str(res3))
            CallSid_1 = call_2["Sid"]
            self.verify_text_match(sid, CallSid_1, "Sid")

            self.log.info("Call details validation completed")

            AccountSid_1 = call_2["AccountSid"]
            self.verify_text_match(self.account_sid, AccountSid_1, "AccountSid")

            To_1 = call_2["To"]
            self.verify_text_match(self.callerId, To_1, "To")

            From_1 = call_2["From"]
            self.verify_text_match(From, From_1, "From")

            PhoneNumberSid_1 = call_2["PhoneNumberSid"]
            self.verify_text_match(self.callerId, PhoneNumberSid_1, "PhoneNumberSid")

            Status_1 = call_2["Status"]
            self.verify_text_match("completed", Status_1, "Status")

            Direction_1 = call_2["Direction"]
            self.verify_text_match("outbound-api", Direction_1, "Direction")

            call_3 = call_2["Details"]
            Leg1Status_1 = call_3["Leg1Status"]
            self.verify_text_match("completed", Leg1Status_1, "Leg1Status")

            Leg2Status_1 = call_3["Leg2Status"]
            self.log.info(Leg2Status_1)
            if Leg2Status_1 is None:
                Leg2Status_1 = ""

            self.log.info("Leg2Status:" + Leg2Status_1)
            self.verify_text_match("", Leg2Status_1, "Leg2Status")

            data_reader.write_data_file(file_name, row, 9, str("PASSED"))

        except Exception as e:

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception

    def verify_EXTC_IVR_010(self,test_name,file_name):
        row, count = data_reader.get_row_count(file_name)
        try:
            data_reader.write_data_file(file_name, row, 1, test_name)

            From = data_reader.get_cell_data("EXTC_IVR_010", "From")
            apiName = data_reader.get_cell_data("EXTC_IVR_010", "ApiName")
            api_URL = data_reader.get_cell_data("EXTC_IVR_010", "app_id")
            DialWhomNumber = data_reader.get_cell_data("EXTC_IVR_010", "DialWhomNumber")

            Url = 'http://my.exotel.com/{}/exoml/start_voice/{}'.format(self.account_sid, api_URL)
            self.log.info(Url)
            self.write_digit(digit_path, "")
            self.second_call_Status(call_path, "answer")

            StatusCallback = self.aws_url + "/status_callback"

            self.log.info(StatusCallback)

            status_Call_back = self.aws_url + "/status_callback"
            self.log.info(status_Call_back)

            #Truncating the Passthru Data#

            truncate_data_URL1 = self.aws_url + "truncate_response_data?filename=passthru_applet"
            res1 = self.request.post(truncate_data_URL1)

            # Truncating the programmable connect applet

            truncate_data_URL2 = self.aws_url + "truncate_response_data?filename=programmable_connect"
            res2 = self.request.post(truncate_data_URL2)

            truncate_data_URL3 = self.aws_url + "truncate_response_data?filename=Tc_connect02"
            res3 = self.request.post(truncate_data_URL3)

            #URL Creation #

            API_URL = "https://" + self.api_key + ":" + self.api_token + "@" + self.subdomain + "/v1/Accounts/" + self.account_sid + "/Calls/connect.json"

            self.log.info(API_URL)

            response = self.request.call_to_flow(API_URL, self.api_key, self.api_token, From, Url, self.callerId,
                                                 status_Call_back)
            self.log.info(response)
            data_reader.write_data_file(file_name, row, 2, str(response.text))
            self.log.info("immediate response")
            call = json.loads(response.content)["Call"]
            self.log.info(call)
            sid = call["Sid"]
            from_json = call["From"]
            caller_json = call["PhoneNumberSid"]
            sid = '0ac43c72f8230d1ca68371c58a86162f'
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


            self.log.info("Connect applet call details response validation in progress")

            connect_res = self.aws_url + '/Tc_connect01.json'
            connect_res2 = self.request.get(connect_res).text
            self.log.info(connect_res)
            data_reader.write_data_file(file_name, row, 6, str(connect_res2))
            c_response = connect_res2.split("\n")[0]
            connect_response = json.loads(c_response)
            self.log.info(connect_response)
            self.validation_dial_whom_details(connect_response, From, self.callerId, 'outbound-dial', DialWhomNumber,
                                              'busy', 'Dial')

            con_response1 = connect_res2.split("\n")[1]
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

            # To get the call details for the programmable_connect #
            pro_connect_url = self.aws_url + '/programmable_connect.json'
            pro_con_res = self.request.get(pro_connect_url).text
            data_reader.write_data_file(file_name, row, 5, str(pro_con_res))
            self.log.info(pro_con_res)
            pro_connect_response = json.loads(pro_con_res)
            self.log.info(pro_connect_response)

            # Extracting the and validating
            CallSid12 = pro_connect_response["CallSid"]
            self.verify_text_match(sid, CallSid12, "CallSid")

            CallFrom12 = pro_connect_response["CallFrom"]
            self.verify_text_match(From, CallFrom12, "CallFrom")

            CallTo12 = pro_connect_response["CallTo"]
            self.verify_text_match(self.callerId, CallTo12, "CallTo")

            CallType12 = pro_connect_response["CallType"]
            self.verify_text_match("call-attempt", CallType12, "CallType")

            flow_id12 = pro_connect_response["flow_id"]
            self.verify_text_match(str(api_URL), flow_id12, "flow_id")

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

            data_reader.write_data_file(file_name, row, 9, str("FAILED"))
            self.log.info(e)
            raise Exception
