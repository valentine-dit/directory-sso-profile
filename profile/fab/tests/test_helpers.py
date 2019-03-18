from unittest import mock

import pytest

from profile.fab import helpers


@pytest.mark.parametrize('value,expected', (
    ('2019-01-31', '31 January 2019'),
    ('', None),
    (None, None),
))
def test_profile_parser_date_of_creation(value, expected):
    parser = helpers.ProfileParser({'date_of_creation': value})
    assert parser.date_of_creation == expected


@pytest.mark.parametrize('value,expected', (
    (
        {
            'address_line_1': '123 Fake street',
            'address_line_2': 'Fakeville',
            'locality': 'Fakeshire',
            'postal_code': 'FAK ELA'
        },
        '123 Fake street, Fakeville, Fakeshire, FAK ELA'
    ),
    (
        {
            'address_line_1': '123 Fake street',
            'locality': 'Fakeshire',
            'postal_code': 'FAK ELA'
        },
        '123 Fake street, Fakeshire, FAK ELA'
    ),
    (
        {
            'address_line_1': '123 Fake street',
            'address_line_2': 'Fakeville',
            'postal_code': 'FAK ELA'
        },
        '123 Fake street, Fakeville, FAK ELA'
    ),
))
def test_profile_parser_address(value, expected):
    parser = helpers.ProfileParser(value)
    assert parser.address == expected


@pytest.mark.parametrize('value', ('', None))
@mock.patch.object(helpers, 'tokenize_keywords')
def test_profile_parser_keywords_no_keyword(mock_tokenize_keywords, value):
    parser = helpers.ProfileParser({'keywords': value})

    parser.keywords

    assert mock_tokenize_keywords.call_count == 0


@mock.patch.object(helpers, 'tokenize_keywords')
def test_profile_parser_keywords(mock_tokenize_keywords):
    parser = helpers.ProfileParser({'keywords': 'thing,other'})

    parser.keywords

    assert mock_tokenize_keywords.call_count == 1
    assert mock_tokenize_keywords.call_args == mock.call('thing,other')


@pytest.mark.parametrize('value,expected', (
    (None, []),
    ('', []),
    (['AEROSPACE'], ['Aerospace']),
))
def test_profile_parser_sectors(value, expected):
    parser = helpers.ProfileParser({'sectors': value})

    assert parser.sectors_label == expected


@pytest.mark.parametrize('value,expected', (
    (None, None),
    ('', None),
    ('1-10', '1-10'),
))
def test_profile_parser_employees_label(value, expected):
    parser = helpers.ProfileParser({'employees': value})

    assert parser.employees_label == expected


@pytest.mark.parametrize('value,expected', (
    ('COMPANIES_HOUSE', False),
    ('SOLE_TRADER', True),
))
def test_profile_parser_is_sole_trader(value, expected):
    parser = helpers.ProfileParser({'company_type': value})

    assert parser.is_sole_trader is expected
