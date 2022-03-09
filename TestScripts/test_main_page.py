import logging
import sys
import pytest
import Utilities.logger_utility as log_utils
from Source.Pages.IVR_applet import IVR_applet
from Source.Pages.Passthru_applet import Passthru_Applet
from Utilities.config_utility import ConfigUtility
from Utilities.data_reader_utility import DataReader
from Source.pjsua_config.registration import PJSIP_Config

data_reader = DataReader()
log = log_utils.custom_logger(logging.INFO)


# @allure.story('[DEMO] - Automate  the  basic functionality')
# @allure.feature('Web App Input Tests')
@pytest.mark.usefixtures("initialize")
class TestMainPage:
    config = ConfigUtility()
    report_filename = data_reader.create_xlsx()
    log.info(report_filename)

    @pytest.fixture(scope='function')
    def initialize(self):
        self.passthru = Passthru_Applet()
        self.ivr = IVR_applet()
        self.prop = self.config.load_properties_file()


    @pytest.fixture(autouse=True)
    def class_level_setup(self, request):
        test_name = request.function.__name__
        if data_reader.get_data(test_name, "Run_mode") != "Y":
            pytest.skip("Excluded from current execution run.")

    @pytest.mark.passthru
    def test_sip_start(self):
        log.info("###### TEST EXECUTION STARTED :: setup class  ######")

        sip_id = self.prop.get('SIP_Account', 'sip_id1')
        reg_uri = self.prop.get('SIP_Account', 'reg_uri')
        proxy_reg_uri = self.prop.get('SIP_Account', 'proxy_reg_uri')
        user1 = self.prop.get('SIP_Account', 'user1')
        pwd1 = self.prop.get('SIP_Account', 'password1')

        sip_id2 = self.prop.get('SIP_Account', 'sip_id2')
        reg_uri2 = self.prop.get('SIP_Account', 'reg_uri')
        user2 = self.prop.get('SIP_Account', 'user2')
        pwd2 = self.prop.get('SIP_Account', 'password2')
        PJSIP_Config().Start(sip_id, reg_uri, proxy_reg_uri, user1, pwd1, sip_id2, reg_uri2, user2, pwd2)

    # @allure.testcase(" valid passthru URL(200 Response)")
    @pytest.mark.passthru
    def test_EXTC_PASS_001(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_001(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_002(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_002(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_003(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_003(test_name,self.report_filename )

    @pytest.mark.passthru
    def test_EXTC_PASS_004(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_004(test_name,self.report_filename )

    @pytest.mark.passthru
    def test_EXTC_PASS_005(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_005(test_name,self.report_filename )

    @pytest.mark.passthru
    def test_EXTC_PASS_006(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_006(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_007(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_007(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_008(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_008(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_009(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STA"
                 "RTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_009(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_010(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_010(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_011(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_011(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_012(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_012(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_013(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_013(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_014(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_014(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_015(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_015(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_016(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_016(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_017(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_017(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_018(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_018(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_019(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_019(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_020(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_020(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_021(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_021(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_022(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_022(test_name,self.report_filename)

    @pytest.mark.passthru
    def test_EXTC_PASS_023(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.passthru.verify_EXTC_PASS_023(test_name,self.report_filename)

    def test_EXTC_IVR_001(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_001(test_name,self.report_filename)

    def test_EXTC_IVR_002(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_002(test_name,self.report_filename)

    def test_EXTC_IVR_003(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_003(test_name,self.report_filename)

    def test_EXTC_IVR_004(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_004(test_name,self.report_filename)


    def test_EXTC_IVR_005(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_005(test_name,self.report_filename)

    def test_EXTC_IVR_006(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_006(test_name,self.report_filename)



    def test_EXTC_IVR_007(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_007(test_name,self.report_filename)

    def test_EXTC_IVR_008(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_008(test_name,self.report_filename)

    def test_EXTC_IVR_009(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_009(test_name,self.report_filename)

    def test_EXTC_IVR_010(self):
        test_name = sys._getframe().f_code.co_name
        log.info("###### TEST EXECUTION STARTED :: " + test_name + " ######")
        self.ivr.verify_EXTC_IVR_010(test_name,self.report_filename)


    def test_sip_stop(self):
        log.info("###### TEST EXECUTION STARTED :: tear down   ######")
        PJSIP_Config().pjsua_stop()
