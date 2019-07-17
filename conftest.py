from copy import deepcopy
import os
import http
from unittest import mock

import pytest
import requests

from django.contrib.sessions.backends import signed_cookies
from django.contrib.auth import get_user_model

from core.tests.helpers import create_response
from profile.eig_apps.constants import HAS_VISITED_ABOUT_PAGE_SESSION_KEY


@pytest.fixture
def user():
    SSOUser = get_user_model()
    return SSOUser(
        id=1,
        email='jim@example.com',
        session_id='123',
        has_user_profile=False,
    )


@pytest.fixture
def request_logged_in(rf, user):
    request = rf.get('/')
    request.user = user
    return request


@pytest.fixture
def api_response_200():
    return create_response()


@pytest.fixture
def api_response_403():
    return create_response(status_code=403)


@pytest.fixture
def api_response_500():
    return create_response(status_code=500)


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
def mock_session_user(client, settings):
    client.cookies[settings.SSO_SESSION_COOKIE] = '123'
    patch = mock.patch(
        'directory_sso_api_client.client.sso_api_client.user.get_session_user',
        return_value=create_response(404)
    )

    def login():
        started.return_value = create_response(
            200,
            {
                'id': '123',
                'email': 'test@a.com',
                'hashed_uuid': 'abc',
                'has_user_profile': False,
            }
        )
    started = patch.start()
    started.login = login
    yield started
    patch.stop()
