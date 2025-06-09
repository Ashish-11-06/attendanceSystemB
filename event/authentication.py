from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from management.models import Admin, Register, Unit

class MultiUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_type = validated_token.get('user_type')
            user_id = validated_token['user_id']
        except KeyError:
            raise AuthenticationFailed('Token contained no recognizable user identification')

        if user_type == 'admin':
            try:
                return Admin.objects.get(pk=user_id)
            except Admin.DoesNotExist:
                raise AuthenticationFailed('Admin user not found')

        elif user_type == 'unit':
            # Try Register model first
            try:
                return Register.objects.get(pk=user_id)
            except Register.DoesNotExist:
                # Try Unit model next
                try:
                    return Unit.objects.get(pk=user_id)
                except Unit.DoesNotExist:
                    raise AuthenticationFailed('Unit user not found')

        else:
            raise AuthenticationFailed('Invalid user type in token')

