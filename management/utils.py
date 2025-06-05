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
    for line in lines:
        if re.match(r"^\d+\s+\w+", line):  # line starts with sr. no and designation
            try:
                entry = {}
                parts = line.strip().split(None, 2)
                entry['sr_no'] = int(parts[0])
                entry['designation'] = parts[1]

                # Re-join remaining text block
                details = parts[2]

                # Extract fields using regex
                name_match = re.search(r'\t{2,}(.*?)\n', details)
                if name_match:
                    entry['name'] = name_match.group(1).strip()
                else:
                    name_line = details.split("\n")[0].strip()
                    entry['name'] = name_line

                entry['father_name'] = re.search(r'\n\s*(.*?)\n', details).group(1).strip()

                entry['new_p_no'] = re.search(r'New P#:\s*(SNSD\d+)', details).group(1)
                entry['old_p_no'] = re.search(r'Old P#:\s*(\d+)', details).group(1)
                entry['wef'] = re.search(r'WEF:\s*([\d/]+)', details).group(1)
                entry['dob'] = re.search(r'DOB:\s*([\d/]+)', details).group(1)

                qualification = re.search(r'\n\s*([A-Za-z0-9.\s]+)\n', details)
                entry['qualification'] = qualification.group(1).strip() if qualification else ""

                occupation = re.findall(r'\n\s*([A-Za-z0-9().\s]+)\n', details)
                if occupation and len(occupation) > 1:
                    entry['occupation'] = occupation[1].strip()
                else:
                    entry['occupation'] = ""

                contact_match = re.search(r'\b\d{10}\b', details)
                entry['contact'] = contact_match.group() if contact_match else ""

                # Address is text just before contact number
                if entry['contact']:
                    address = details.split(entry['contact'])[0].split("\n")[-1].strip()
                    entry['address'] = address
                else:
                    entry['address'] = ""

                data.append(entry)

            except Exception as e:
                continue
    return data