from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from management.models import Admin, Register, Unit

class MultiUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_type = validated_token.get('user_type')
            user_id = validated_token['user_id']
        except KeyError:
            raise AuthenticationFailed('Token missing user_id or user_type')

        user = None

        if user_type == 'admin':
            try:
                user = Admin.objects.get(pk=user_id)
            except Admin.DoesNotExist:
                raise AuthenticationFailed('Admin user not found')

        elif user_type == 'unit':
            try:
                user = Register.objects.get(pk=user_id)
            except Register.DoesNotExist:
                try:
                    user = Unit.objects.get(pk=user_id)
                except Unit.DoesNotExist:
                    raise AuthenticationFailed('Unit user not found')

        if user is not None:
            # Inject is_authenticated property if not built-in
            if not hasattr(user, 'is_authenticated'):
                setattr(user, 'is_authenticated', True)
            return user

        raise AuthenticationFailed('User not found')
