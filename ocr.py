from PIL import Image
import pytesseract
from exceptions import CaptchaIsNotNumberException


def ocr_captcha(image):
    """
    Recognize the characters in image using pytesseract
    :param image: A PIL.Image object
    :return: text str
    """

    # Generate a new image (50x20) as a container to let the original
    # captcha paste on it in order to be recognized by tesseract-ocr
    out = Image.new('RGB', (50, 20), (255,)*3)
    out.paste(image, (5, 5))
    # Convert the image to grey-scale
    out = out.convert('L')
    # Binarization
    threshold = 140
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    out = out.point(table, '1')
    text = pytesseract.image_to_string(out)

    if text.isnumeric() is False:
        raise CaptchaIsNotNumberException(text)
    return text
