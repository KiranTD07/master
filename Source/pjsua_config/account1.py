import os
import threading
import time

import pjsua
import Utilities.logger_utility as log_utils

lib = None
cur_path = os.path.abspath(os.path.dirname(__file__))
path = '/home/rbt/API_automation/Exotel_master/TestData/Digit.txt'
log = log_utils.custom_logger()


def play_call_audio(call):
    time.sleep(0.5)
    call.answer(200)
    log.info("call has been answered by user 1")


class MyAccountCallback(pjsua.AccountCallback):
    sem = None

    def __init__(self, account=None, ):
        pjsua.AccountCallback.__init__(self, account)

    def wait(self):
        self.sem = threading.Semaphore(0)
        self.sem.acquire()

    def on_reg_state(self):
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()

    def on_incoming_call(self, call, ):
        global current_call
        log.info("=======================================")
        log.info(str(call))
        log.info("=======================================")

        current_call = call
        log.info("user 1 notification: Incoming call from " + str(call.info().remote_uri))
        # print("Press 'a' to answer")
        call_cb = MyCallCallback(current_call, )
        current_call.set_callback(call_cb)
        # current_call.answer(200)
        try:
            play_call_audio(current_call)
        except pjsua.Error as e:
            print("Exception: " + str(e))
            return None


# Callback to receive events from Call
class MyCallCallback(pjsua.CallCallback):

    def __init__(self, call=None, ):
        pjsua.CallCallback.__init__(self, call)

    # Notification when call state has changed
    def on_state(self):
        global current_call
        global in_call
        log.info("Call with " + str(self.call.info().remote_uri))
        log.info("is " + str(self.call.info().state_text))
        log.info("last code = " + str(self.call.info().last_code))
        log.info("(" + str(self.call.info().last_reason) + ")")

        if self.call.info().state == pjsua.CallState.DISCONNECTED:
            current_call = None
            log.info('Current call is ****************** ' + str(current_call))
            in_call = False

        elif self.call.info().state == pjsua.CallState.CONFIRMED:
            log.info("user 1 answered the Call")
            # log.info("Hey !!!!! Hope you are doing GOOD !!!!!!!!!!")
            pjsua.Lib.instance().handle_events(1000)
            with open(file=path, mode='r+') as f:
                digit = f.read()
            log.info(str(digit))
            if digit != '':
                time.sleep(0.5)
                ## read the inputh fecth the details
                self.on_dtmf_digits2(digit)
            else:
                pass
            pjsua.Lib.instance().handle_events(30000)

            # self.call.hangup()
            '''while in_call:
                if self.call.info().state == pjsua.CallState.DISCONNECTED:
                    in_call = False
                    break
                pass

            self.call.hangup()
            in_call = False'''

    # Notification when call's media state has changed.
    def on_media_state(self):
        if self.call.info().media_state == pjsua.MediaState.ACTIVE:
            log.info("Media is now active")
            call_slot = self.call.info().conf_slot
            pjsua.Lib.instance().conf_connect(call_slot, 0)
            pjsua.Lib.instance().conf_connect(0, call_slot)
        else:
            log.info("Media is inactive")

    def on_dtmf_digits2(self, digit):
        try:
            for u in digit.split(','):
                log.info(str(u))
                status = pjsua.Call.send_request(self.call, method="INFO", content_type=" application/dtmf-relay",
                                                 body="Signal=" + str(u) + "\n" + "Duration=160")
                pjsua.Lib.instance().handle_events(1000)
                log.info(status)
        except Exception as e:
            raise Exception
