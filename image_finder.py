import numpy as np
import pandas as pd
import cv2
import pyautogui
import pytesseract
import mouse
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


def find_on_screen(word: str) -> (int, int):
    word = word.lower()
    image = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    cv2.imwrite('images/screen.png', image)

    im = Image.open("images/screen.png")
    df = pytesseract.image_to_data(im, output_type='data.frame')
    df['text'] = df['text'].str.lower()
    try:
        return df.loc[df['text'] == word].iloc[0]['left'], df.loc[df['text'] == word].iloc[0]['top']
    except IndexError:
        try:
            return df.loc[df['text'] == word + '...'].iloc[0]['left'], df.loc[df['text'] == word + '...'].iloc[0]['top']
        except IndexError:
            return 0, 0
