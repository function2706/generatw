import time
import pyperclip

last_text = ""
while True:
    text = pyperclip.paste()
    if text != last_text:
        print("Clipboard updated:", text)
        # ここでJSON化やファイル保存も可能
        last_text = text
    time.sleep(0.5)
