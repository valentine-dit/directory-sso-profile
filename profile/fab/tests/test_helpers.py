from unittest import mock

from directory_api_client import api_client
import pytest

from core.tests.helpers import create_response
from profile.fab import helpers


@pytest.mark.parametrize('value,expected', (
    ('COMPANIES_HOUSE', False),
    ('SOLE_TRADER', True),
))
def test_profile_parser_is_sole_trader(value, expected):
    parser = helpers.CompanyParser({'company_type': value})

    assert parser.is_sole_trader is expected


def test_profile_parser_no_data_serialize_for_form():
    parser = helpers.CompanyParser({})

    assert parser.serialize_for_form() == {}


def test_profile_parser_no_data_serialize_for_template():
    parser = helpers.CompanyParser({})

    assert parser.serialize_for_template() == {}


@mock.patch.object(api_client.supplier, 'retrieve_profile')
def test_get_supplier_profile(mock_retrieve_profile):
    data = {'name': 'Foo Bar'}
    mock_retrieve_profile.return_value = create_response(data)

    profile = helpers.get_supplier_profile('1234')

    assert mock_retrieve_profile.call_count == 1
    assert mock_retrieve_profile.call_args == mock.call('1234')
    assert profile == data


@mock.patch.object(api_client.supplier, 'retrieve_profile')
def test_get_supplier_profile_not_found(mock_retrieve_profile):
    mock_retrieve_profile.return_value = create_response(status_code=404)

    profile = helpers.get_supplier_profile('1234')

    assert mock_retrieve_profile.call_count == 1
    assert mock_retrieve_profile.call_args == mock.call('1234')
    assert profile is None


@mock.patch.object(api_client.company, 'retrieve_private_profile')
def test_get_company_profile_not_found(mock_retrieve_private_profile):
    mock_retrieve_private_profile.return_value = create_response(status_code=404)

    profile = helpers.get_company_profile('1234')

    assert mock_retrieve_private_profile.call_count == 1
    assert mock_retrieve_private_profile.call_args == mock.call('1234')
    assert profile is None
