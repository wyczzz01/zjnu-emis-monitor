class CaptchaIsNotNumberException(Exception):
    default_detail = 'Captcha is not recognized as a number, retry'

    def __init__(self, code=None):
        if code is not None:
            self.detail = self.default_detail + ": " + code
        else:
            self.detail = self.default_detail

    def __str__(self):
        return self.detail
