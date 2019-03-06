import pytest

from django.urls import reverse

from enrolment import forms


def test_password_verify_password_not_matching():
    form = forms.UserAccount(
        data={'password': 'password', 'password_confirmed': 'drowssap'}
    )

    assert form.is_valid() is False
    assert "Passwords don't match" in form.errors['password_confirmed']


def test_companies_house_search_company_number_empty():
    form = forms.CompaniesHouseSearch(data={'company_name': 'Thing'})

    assert form.is_valid() is False

    url = reverse('enrolment-business-type')
    assert form.errors['company_name'] == [
        form.MESSAGE_COMPANY_NOT_FOUND.format(url=url)
    ]


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
