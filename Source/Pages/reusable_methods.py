import json
import logging
import os

from Utilities.config_utility import ConfigUtility
import Utilities.logger_utility as log_utils


class reusable_methods:
    config = ConfigUtility()
    log = log_utils.custom_logger(logging.INFO)

    def verify_text_match(self, actual_text, expected_text, text):
        try:
            if expected_text == actual_text:
                self.log.info(
                    "### {} VERIFICATION PASSED :\nActual Text --> {}\nExpected Text --> {}".format(text, actual_text,
                                                                                                    expected_text,
                                                                                                    ))
                assert True
            else:
                self.log.error("### {} VERIFICATION FAILED:\nActual Text --> {}\nExpected Text --> {}"
                               .format(text, actual_text, expected_text))
                assert False
        except Exception as e:
            raise Exception

    def write_digit(self, digit_path, digit):
        with open(digit_path, 'w+') as d:
            self.log.info("sent the digit {}".format(str(digit)))
            d.write(str(digit))

    def second_call_Status(self, status_path, status):
        with open(status_path, 'w+') as s:
            self.log.info("sent the status {}".format(str(status)))
            s.write(status)

    def read_data(self, path, data):
        with open(path, 'w+') as s:
            s.write(data)

    def validation_dial_whom_details(self, response, from_number, CallerId, Direction, DialWhomNumber, Status,
                                     EventType):

        try:

            print(response)
            CallSid = response["CallSid"]
            self.log.info(CallSid)
            CallFrom = response["CallFrom"]
            self.log.info(CallFrom)

            self.verify_text_match(CallFrom, from_number, "CallFrom")

            CallTo_1 = response["CallTo"]
            self.verify_text_match( CallTo_1, CallerId,"CallTo")

            From_1 = response["From"]
            self.verify_text_match(From_1, from_number, "From")

            To_1 = response["To"]
            self.verify_text_match( To_1,CallerId, "To")

            Direction_1 = response["Direction"]
            self.verify_text_match( Direction_1,Direction, "Direction")

            DialWhomNumber_1 = response["DialWhomNumber"]
            self.verify_text_match( DialWhomNumber_1,DialWhomNumber, "DialWhomNumber")

            Status_1 = response["Status"]
            self.verify_text_match( Status_1,Status, "Status")

            EventType_1 = response["EventType"]
            self.verify_text_match(EventType_1,EventType,  "EventType")

        except Exception as e:
            self.log.info(e)
            raise Exception










        ''''
            #  dial whom details verification

            get_value2 = self.aws_url + "/Tc_connect01.json"

            cr = self.request.get(get_value2)
            connect_response = cr.text

            response1 = connect_response.split("\n")[0]

            self.validation_dial_whom_details(response1, From, self.callerId, "outbound-dial", DialWhomNumber, "busy",
                                              "Dial")

            response2 = connect_response.split("\n")[1]

            self.validation_dial_whom_details(response2, From, self.callerId, "outbound-dial", DialWhomNumber, "busy",
                                              "Answered")

            response3 = connect_response.split("\n")[2]

            self.validation_dial_whom_details(response3, From, self.callerId, "outbound-dial", DialWhomNumber, "free",
                                              "Terminal")'''
