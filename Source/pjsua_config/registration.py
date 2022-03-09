import time
import pjsua
from Source.pjsua_config.account1 import MyAccountCallback
from Source.pjsua_config.account2 import AccountCallback
import Utilities.logger_utility as log_utils

lib = pjsua.Lib()

log = log_utils.custom_logger()


# # acc_cfg.ka_interval =30; re-registration period
# def log_cb(level, str, len):
#     print(str, )


class PJSIP_Config:
    global in_call
    global acc
    global acc2
    ua_cfg1 = pjsua.UAConfig()
    ua_cfg1.max_calls = 50
    ua_cfg1.thread_cnt = 10
    # lib.init(ua_cfg=ua_cfg1,log_cfg=pjsua.LogConfig(level=4, filename=log_filename, callback=log_cb) )
    lib.init(ua_cfg=ua_cfg1)
    lib.create_transport(pjsua.TransportType.TLS, pjsua.TransportConfig(5060))
    #lib.set_null_snd_dev()
    try:
        lib.start()
        #log.info("\nPJSIP library has been started")
    except pjsua.Error as q:
        log.error("Execption occurred" + str(q))
        log.info(q)
        raise Exception

    def Start(self, sip_id, reg_uri, proxy_reg_uri, username, password, sip_id2, reg_uri2, username2, password2):

        try:

            acc_cfg = pjsua.AccountConfig()
            acc_cfg.id = sip_id
            acc_cfg.reg_uri = reg_uri
            acc_cfg.proxy = [str(proxy_reg_uri)]
            acc_cfg.ka_interval = 30
            acc_cfg.use_srtp = 1
            acc_cfg.srtp_secure_signaling = 1
            acc_cfg.auth_cred = [pjsua.AuthCred("*", username, password)]
            acc_cb = MyAccountCallback()
            acc = lib.create_account(acc_cfg, cb=acc_cb)
            acc_cb.wait()
            lib.handle_events(1000)
            log.info("\n")
            while str(acc.info().reg_status) == '200':
                log.info("Registration completed for user 1 status = " + str(
                    acc.info().reg_status) + " ,  " + "(" + acc.info().reg_reason + ")")
                break
            acc_cfg2 = pjsua.AccountConfig()
            acc_cfg2.id = sip_id2
            acc_cfg2.reg_uri = reg_uri2
            acc_cfg2.proxy = [str(proxy_reg_uri)]
            acc_cfg2.ka_interval = 30
            acc_cfg2.use_srtp = 1
            acc_cfg2.srtp_secure_signaling = 1
            acc_cfg2.auth_cred = [pjsua.AuthCred("*", username2, password2)]
            acc_cb2 = AccountCallback()
            acc2 = lib.create_account(acc_cfg2, cb=acc_cb2)
            acc_cb2.wait()
            log.info("\n")
            in_call = True
            while str(acc2.info().reg_status) == '200':
                log.info("Registration complete user 2, status = " + str(acc2.info().reg_status) + " ,  " + "(" + str(
                    acc2.info().reg_reason) + ")")
                break
        except Exception as e:
            log.info(e)
            raise Exception

    def pjsua_stop(self):
        try:
            lib.destroy()
            log.info("pjsip lib is destroyed")
            time.sleep(3)
        except Exception as e:
            raise Exception


# sip_id = 'sip:kiranjbbe5be53@exotest1m.voip.exotel.com'
# reg_uri = "sip:voip.exotel.in:443;transport=tls"
# proxy_reg_uri = ["sip:voip.exotel.in:443;transport=tls;lr"]
# user1 = "kiranjbbe5be53"
# pwd1 = "Trackdfect@123"
#
# sip_id2 = 'sip:vijays4ea15400@exotest1m.voip.exotel.com'
# reg_uri2 = "sip:voip.exotel.in:443;transport=tls"
# user2 = "vijays4ea15400"
# pwd2 = "Trackdfect@123"
#
# PJSIP_Config().Start( sip_id, reg_uri, proxy_reg_uri, user1, pwd1, sip_id2, reg_uri2, user2, pwd2)
# while 1==1:
#     pass
