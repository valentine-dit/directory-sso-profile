from unittest import mock

import pytest
from requests.exceptions import HTTPError

from enrolment import helpers
from core.tests.helpers import create_response


@mock.patch.object(helpers.ch_search_api_client.company, 'get_company_profile')
def test_get_company_profile_ok(mock_get_company_profile):
    data = {
        'company_number': '12345678',
        'company_name': 'Example corp',
        'sic_codes': ['1234'],
        'date_of_creation': '2001-01-20',
        'registered_office_address': {'one': '555', 'two': 'fake street'},
    }

    mock_get_company_profile.return_value = create_response(200, data)
    result = helpers.get_company_profile('123456')

    assert mock_get_company_profile.call_count == 1
    assert mock_get_company_profile.call_args == mock.call('123456')
    assert result == data


@mock.patch.object(helpers.ch_search_api_client.company, 'get_company_profile')
def test_get_company_profile_not_ok(mock_get_company_profile):
    mock_get_company_profile.return_value = create_response(400)
    with pytest.raises(HTTPError):
        helpers.get_company_profile('123456')
