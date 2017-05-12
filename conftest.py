from copy import deepcopy
import http
from unittest.mock import patch

import pytest
import requests

from django.utils.module_loading import import_string
from rest_framework.test import APIClient

from sso.utils import SSOUser
from profile.eig_apps.constants import HAS_VISITED_ABOUT_PAGE_SESSION_KEY


@pytest.fixture
def sso_user():
    return SSOUser(
        id=1,
        email='jim@example.com',
    )


@pytest.fixture
def request_logged_in(rf, sso_user):
    request = rf.get('/')
    request.sso_user = sso_user
    return request


@pytest.fixture
def request_logged_out(rf):
    request = rf.get('/')
    request.sso_user = None
    return request


@pytest.fixture
def api_response_200():
    response = requests.Response()
    response.status_code = http.client.OK
    response.json = lambda: deepcopy({})
    return response


@pytest.fixture
def api_response_403():
    response = requests.Response()
    response.status_code = http.client.FORBIDDEN
    return response


@pytest.fixture
def api_response_404():
    response = requests.Response()
    response.status_code = http.client.NOT_FOUND
    return response


@pytest.fixture
def api_response_500():
    response = requests.Response()
    response.status_code = http.client.INTERNAL_SERVER_ERROR
    return response


@pytest.fixture
def sso_user_middleware(sso_user):
    def process_request(self, request):
        request.sso_user = sso_user

    stub = patch(
        'sso.middleware.SSOUserMiddleware.process_request',
        process_request
    )
    stub.start()
    yield
    stub.stop()


@pytest.fixture
def sso_user_middleware_unauthenticated():
    def process_request(self, request):
        request.sso_user = None

    stub = patch(
        'sso.middleware.SSOUserMiddleware.process_request',
        process_request
    )
    stub.start()
    yield
    stub.stop()


@pytest.fixture
def returned_client(client, settings):
    """Client that has visited the about page already"""

    session = import_string(settings.SESSION_ENGINE).SessionStore()
    session.save()
    session[HAS_VISITED_ABOUT_PAGE_SESSION_KEY] = 'true'
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client


@pytest.fixture
def api_client():
    """DRF APIClient instance."""
    return APIClient()
