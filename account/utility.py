import phonenumbers
from django.core.mail import send_mail
from twilio.rest import Client
from account import serializers
from instaworld.settings import twilio_phone_number, account_sid, auth_token


def send_otp(self, email, otp):
    subject = 'Your OTP'
    message = f'Your OTP is: {otp}'
    from_email = 'mohd.asad@kiwitech.com'
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list,
              auth_user="mohd.asad@kiwitech.com", auth_password="3339khanasad")


def validate_phone_number(self, phone_number):
    if not phone_number:
        raise serializers.ValidationError('Phone number is required')
    if not phonenumbers.is_valid_number(phonenumbers.parse(phone_number)):
        raise serializers.ValidationError('Invalid phone number')
    return phone_number


def send_otp_on_phone(self, phone_number, otp):
    client = Client(account_sid, auth_token)

    message = f'Your OTP is: {otp}'
    verification = client.messages.create(from_=twilio_phone_number, to=phone_number, body=message)
    print(verification.status)

