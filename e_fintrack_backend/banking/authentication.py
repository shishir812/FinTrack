from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from .jwt_utils import decode_token


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode('utf-8')
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed('Invalid authorization header.')
        payload = decode_token(parts[1])
        if not payload:
            raise exceptions.AuthenticationFailed('Invalid or expired token.')
        try:
            user = get_user_model().objects.get(pk=payload['sub'], is_active=True)
        except get_user_model().DoesNotExist as exc:
            raise exceptions.AuthenticationFailed('User not found.') from exc
        return user, None
