import os
import threading
import time
import pjsua
import Utilities.logger_utility as log_utils

cur_path = os.path.abspath(os.path.dirname(__file__))
path = '/home/rbt/API_automation/Exotel_master/TestData/CallStatus.txt'
log = log_utils.custom_logger()


class AccountCallback(pjsua.AccountCallback):
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
        global current_call2
        current_call2 = call

        log.info("********************************************")
        log.info(str(call))
        log.info("********************************************")

        log.info("user 2 notification: Incoming call from " + str(current_call2.info().remote_uri))

        with open(file=path, mode='r') as f:
            call_code = f.read()
            print(call_code)

        if call_code == "No_answer":
            current_call2.answer(180, "No answer")
            log.info("call has been not answered and send code 180")
        elif call_code == 'answer':
            current_call2.answer(200, "ok")
            log.info("call has been answered and send code 200")
            pjsua.Lib.instance().handle_events(10000)
            current_call2.hangup()
            log.info("call has been hangup")
        elif call_code == 'busy':
            current_call2.answer(600, 'Busy')
            log.info("call has been Busy and send code 600")
        elif call_code == 'canceled':
            current_call2.answer(180, "canceled")
            log.info("call has been canceled and send code 180")
        elif call_code == 'failed':
            current_call2.answer(608, "failed")
            log.info("call has been failed and send code 608")

        else:
            current_call2.hangup()
            log.info("call has been hangup")


class CallCallback(pjsua.CallCallback):

    def __init__(self, call=None, ):
        pjsua.CallCallback.__init__(self, call)

    # Notification when call state has changed
    def on_state(self):
        global current_call2
        global incall2
        log.info("Call with ", str(self.call.info().remote_uri), )
        log.info("is ", str(self.call.info().state_text), )
        log.info("last code = " + str(self.call.info().last_code), )
        log.info("(" + str(self.call.info().last_reason) + ")")

        if self.call.info().state == pjsua.CallState.DISCONNECTED:
            current_call2 = None
            log.info('Current call is' + str(current_call2))

            incall2 = False
        elif self.call.info().state == pjsua.CallState.CONFIRMED:
            print("User 2 has answered the call")
