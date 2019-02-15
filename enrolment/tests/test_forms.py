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
