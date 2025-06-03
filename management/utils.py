from django.core.mail import send_mail
import random
from django.conf import settings

def send_otp_email(email, otp):
    subject = 'Your Registration OTP'
    message = f'Your OTP for registration is: {otp}'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
