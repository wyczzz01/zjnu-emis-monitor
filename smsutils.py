from abc import abstractmethod, ABCMeta
import json
import requests
import grequests
from datetime import datetime


class BaseSmsUtils:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.get_credentials()

    @abstractmethod
    def send(self, receivers, content): pass

    @abstractmethod
    def get_credentials(self): pass


class Open189SmsUtils(BaseSmsUtils):

    def __init__(self):
        super().__init__()
        self.url_cc_token = 'https://oauth.api.189.cn/emp/oauth2/v3/access_token'
        self.url_send_message = 'http://api.189.cn/v2/emp/templateSms/sendSms'
        self.app_id = '726195780000251941'
        self.app_secret = 'e1fc0f5cfba335ea8b8d5f8d698cf218'

    def get_credentials(self):
        data = {
            'grant_type': 'client_credentials',
            'app_id': self.app_id,
            'app_secret': self.app_secret,
        }
        res = requests.post(self.url_cc_token, data=data)
        if res.content is not None:
            content = json.loads(res.content.decode())
            self.access_token = content["access_token"]

    def send(self, receivers, content=''):
        rs = set()
        for each in receivers:
            data = {
                'app_id': self.app_id,
                'access_token': self.access_token,
                'acceptor_tel': each,
                'template_id': '91550991',
                'template_param': '{}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            rs.add(grequests.post(self.url_send_message, data=data))
        grequests.map(rs)


class BmobSmsUtils(BaseSmsUtils):

    def __init__(self):
        super().__init__()
        self.url = 'https://api.bmob.cn/1/requestSmsCode'
        self.bmob_app_id = '2b3840dbaea06dca9e822699a20b22be'
        self.bmob_rest_api_key = '31165eb3c129fffd72c021a7c2f9c2f6'

    def send_sms(self, receivers, content):
        pass

    def send_sms_template(self, receivers, template_name):
        rs = set()
        headers = {
            'X-Bmob-Application-Id': self.bmob_app_id,
            'X-Bmob-REST-API-Key': self.bmob_rest_api_key,
            'Content-Type': 'application/json',
        }
        for each in receivers:
            data = {
                'mobilePhoneNumber': each,
                'template': template_name,
            }
            rs.add(grequests.post(data=data, headers=headers))
        grequests.map(rs)

    def get_credentials(self):
        pass


if __name__ == '__main__':
    BmobSmsUtils().send_sms_template(['18395960722'], 'new_score')
