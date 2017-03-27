from unittest.mock import patch

import pytest

from sso.utils import SSOUser


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
