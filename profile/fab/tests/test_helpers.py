import pytest

from profile.fab import helpers


@pytest.mark.parametrize('value,expected', (
    ('COMPANIES_HOUSE', False),
    ('SOLE_TRADER', True),
))
def test_profile_parser_is_sole_trader(value, expected):
    parser = helpers.CompanyParser({'company_type': value})

    assert parser.is_sole_trader is expected
