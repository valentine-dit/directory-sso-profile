from django.conf import settings


def sso_processor(request):
    return {
        'sso_password_reset_url': settings.SSO_PASSWORD_RESET_URL,
    }
