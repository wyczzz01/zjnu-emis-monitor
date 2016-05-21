from io import BytesIO
import random

from blitzdb import Document, FileBackend
from lxml import etree
from PIL import Image
import requests

from exceptions import CaptchaIsNotNumberException
import ocr
from smsutils import BmobSmsUtils



# EMIS_URL
URL_LOGIN = 'http://10.1.68.13:8001/login.asp'
URL_LOGOUT = 'http://10.1.68.13:8001/loginOut.asp'
URL_CODE = 'http://10.1.74.13/checkcode.asp'
URL_TOTALSCORE = 'http://10.1.68.13:8001/studentWeb/ViewScore/ViewTotalScore.asp'

# Session status code
STATUS_ERR_PARAM = -2
STATUS_ERR_UNKNOWN = -1
STATUS_SUCCESS = 0  # Login success
STATUS_ERR_USERNAME = 1  # Username invalid
STATUS_ERR_PASSWORD = 2  # Password invalid
STATUS_ERR_CODE = 4  # Captcha invalid & other // TODO
STATUS_ERR_EMIS = 4  # EMIS error

# Messages
MSG_ERR_PARAM = '参数错误'
MSG_ERR_UNKNOWN = '未知错误'
MSG_SUCCESS = '登录成功！'  # Login success
MSG_ERR_USERNAME = '账号不存在哦，请检查账号是否输入正确。'  # Username invalid
MSG_ERR_PASSWORD = '你的密码输错了呢，请检查。'  # Password invalid
# MSG_ERR_CODE = '教务系统已关闭，本学期将不再会有数据更新，请在下学期开学前后再访问'  # EMIS closed
MSG_ERR_CODE = '教务系统无法访问了，可能正在维护'  # EMIS closed
MSG_ERR_EMIS = '教务系统的访问量太高，过会儿再访问吧！'  # EMIS error
MSG_BMOB_BIND_TIMES_COUNT = '绑定成功！你还能绑定{}个教务账号。'


# Headers
def gen_random_header():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
        'X-Real-IP': '10.11.12.' + str(random.randint(1, 253)),
        'X-Forwarded-For': '222.223.233.' + str(random.randint(1, 253)),
    }


class Score(Document):
    pass


class Session(requests.Session):

    def __init__(self, username='', password='', usertype='student'):
        super().__init__()
        self.username = username
        self.password = password
        self.usertype = usertype
        # Result code represents session status
        self.result_code = 0

    def login(self):
        global result, request_times
        # Try to do 10 times to do captcha
        request_times = 0
        while self.result_code != 200 and request_times < 10:
            request_times += 1

            # Fetch captcha
            codeimg = self.get(URL_CODE, headers=gen_random_header())
            imgbytes = codeimg.content
            # Recognize the captcha
            try:
                image = Image.open(BytesIO(imgbytes))
                code = ocr.ocr_captcha(image)
            except IOError as e:
                continue
            except CaptchaIsNotNumberException as ce:
                print(ce)
                continue

            # Post data
            data = {
                'radioUserType': self.usertype,
                'userId': self.username,
                'pwd': self.password,
                'GetCode': code,
            }

            # Perform login
            print('Perform login as username: ' + self.username + ', password: ' + self.password)
            result = self.post(URL_LOGIN, data=data, headers=gen_random_header())
            self.result_code = result.status_code

        status, message = self.check_status(result.content.decode('gbk'))
        return status, message

    def check_status(self, content):
        if self.result_code == 200:
            if content.find('当前用户账号不存在') != -1:
                return STATUS_ERR_USERNAME, MSG_ERR_USERNAME
            elif content.find('当前用户密码错误') != -1:
                return STATUS_ERR_PASSWORD, MSG_ERR_PASSWORD
            elif content.find('验证码输入错误') != -1 or \
                 content.find('浙江师范大学教务管理系统EMIS') == -1:
                # Captcha error or other situations that indicate login error
                return STATUS_ERR_CODE, MSG_ERR_CODE
            else:
                # Login success!
                return STATUS_SUCCESS, MSG_SUCCESS
        print('EMIS banned!')
        return STATUS_ERR_EMIS, MSG_ERR_EMIS

    def logout(self,):
        self.get(URL_LOGOUT, headers=gen_random_header())
        self.close()
        print('Success, logged out!')


if __name__ == '__main__':

    username = '13211137'
    password = '940903'
    s = Session(username, password)
    status, message = s.login()
    if status == STATUS_SUCCESS:
        html = s.get(URL_TOTALSCORE)
        if html.content is not None:
            backend = FileBackend("./emis.db")

            selector = etree.HTML(html.content.decode('gbk'))
            current_credit = int(selector.xpath(r'//*[@color="#FF0000"]/text()')[0])
            credit = Score({'credit': current_credit})

            try:
                saved_credit = backend.get(Score, {'credit': current_credit})

                if current_credit != '' and current_credit != int(saved_credit.credit):
                    credit.save(backend)
                    backend.commit()
                    BmobSmsUtils().send_sms_template(['18395960722'], 'new_score')
                    print('Credit changed, SMS sent!')
                else:
                    print('Credit not changed: ' + str(current_credit))
            except Score.DoesNotExist:
                credit.save(backend)
                backend.commit()
                print('New score created!')
            s.logout()
