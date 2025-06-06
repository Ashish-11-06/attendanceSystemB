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


# def parse_ocr_lines_to_table(lines):
#     data = []
#     for line in lines:
#         # Try to find lines starting with a unit number (e.g., 358-Jai Jawan Nagar)
#         match = re.match(r'^(\d{3,5}[\-\s]?[A-Za-z ]+)', line)
#         if match:
#             parts = re.split(r'\s+', line.strip())
            
#             # Example: ['358-Jai', 'Jawan', 'Nagar', '0', '0', '0', ...]
#             # Find first number index
#             num_index = next((i for i, v in enumerate(parts) if v.isdigit()), -1)
#             if num_index == -1 or len(parts[num_index:]) < 7:
#                 continue  # skip broken rows

#             unit_name = ' '.join(parts[:num_index])
#             try:
#                 data.append({
#                     "unit": unit_name,
#                     "reg_gents": int(parts[num_index]),
#                     "reg_ladies": int(parts[num_index+1]),
#                     "reg_total": int(parts[num_index+2]),
#                     "unreg_gents": int(parts[num_index+3]),
#                     "unreg_ladies": int(parts[num_index+4]),
#                     "unreg_total": int(parts[num_index+5]),
#                     "satsang_strength": int(parts[num_index+6]),
#                     "grand_total": int(parts[num_index+7]),
#                 })
#             except (IndexError, ValueError):
#                 continue
#     return data



def parse_sewadal_adhikari_data(lines):
    data = []
    current_entry = {}

    for line in lines:
        # Entry starts with Sr. No.
        match = re.match(r"^(\d+)\s+([A-Za-z]+)\s+(.*)", line)
        if match:
            # Save previous entry if any
            if current_entry:
                data.append(current_entry)
                current_entry = {}

            current_entry["sr_no"] = int(match.group(1))
            current_entry["designation"] = match.group(2).strip()
            current_entry["name"] = match.group(3).strip()

        elif "New P#:" in line:
            current_entry["new_p_no"] = re.search(r'New P#:\s*(\S+)', line).group(1)

        elif "Old P#:" in line:
            current_entry["old_p_no"] = re.search(r'Old P#:\s*(\S+)', line).group(1)

        elif "WEF:" in line:
            current_entry["wef"] = re.search(r'WEF:\s*(\S+)', line).group(1)

        elif "DOB:" in line:
            current_entry["dob"] = re.search(r'DOB:\s*(\S+)', line).group(1)

        elif re.match(r'^[A-Za-z. ]+$', line.strip()):
            # Likely qualification or occupation
            if "qualification" not in current_entry:
                current_entry["qualification"] = line.strip()
            elif "occupation" not in current_entry:
                current_entry["occupation"] = line.strip()

        elif re.search(r'\d{10}', line):
            # Line with address and 10-digit mobile
            contact_match = re.search(r'(\d{10})', line)
            current_entry["contact"] = contact_match.group(1)
            current_entry["address"] = line.replace(contact_match.group(1), '').strip()

        elif current_entry and "father_name" not in current_entry:
            current_entry["father_name"] = line.strip()

    if current_entry:
        data.append(current_entry)

    return data
