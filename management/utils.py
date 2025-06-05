import re
from django.core.mail import send_mail
import random
import pytesseract                     #pip install pytesseract opencv-python pillow
import cv2
from django.conf import settings

def send_otp_email(email, otp):
    subject = 'Your Registration OTP'
    message = f'Your OTP for registration is: {otp}'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    
    
def extract_table_data_from_image(image_path):
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold to get binary image
    thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # OCR config: assume uniform block of text
    custom_config = r'--oem 3 --psm 6'

    # Run OCR
    text = pytesseract.image_to_string(thresh, config=custom_config)

    return text


def parse_ocr_lines_to_table(lines):
    data = []
    for line in lines:
        # Try to find lines starting with a unit number (e.g., 358-Jai Jawan Nagar)
        match = re.match(r'^(\d{3,5}[\-\s]?[A-Za-z ]+)', line)
        if match:
            parts = re.split(r'\s+', line.strip())
            
            # Example: ['358-Jai', 'Jawan', 'Nagar', '0', '0', '0', ...]
            # Find first number index
            num_index = next((i for i, v in enumerate(parts) if v.isdigit()), -1)
            if num_index == -1 or len(parts[num_index:]) < 7:
                continue  # skip broken rows

            unit_name = ' '.join(parts[:num_index])
            try:
                data.append({
                    "unit": unit_name,
                    "reg_gents": int(parts[num_index]),
                    "reg_ladies": int(parts[num_index+1]),
                    "reg_total": int(parts[num_index+2]),
                    "unreg_gents": int(parts[num_index+3]),
                    "unreg_ladies": int(parts[num_index+4]),
                    "unreg_total": int(parts[num_index+5]),
                    "satsang_strength": int(parts[num_index+6]),
                    "grand_total": int(parts[num_index+7]),
                })
            except (IndexError, ValueError):
                continue
    return data