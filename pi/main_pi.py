import cv2
import requests
import time
from RPLCD.i2c import CharLCD
from PIL import Image
import base64
import numpy as np

# --- CONFIG ---
LCD_ADDR = 0x27
FLASK_API = 'http://127.0.0.1:5000/api/attendance'  # <-- Also remove the double slash!
ADMIN_PHONE = '+639272623413'

# --- INIT ---
lcd = CharLCD('PCF8574', LCD_ADDR)

def send_lcd(msg, line=0):
    lcd.clear()
    lcd.cursor_pos = (line, 0)
    lcd.write_string(msg[:16])

def send_sms(phone, message):
    # (stub) Send SMS via GSM, if connected by serial
    pass

def capture_face():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        send_lcd("No Camera Found")
        time.sleep(2)
        return None
    ret, frame = cap.read()
    cap.release()
    if ret:
        # Convert frame to base64 JPEG
        buf = np.array(cv2.imencode('.jpg', frame)[1]).tobytes()
        img_base64 = base64.b64encode(buf).decode()
        return f"data:image/jpeg;base64,{img_base64}"
    else:
        send_lcd("No Face Detected")
        return None

def read_rfid():
    send_lcd("Scan RFID...")
    print("Scan RFID card:")
    tag = input().strip()
    send_lcd(f"RFID: {tag}")
    time.sleep(1)
    return tag

def record_attendance(rfid, face_image):
    send_lcd("Sending Data...")
    payload = {
        "rfid_tag": rfid,
        "face_image": face_image
    }
    try:
        resp = requests.post(FLASK_API, json=payload, timeout=10)
        if resp.status_code == 200 and resp.json().get('success'):
            send_lcd("Attendance OK", 0)
            send_sms(ADMIN_PHONE, f"Student {rfid} present!")
        else:
            send_lcd("Attendance Fail", 0)
    except Exception as e:
        send_lcd("API Error")
        print("API Error:", e)

def main_loop():
    while True:
        rfid = read_rfid()
        send_lcd("Capture Face...", 0)
        face_image = capture_face()
        if face_image:
            record_attendance(rfid, face_image)
        else:
            send_lcd("No Face", 0)
        time.sleep(3)
        send_lcd("Ready.", 0)
        

if __name__ == "__main__":
    send_lcd("System Ready")
    time.sleep(1)
    try:
        main_loop()
    except KeyboardInterrupt:
        lcd.clear()
        print("Exiting...")
