import base64
import hashlib
import hmac
import json
import time

from django.conf import settings


def _b64encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def _b64decode(value):
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode('ascii'))


TOKEN_EXPIRES_IN_SECONDS = 60 * 60 * 24 * 30


def create_token(user, expires_in=TOKEN_EXPIRES_IN_SECONDS):
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {
        'sub': user.id,
        'username': user.username,
        'is_staff': user.is_staff,
        'exp': int(time.time()) + expires_in,
    }
    signing_input = f'{_b64encode(json.dumps(header).encode())}.{_b64encode(json.dumps(payload).encode())}'
    signature = hmac.new(settings.SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f'{signing_input}.{_b64encode(signature)}'


def decode_token(token):
    try:
        header, payload, signature = token.split('.')
        signing_input = f'{header}.{payload}'
        expected = hmac.new(settings.SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64decode(signature), expected):
            return None
        data = json.loads(_b64decode(payload))
        if data.get('exp', 0) < int(time.time()):
            return None
        return data
    except (ValueError, json.JSONDecodeError, TypeError):
        return None
