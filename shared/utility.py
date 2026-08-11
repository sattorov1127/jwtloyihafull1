import re
from rest_framework import status
from rest_framework.exceptions import ValidationError

phone_regex=re.compile(r'^\+?\d{9,15}$')
email_regex=re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


username_regex=re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_]{3,20}$"
)


def check_email_or_phone(user_input):
    if re.fullmatch(phone_regex,user_input):
        return 'phone'
    elif re.fullmatch(email_regex,user_input):
        return 'email'
    else:
        response={
            'status':status.HTTP_400_BAD_REQUEST,
            'message':'Email yoki Telefon nomeringiz notogri kiritilgan'
        }
        raise ValidationError(response)



def check_email_or_phone_or_username(user_input):
    if re.fullmatch(phone_regex,user_input):
        return 'phone'
    elif re.fullmatch(email_regex,user_input):
        return 'email'
    elif re.fullmatch(username_regex,user_input):
        return 'username'
    else:
        response={
            'status':status.HTTP_400_BAD_REQUEST,
            'message':'Login  notogri kiritilgan'
        }
        raise ValidationError(response)
