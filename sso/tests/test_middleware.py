import http
from unittest.mock import patch, Mock

from directory_api_client.client import api_client
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


def api_response_bad(*args, **kw):
    return Mock(ok=False)


def test_sso_middleware_installed(settings):
    assert 'sso.middleware.SSOUserMiddleware' in settings.MIDDLEWARE_CLASSES


@patch('directory_sso_api_client.client.sso_api_client.user.get_session_user')
def test_sso_middleware_no_cookie(
    mock_get_session_user, settings, client, mock_session_user
):
    del client.cookies[settings.SSO_SESSION_COOKIE]
    mock_session_user.stop()
    settings.MIDDLEWARE_CLASSES = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'sso.middleware.SSOUserMiddleware',
    ]
    response = client.get(reverse('find-a-buyer'))

    assert mock_get_session_user.call_count == 0

    assert response.status_code == http.client.FOUND


@patch.object(api_client.company, 'retrieve_private_profile')
@patch('directory_sso_api_client.client.sso_api_client.user.get_session_user')
def test_sso_middleware_api_response_ok(
    mock_get_session_user, mock_retrieve_supplier_company, settings,
    returned_client, rf
):
    mock_retrieve_supplier_company.return_value = api_response_ok()
    mock_get_session_user.return_value = api_response_ok()

    request = rf.get(reverse('find-a-buyer'))
    request.COOKIES[settings.SSO_SESSION_COOKIE] = '123'

    middleware.SSOUserMiddleware().process_request(request)

    mock_get_session_user.assert_called_with('123')
    assert request.sso_user.id == 1
    assert request.sso_user.email == 'jim@example.com'


@patch(
    'directory_sso_api_client.client.sso_api_client.user.get_session_user',
    api_response_bad
)
def test_sso_middleware_bad_response(settings, returned_client):
    settings.MIDDLEWARE_CLASSES = ['sso.middleware.SSOUserMiddleware']
    response = returned_client.get(reverse('find-a-buyer'))

    assert response.status_code == http.client.FOUND


@patch('directory_sso_api_client.client.sso_api_client.user.get_session_user')
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
        returned_client.get(reverse('find-a-buyer'))


@pytest.mark.parametrize(
    'excpetion_class', requests.exceptions.RequestException.__subclasses__()
)
@patch('directory_sso_api_client.client.sso_api_client.user.get_session_user')
def test_sso_middleware_timeout(
    mock_get_session_user, settings, returned_client, caplog, excpetion_class
):
    mock_get_session_user.side_effect = excpetion_class()
    returned_client.cookies[settings.SSO_SESSION_COOKIE] = '123'
    settings.MIDDLEWARE_CLASSES = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'sso.middleware.SSOUserMiddleware'
    ]

    response = returned_client.get(reverse('about'))

    assert response.status_code == 200

    log = caplog.records[0]
    assert log.levelname == 'ERROR'
    assert log.msg == middleware.SSOUserMiddleware.MESSAGE_SSO_UNREACHABLE
