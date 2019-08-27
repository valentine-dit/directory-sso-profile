import os
from unittest import mock

import pytest

from django.contrib.auth import get_user_model

from core.tests.helpers import create_response


@pytest.fixture
def user():
    SSOUser = get_user_model()
    return SSOUser(
        id=1,
        pk=1,
        email='jim@example.com',
        session_id='123',
        has_user_profile=False,
    )


@pytest.fixture(autouse=True)
def feature_flags(settings):
    # solves this issue: https://github.com/pytest-dev/pytest-django/issues/601
    settings.FEATURE_FLAGS = {**settings.FEATURE_FLAGS}
    yield settings.FEATURE_FLAGS


@pytest.fixture()
def captcha_stub():
    # https://github.com/praekelt/django-recaptcha#id5
    os.environ['RECAPTCHA_TESTING'] = 'True'
    yield 'PASSED'
    os.environ['RECAPTCHA_TESTING'] = 'False'


@pytest.fixture(autouse=True)
def auth_backend():
    patch = mock.patch(
        'directory_sso_api_client.sso_api_client.user.get_session_user',
        return_value=create_response(404)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture
def client(client, auth_backend, settings):
    def force_login(user):
        client.cookies[settings.SSO_SESSION_COOKIE] = '123'
        if user.has_user_profile:
            user_profile = {
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        else:
            user_profile = {}
        auth_backend.return_value = create_response({
            'id': user.id,
            'email': user.email,
            'hashed_uuid': user.hashed_uuid,
            'user_profile': user_profile
        })
    client.force_login = force_login
    return client


@pytest.fixture(autouse=True)
def mock_create_user_profile():
    response = create_response({
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'job_title': 'Director',
        'mobile_phone_number': '08888888888',
    })
    patch = mock.patch(
        'directory_sso_api_client.sso_api_client.user.create_user_profile',
        return_value=response
    )
    yield patch.start()
    patch.stop()
