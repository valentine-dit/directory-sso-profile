import http
from unittest.mock import patch, Mock

import pytest
import requests

from django.core.urlresolvers import reverse

from sso import middleware


def api_response_ok(*args, **kwargs):
    return Mock(
        ok=True,
        json=lambda: {
            'id': 1,
            'email': 'jim@example.com',
        }
    )


def api_response_ok_bad_json(*args, **kwargs):
    response = requests.models.Response()
    response.status_code = 200
    response._content = b'<html></html>'
    return response


def api_response_bad():
    return Mock(ok=False)


def test_sso_middleware_installed(settings):
    assert 'sso.middleware.SSOUserMiddleware' in settings.MIDDLEWARE_CLASSES


@patch('sso.utils.sso_api_client.user.get_session_user')
def test_sso_middleware_no_cookie(
    mock_get_session_user, settings, client
):
    settings.MIDDLEWARE_CLASSES = ['sso.middleware.SSOUserMiddleware']
    response = client.get(reverse('find-a-buyer'))

    mock_get_session_user.assert_not_called()

    assert response.status_code == http.client.FOUND


@patch('sso.utils.sso_api_client.user.get_session_user')
def test_sso_middleware_api_response_ok(
    mock_get_session_user, settings, returned_client
):
    mock_get_session_user.return_value = api_response_ok()
    returned_client.cookies[settings.SSO_SESSION_COOKIE] = '123'
    settings.MIDDLEWARE_CLASSES = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'sso.middleware.SSOUserMiddleware'
    ]
    response = returned_client.get(reverse('find-a-buyer'))

    mock_get_session_user.assert_called_with('123')
    assert response._request.sso_user.id == 1
    assert response._request.sso_user.email == 'jim@example.com'


@patch('sso.utils.sso_api_client.user.get_session_user', api_response_bad)
def test_sso_middleware_bad_response(settings, returned_client):
    settings.MIDDLEWARE_CLASSES = ['sso.middleware.SSOUserMiddleware']
    response = returned_client.get(reverse('find-a-buyer'))

    assert response.status_code == http.client.FOUND


@patch('sso.utils.sso_api_client.user.get_session_user')
def test_sso_middleware_bad_good_response(
    mock_get_session_user, settings, returned_client
):
    mock_get_session_user.return_value = api_response_ok_bad_json()
    returned_client.cookies[settings.SSO_SESSION_COOKIE] = '123'
    settings.MIDDLEWARE_CLASSES = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'sso.middleware.SSOUserMiddleware'
    ]

    message = middleware.SSOUserMiddleware.MESSAGE_INVALID_JSON

    with pytest.raises(ValueError, message=message):
        response = returned_client.get(reverse('find-a-buyer'))
