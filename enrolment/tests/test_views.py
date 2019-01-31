import datetime

import pytest
from unittest import mock

from django.urls import reverse

from enrolment import constants, helpers, views

urls = (
    reverse('enrolment', kwargs={'step': 'business-type'}),
    reverse('enrolment-success'),
)


@pytest.fixture
def submit_enrolment_step(client):
    return submit_step_factory(
        client=client,
        url_name='enrolment',
        view_name='enrolment_view',
        view_class=views.EnrolmentView,
    )


@pytest.fixture(autouse=True)
def mock_get_company_profile():
    patch = mock.patch.object(helpers, 'get_company_profile', return_value={
        'company_number': '12345678',
        'company_name': 'Example corp',
        'sic_codes': ['1234'],
        'date_of_creation': '2001-01-20',
        'registered_office_address': {'one': '555', 'two': 'fake street'},
    })
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_create_user():
    patch = mock.patch.object(helpers, 'create_user', return_value={
        'email': 'test@test.com',
        'verification_code': '123456',
    })
    yield patch.start()
    patch.stop()


@pytest.mark.parametrize('url', urls)
def test_404_feature_off(url, client, settings):

    settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_ON'] = False

    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize('url', urls)
def test_200_feature_on(url, client, settings):

    settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_ON'] = True

    response = client.get(url)

    assert response.status_code == 200


def submit_step_factory(client, url_name, view_name, view_class):
    step_names = iter([name for name, form in view_class.form_list])

    def submit_step(data, step_name=None):
        step_name = step_name or next(step_names)
        return client.post(
            reverse(url_name, kwargs={'step': step_name}),
            {
                view_name + '-current_step': step_name,
                **{
                    step_name + '-' + key: value
                    for key, value in data.items()
                }
            },
        )
    return submit_step


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_companies_house_enrolment(
    mock_clean, client, captcha_stub, submit_enrolment_step
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'text@example.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '123'
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'company_name': 'Example corp',
        'company_number': '12345678',
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'given_name': 'Foo',
        'family_name': 'Example',
        'job_title': 'Exampler',
        'phone_number': '1232342',
        'confirmed_is_company_representative': True,
        'confirmed_background_checks': True,
    })
    assert response.status_code == 302


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_companies_house_enrolment_change_company_name(
    mock_clean, client, captcha_stub, submit_enrolment_step
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'text@example.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '123'
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'company_name': 'Foo corp',
        'company_number': '12345678',
    })
    assert response.status_code == 302

    # given the user has submitted their company details
    response = submit_enrolment_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    # when they go back and changed their company
    response = submit_enrolment_step(
        data={
            'company_name': 'Bar corp',
            'company_number': '12345679',
        },
        step_name=views.EnrolmentView.COMPANY_SEARCH
    )
    assert response.status_code == 302

    # then the company name is not overwritten by the previously submitted one.
    response = client.get(response.url)

    assert response.context_data['form']['company_name'].data == 'Example corp'


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_create_user_enrolment(
    mock_clean, mock_create_user, client, captcha_stub, submit_enrolment_step
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'tex4566eqw34e7@example.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })

    assert response.status_code == 302
    assert mock_create_user.call_count == 1
    assert mock_create_user.call_args == mock.call(
        email='tex4566eqw34e7@example.com',
        password='thing'
    )


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_companies_house_enrolment_expose_company(
    mock_clean, client, captcha_stub, submit_enrolment_step
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'text@example.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '123'
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'company_name': 'Example corp',
        'company_number': '12345678',
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.context_data['company'] == {
        'company_name': 'Example corp',
        'company_number': '12345678',
        'sic': '1234',
        'date_created': datetime.date(2001, 1, 1),
        'address_finder': '',
        'address': '555 fake street',
        'industry': 'AEROSPACE',
        'website_address': ''
    }


def test_companies_house_enrolment_redirect_to_start(
    submit_enrolment_step, client
):

    url = reverse(
        'enrolment', kwargs={'step': views.EnrolmentView.COMPANY_SEARCH}
    )
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        'enrolment', kwargs={'step': views.EnrolmentView.BUSINESS_TYPE}
    )
