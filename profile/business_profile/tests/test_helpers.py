from unittest import mock

from directory_api_client import api_client
from directory_constants import company_types
import pytest

from core.tests.helpers import create_response
from profile.business_profile import helpers


@pytest.mark.parametrize('value,expected', (
    (company_types.COMPANIES_HOUSE, True),
    (company_types.SOLE_TRADER, False),
    (company_types.CHARITY, False),
    (company_types.PARTNERSHIP, False),
))
def test_profile_parser_is_in_companies_house(value, expected):
    parser = helpers.CompanyParser({'company_type': value})

    assert parser.is_in_companies_house is expected


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


@mock.patch.object(api_client.company, 'profile_retrieve')
def test_get_company_profile_not_found(mock_profile_retrieve):
    mock_profile_retrieve.return_value = create_response(status_code=404)

    profile = helpers.get_company_profile('1234')

    assert mock_profile_retrieve.call_count == 1
    assert mock_profile_retrieve.call_args == mock.call('1234')
    assert profile is None
