from django.urls import reverse

from enrolment import forms


def test_companies_house_search_company_number_empty():
    form = forms.CompaniesHouseSearch(data={'company_name': 'Thing'})

    assert form.is_valid() is False

    url = reverse('enrolment', kwargs={'step': 'business-type'})
    assert form.errors['company_name'] == [
        form.MESSAGE_COMPANY_NOT_FOUND.format(url=url)
    ]
