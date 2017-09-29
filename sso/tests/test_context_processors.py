from sso import context_processors


def test_sso_user_middleware_plugged_in(settings):
    assert 'sso.middleware.SSOUserMiddleware' in settings.MIDDLEWARE_CLASSES


def test_sso_processor_plugged_in(settings):
    context_processors = settings.TEMPLATES[0]['OPTIONS']['context_processors']
    assert 'sso.context_processors.sso_processor' in context_processors


def test_sso_reset_password_url(request_logged_in, settings):
    context = context_processors.sso_processor(request_logged_in)

    assert context['sso_password_reset_url'] == (
        settings.SSO_PROXY_PASSWORD_RESET_URL
    )
