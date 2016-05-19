import json
import requests
import grequests
from datetime import datetime

URL_CC_TOKEN = 'https://oauth.api.189.cn/emp/oauth2/v3/access_token'
URL_SEND_MESSAGE = 'http://api.189.cn/v2/emp/templateSms/sendSms'
APP_ID = '726195780000251941'
APP_SECRET = 'e1fc0f5cfba335ea8b8d5f8d698cf218'


class SmsUtils:

    def __init__(self, app_id=APP_ID, app_secret=APP_SECRET):
        self.access_token = self.get_access_token(app_id, app_secret)

    def get_access_token(self, app_id, app_secret):
        data = {
            'grant_type': 'client_credentials',
            'app_id': app_id,
            'app_secret': app_secret,
        }
        res = requests.post(URL_CC_TOKEN, data=data)
        if res.content is not None:
            content = json.loads(res.content.decode())
            return content["access_token"]

    def send(self, receivers, content=''):
        rs = set()
        for each in receivers:
            data = {
                'app_id': APP_ID,
                'access_token': self.access_token,
                'acceptor_tel': each,
                'template_id': '91550991',
                'template_param': '{}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            rs.add(grequests.post(URL_SEND_MESSAGE, data=data))
        grequests.map(rs)

