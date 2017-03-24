from unittest.mock import patch

import pytest

from sso.utils import SSOUser


@pytest.fixture
def sso_user_middleware():
    def process_request(self, request):
        request.sso_user = SSOUser(
            id=1,
            email='jim@example.com',
        )

    stub = patch(
        'sso.middleware.SSOUserMiddleware.process_request',
        process_request
    )
    stub.start()
    yield
    stub.stop()
