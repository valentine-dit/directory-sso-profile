import pytest
from unittest import mock
from core.tests.helpers import create_response

from django.urls import reverse
from requests.exceptions import HTTPError

from enrolment import forms, helpers


@pytest.fixture(autouse=True)
def mock_clean():
    patch = mock.patch('captcha.fields.ReCaptchaField.clean')
    yield patch.start()
    patch.stop()


@mock.patch.object(helpers.sso_api_client.user, 'create_user')
def test_create_user_password_invalid_not_matching(mock_create_user):
    mock_create_user.return_value = create_response(400)
    form = forms.UserAccount(
        data={
            'email': 'test@test.com',
            'password': 'password',
            'password_confirmed': 'drowssap',
         }
    )

    assert form.is_valid() is False
    assert "Passwords don't match" in form.errors['password_confirmed']


@mock.patch.object(helpers.sso_api_client.user, 'create_user')
def test_create_user_password_invalid(mock_create_user):
    data = {'password': 'validation error'}
    mock_create_user.return_value = create_response(400, data)

    form = forms.UserAccount(
        data={
            'email': 'test@test.com',
            'password': '12P',
            'password_confirmed': '12P',
        }
    )

    assert form.is_valid() is False
    assert "Invalid Password" in form.errors['password']


@mock.patch.object(helpers.sso_api_client.user, 'create_user')
def test_create_user_password_existing_user(mock_create_user):
    mock_create_user.return_value = create_response(400)

    form = forms.UserAccount(
        data={
            'email': 'test@test.com',
            'password': '12P',
            'password_confirmed': '12P',
            'terms_agreed': True,
        }
    )
    assert form.is_valid() is True
    assert not form.cleaned_data['user_details']


@mock.patch.object(helpers.sso_api_client.user, 'create_user')
def test_create_user_error(mock_create_user):

    mock_create_user.return_value = create_response(401)
    form = forms.UserAccount(
        data={
            'email': 'test@test.com',
            'password': '12P',
            'password_confirmed': '12P',
            'terms_agreed': True,
        }
    )

    with pytest.raises(HTTPError):
        form.is_valid()


@mock.patch.object(helpers.sso_api_client.user, 'create_user')
def test_create_user(mock_create_user):
    data = {'email': 'test@test.com', 'verification_code': '12345'}
    mock_create_user.return_value = create_response(201, data)

    form = forms.UserAccount(
        data={
            'email': 'test@test.com',
            'password': 'ABCdefg12345',
            'password_confirmed': 'ABCdefg12345',
            'terms_agreed': True,
        }
    )

    assert form.is_valid() is True
    assert form.cleaned_data["user_details"] == data


def test_companies_house_search_company_number_empty(client):
    form = forms.CompaniesHouseSearch(
        data={'company_name': 'Thing'},
        session=client.session
    )

    assert form.is_valid() is False

    url = reverse('enrolment-business-type')
    assert form.errors['company_name'] == [
        form.MESSAGE_COMPANY_NOT_FOUND.format(url=url)
    ]


@mock.patch.object(helpers, 'get_company_profile', return_value={
    'company_status': 'dissolved',
})
def test_companies_house_search_company_dissolved(client):
    form = forms.CompaniesHouseSearch(
        data={'company_name': 'Thing', 'company_number': '1234'},
        session=client.session
    )

    assert form.is_valid() is False
    assert form.errors['company_name'] == [form.MESSAGE_COMPANY_NOT_ACTIVE]


@mock.patch.object(helpers, 'get_company_profile', return_value={
    'company_status': 'active',
})
def test_companies_house_search_company_active(client):
    form = forms.CompaniesHouseSearch(
        data={'company_name': 'Thing', 'company_number': '1234'},
        session=client.session
    )

    assert form.is_valid() is True


@pytest.mark.parametrize('address,expected', (
    ('thing\nthing', 'thing\nthing\nEEE EEE'),
    ('thing\nthing\nEEE EEE', 'thing\nthing\nEEE EEE')
))
def test_sole_trader_search_address_postcode_appended(address, expected):
    form = forms.SoleTraderSearch(data={
        'company_name': 'thing',
        'address': address,
        'postal_code': 'EEE EEE',
    })
    assert form.is_valid()

    assert form.cleaned_data['address'] == expected


@pytest.mark.parametrize('address', ('thing\n', 'thing\n '))
def test_sole_trader_search_address_too_short(address):
    form = forms.SoleTraderSearch(data={
        'address': address,
        'postal_code': 'EEE EEE',
    })
    assert form.is_valid() is False

    assert form.errors['address'] == [
        forms.SoleTraderSearch.MESSAGE_INVALID_ADDRESS
    ]
