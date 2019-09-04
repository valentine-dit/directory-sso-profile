from unittest import mock

from directory_components.forms import CharField, EmailField
import pytest

from enrolment import forms, helpers


@pytest.fixture(autouse=True)
def mock_clean():
    patch = mock.patch('captcha.fields.ReCaptchaField.clean')
    yield patch.start()
    patch.stop()


def test_create_user_password_invalid_not_matching():
    form = forms.UserAccount(
        data={
            'email': 'test@test.com',
            'password': 'password',
            'password_confirmed': 'drowssap',
         }
    )

    assert form.is_valid() is False
    assert "Passwords don't match" in form.errors['password_confirmed']


def test_verification_code_empty_email():

    form = forms.UserAccountVerification()
    assert isinstance(form.fields['email'], EmailField)


def test_verification_code_with_email():

    form = forms.UserAccountVerification(
        initial={'email': 'test@test.com'}
    )
    assert isinstance(form.fields['email'], CharField)


@mock.patch.object(helpers, 'get_company_profile', return_value={
    'company_status': 'active',
})
def test_companies_house_search_company_number_incomplete_data(client):
    expected = 'Please contact support to register a Royal Charter Company.'
    form = forms.CompaniesHouseSearch(
        data={'company_name': 'Thing', 'company_number': 'RC232323'},
        session=client.session
    )

    assert form.is_valid() is False
    assert form.errors['company_name'] == [expected]


def test_companies_house_search_company_number_empty(client):
    form = forms.CompaniesHouseSearch(
        data={'company_name': 'Thing'},
        session=client.session
    )

    assert form.is_valid() is False
    assert form.errors['company_name'] == [form.MESSAGE_COMPANY_NOT_FOUND]


def test_companies_house_search_company_name_empty(client):
    form = forms.CompaniesHouseSearch(
        data={},
        session=client.session
    )

    assert form.is_valid() is False
    assert form.errors['company_name'] == ['This field is required.']


@mock.patch.object(helpers, 'get_company_profile', return_value={
    'company_status': 'dissolved',
})
def test_companies_house_search_company_dissolved(client):
    form = forms.CompaniesHouseSearch(
        data={'company_name': 'Thing', 'company_number': '23232323'},
        session=client.session
    )

    assert form.is_valid() is False
    assert form.errors['company_name'] == [form.MESSAGE_COMPANY_NOT_ACTIVE]


@mock.patch.object(helpers, 'get_company_profile', return_value={
    'company_status': 'active',
})
def test_companies_house_search_company_active(client):
    form = forms.CompaniesHouseSearch(
        data={'company_name': 'Thing', 'company_number': '23232323'},
        session=client.session
    )

    assert form.is_valid() is True


@pytest.mark.parametrize('address,expected', (
    ('thing\nthing', 'thing\nthing\nEEE EEE'),
    ('thing\nthing\nEEE EEE', 'thing\nthing\nEEE EEE')
))
def test_sole_trader_search_address_postcode_appended(address, expected):
    form = forms.NonCompaniesHouseSearch(data={
        'company_name': 'thing',
        'company_type': 'SOLE_TRADER',
        'address': address,
        'postal_code': 'EEE EEE',
        'sectors': 'AEROSPACE',
    })
    assert form.is_valid()

    assert form.cleaned_data['address'] == expected


@pytest.mark.parametrize('address', ('thing\n', 'thing\n '))
def test_sole_trader_search_address_too_short(address):
    form = forms.NonCompaniesHouseSearch(data={
        'address': address,
        'postal_code': 'EEE EEE',
        'sectors': 'AEROSPACE',
    })
    assert form.is_valid() is False

    assert form.errors['address'] == [
        forms.NonCompaniesHouseSearch.MESSAGE_INVALID_ADDRESS
    ]
