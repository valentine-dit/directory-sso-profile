from unittest import mock

import pytest
from requests.cookies import RequestsCookieJar
from requests.exceptions import HTTPError

from enrolment import helpers
from core.tests.helpers import create_response


@mock.patch.object(helpers.ch_search_api_client.company, 'get_company_profile')
def test_get_company_profile_ok_saves_to_session(mock_get_company_profile):
    session = {}
    data = {
        'company_number': '12345678',
        'company_name': 'Example corp',
        'sic_codes': ['1234'],
        'date_of_creation': '2001-01-20',
        'registered_office_address': {'one': '555', 'two': 'fake street'},
    }

    mock_get_company_profile.return_value = create_response(200, data)
    helpers.get_company_profile('123456', session)

    assert session['COMPANY_PROFILE-123456'] == data


@mock.patch.object(helpers.ch_search_api_client.company, 'get_company_profile')
def test_get_company_profile_ok(mock_get_company_profile):
    session = {}
    data = {
        'company_number': '12345678',
        'company_name': 'Example corp',
        'sic_codes': ['1234'],
        'date_of_creation': '2001-01-20',
        'registered_office_address': {'one': '555', 'two': 'fake street'},
    }

    mock_get_company_profile.return_value = create_response(200, data)
    result = helpers.get_company_profile('123456', session)

    assert mock_get_company_profile.call_count == 1
    assert mock_get_company_profile.call_args == mock.call('123456')
    assert result == data
    assert session['COMPANY_PROFILE-123456'] == data


@mock.patch.object(helpers.ch_search_api_client.company, 'get_company_profile')
def test_get_company_profile_not_ok(mock_get_company_profile):
    mock_get_company_profile.return_value = create_response(400)
    with pytest.raises(HTTPError):
        helpers.get_company_profile('123456', {})


@mock.patch.object(helpers.sso_api_client.user, 'create_user')
def test_create_user(mock_create_user):

    data = {
        'email': 'test@test1234.com',
        'verification_code': '12345',
        'cookies': RequestsCookieJar(),
    }
    mock_create_user.return_value = response = create_response(200, data)
    result = helpers.create_user(
        email='test@test1234.com',
        password='1234',
        cookies=response.cookies
    )
    assert mock_create_user.call_count == 1
    assert mock_create_user.call_args == mock.call('test@test1234.com', '1234')
    assert result == data


@mock.patch(
    'directory_forms_api_client.client.forms_api_client.submit_generic'
)
def test_send_verification_code_email(mock_submit):
    email = 'gurdeep.atwal@digital.trade.gov.uk'
    verification_code = '12345'
    from_url = 'test'

    mock_submit.return_value = create_response(201)
    helpers.send_verification_code_email(
        email=email,
        verification_code=verification_code,
        from_url=from_url,
    )

    expected = {'data': {'code': '12345', 'expiry_days': 3},
                'meta': {'action_name': 'gov-notify',
                         'form_url': from_url,
                         'sender': {},
                         'spam_control': {},
                         'template_id': 'aa4bb8dc-0e54-43d1-bcc7-a8b29d2ecba6',
                         'email_address': email
                         }
                }
    assert mock_submit.call_count == 1
    assert mock_submit.call_args == mock.call(expected)


@mock.patch.object(helpers.sso_api_client.user, 'verify_verification_code')
def test_confirm_verification_code(mock_confirm_code):
    result = helpers.confirm_verification_code(
        sso_session_id='12345',
        verification_code='1234'
    )

    assert mock_confirm_code.call_count == 1
    assert mock_confirm_code.call_args == mock.call(
        sso_session_id='12345', code='1234'
    )
