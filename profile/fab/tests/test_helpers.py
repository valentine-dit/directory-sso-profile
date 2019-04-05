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


def test_profile_parser_keywords_joined():
    parser = helpers.ProfileParser({'keywords': 'thing,other'})

    assert parser.keywords == 'thing, other'


@pytest.mark.parametrize('value,expected', (
    (None, ''),
    ('', ''),
    (['AEROSPACE'], 'Aerospace'),
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


@pytest.mark.parametrize('value,expected', (
    ({'expertise_industries': 'thing'}, True),
    ({'expertise_regions': 'thing'}, True),
    ({'expertise_countries': 'thing'}, True),
    ({'expertise_languages': 'thing'}, True),
    ({'expertise_industries': ''}, False),
    ({'expertise_regions': ''}, False),
    ({'expertise_countries': ''}, False),
    ({'expertise_languages': ''}, False),
    ({}, False),
))
def test_profile_parser_has_expertise(value, expected):
    parser = helpers.ProfileParser(value)

    assert parser.has_expertise is expected


@pytest.mark.parametrize('value,expected', (
    ({'expertise_industries': ['MARINE']}, 'Marine'),
    ({'expertise_industries': ['MARINE', 'POWER']}, 'Marine, Power'),
    ({'expertise_industries': ['MARINE', '']}, 'Marine'),
    ({'expertise_industries': ['MARINE', None]}, 'Marine'),
    ({'expertise_industries': ['MARINE', 'bad-value']}, 'Marine'),
    ({'expertise_industries': []}, ''),
    ({'expertise_industries': ''}, ''),
    ({'expertise_industries': None}, ''),
    ({}, ''),
))
def test_profile_parser_expertise_industries_label(value, expected):
    parser = helpers.ProfileParser(value)

    assert parser.expertise_industries_label == expected


@pytest.mark.parametrize('value,expected', (
    ({'expertise_regions': ['LONDON']}, 'London'),
    ({'expertise_regions': ['LONDON', 'WALES']}, 'London, Wales'),
    ({'expertise_regions': ['LONDON', '']}, 'London'),
    ({'expertise_regions': ['LONDON', None]}, 'London'),
    ({'expertise_regions': ['LONDON', 'bad-value']}, 'London'),
    ({'expertise_regions': []}, ''),
    ({'expertise_regions': ''}, ''),
    ({'expertise_regions': None}, ''),
    ({}, ''),
))
def test_profile_parser_expertise_regions_label(value, expected):
    parser = helpers.ProfileParser(value)

    assert parser.expertise_regions_label == expected


@pytest.mark.parametrize('value,expected', (
    ({'expertise_countries': ['AL']}, 'Albania'),
    ({'expertise_countries': ['AL', 'AO']}, 'Albania, Angola'),
    ({'expertise_countries': ['AL', '']}, 'Albania'),
    ({'expertise_countries': ['AL', None]}, 'Albania'),
    ({'expertise_countries': ['AL', 'bad-value']}, 'Albania'),
    ({'expertise_countries': []}, ''),
    ({'expertise_countries': ''}, ''),
    ({'expertise_countries': None}, ''),
    ({}, ''),
))
def test_profile_parser_expertise_countries_label(value, expected):
    parser = helpers.ProfileParser(value)

    assert parser.expertise_countries_label == expected


@pytest.mark.parametrize('value,expected', (
    ({'expertise_languages': ['aa']}, 'Afar'),
    ({'expertise_languages': ['aa', 'ak']}, 'Afar, Akan'),
    ({'expertise_languages': ['aa', '']}, 'Afar'),
    ({'expertise_languages': ['aa', None]}, 'Afar'),
    ({'expertise_languages': ['aa', 'bad-value']}, 'Afar'),
    ({'expertise_languages': []}, ''),
    ({'expertise_languages': ''}, ''),
    ({'expertise_languages': None}, ''),
    ({}, ''),
))
def test_profile_parser_expertise_languages_label(value, expected):
    parser = helpers.ProfileParser(value)

    assert parser.expertise_languages_label == expected
