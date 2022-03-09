import base64
import logging
from dataclasses import dataclass
import Utilities.logger_utility as log_utils
import requests


@dataclass
class Response:
    status_code: int
    text: str
    as_dict: object
    headers: dict


class APIRequest:
    log = log_utils.custom_logger(logging.INFO)

    def get(self, url):
        response = requests.get(url)
        return response

    def post(self, url):
        logging.info(url)
        response = requests.request("POST",url)

        return response

    def call_to_flow(self, URL, api_key, api_token, From, Url, callerId, statuscallback):
        auth_str = '%s:%s' % (api_key, api_token)
        b64_auth_str = base64.b64encode(auth_str.encode('ascii'))

        headers = {
            'Content_Type': 'application/json',
            'Authorization': 'Basic %s' % b64_auth_str
        }

        parameters = {
            'From': str(From),
            'Url': str(Url),
            'CallerID': str(callerId),
            'StatusCallback': str(statuscallback)
        }
        self.log.info(URL)
        self.log.info(parameters)
        response = requests.post(URL, params=parameters, headers=headers)
        self.log.info(response)
        return response

    def call_details_get_exotel(self, URL,api_key,api_token):
        auth_str = '%s:%s' % (api_key, api_token)
        b64_auth_str = base64.b64encode(auth_str.encode('ascii'))

        headers = {
            'Content_Type': 'application/json',
            'Authorization': 'Basic %s' % b64_auth_str}
        response = requests.get(URL,headers=headers)
        # return self.__get_responses(response)
        return response

    def delete(self, url):
        response = requests.delete(url)
        return self.__get_responses(response)

    def __get_responses(self, response):
        status_code = response.status_code
        text = response.json()

        try:
            as_dict = response.json()
        except Exception:
            as_dict = {}

        headers = response.headers

        return Response(
            status_code, text, as_dict, headers
        )
