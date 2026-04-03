from django.contrib.auth import get_user_model


class EmailOrUsernameBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        login_value = username or kwargs.get("email")
        if not login_value or password is None:
            return None

        try:
            user = User.objects.get(email__iexact=login_value)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username__iexact=login_value)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def user_can_authenticate(self, user):
        return getattr(user, "is_active", True)
