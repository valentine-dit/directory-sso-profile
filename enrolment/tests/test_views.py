from unittest import mock

from freezegun import freeze_time
import pytest
from requests.cookies import RequestsCookieJar
from requests.exceptions import HTTPError

from django.urls import resolve, reverse

from core.tests.helpers import create_response
from enrolment import constants, helpers, views
from directory_constants.constants import urls as constants_url


urls = (
    reverse('enrolment-business-type'),
    reverse('enrolment-start'),
    reverse('enrolment-companies-house', kwargs={'step': views.USER_ACCOUNT}),
    reverse('enrolment-sole-trader', kwargs={'step': views.USER_ACCOUNT}),
)
company_types = (constants.COMPANIES_HOUSE_COMPANY, constants.SOLE_TRADER)


@pytest.fixture(autouse=True)
def mock_session_user(client, settings):
    client.cookies[settings.SSO_SESSION_COOKIE] = '123'
    patch = mock.patch(
        'directory_sso_api_client.client.sso_api_client.user.get_session_user',
        return_value=create_response(404)
    )

    def login():
        started.return_value = create_response(
            200, {'id': '123', 'email': 'test@a.com'}
        )
    started = patch.start()
    started.login = login
    yield started
    patch.stop()


@pytest.fixture
def submit_companies_house_step(client):
    return submit_step_factory(
        client=client,
        url_name='enrolment-companies-house',
        view_name='companies_house_enrolment_view',
        view_class=views.CompaniesHouseEnrolmentView,
    )


@pytest.fixture
def submit_sole_trader_step(client):
    return submit_step_factory(
        client=client,
        url_name='enrolment-sole-trader',
        view_name='sole_trader_enrolment_view',
        view_class=views.SoleTraderEnrolmentView,
    )


@pytest.fixture
def submit_step_builder(submit_companies_house_step, submit_sole_trader_step):
    def inner(choice):
        if choice == constants.COMPANIES_HOUSE_COMPANY:
            return submit_companies_house_step
        elif choice == constants.SOLE_TRADER:
            return submit_sole_trader_step
    return inner


@pytest.fixture(autouse=True)
def mock_get_company_profile():
    patch = mock.patch.object(helpers, 'get_company_profile', return_value={
        'company_number': '12345678',
        'company_name': 'Example corp',
        'sic_codes': ['1234'],
        'date_of_creation': '2001-01-20',
        'registered_office_address': {
            'address_line_1': '555 fake street, London',
            'postal_code': 'EDG 4DF'
        },
    })
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_send_verification_code_email():
    patch = mock.patch.object(helpers, 'send_verification_code_email')
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_clean():
    patch = mock.patch('captcha.fields.ReCaptchaField.clean')
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_retrieve_public_profile(client):
    patch = mock.patch.object(
        helpers.api_client.company, 'retrieve_public_profile',
        return_value=create_response(404)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_validate_company_number(client):
    patch = mock.patch.object(
        helpers.api_client.company, 'validate_company_number',
        return_value=create_response(200)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_request_collaboration(client):
    patch = mock.patch.object(
        helpers.api_client.company, 'request_collaboration',
        return_value=create_response(200)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_enrolment_send(client):
    patch = mock.patch.object(
        helpers.api_client.enrolment, 'send_form',
        return_value=create_response(201)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_create_user():
    response = create_response(200, {
        'email': 'test@test.com',
        'verification_code': '123456',
    })
    patch = mock.patch.object(
        helpers.sso_api_client.user, 'create_user',
        return_value=response
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_user_has_company():
    patch = mock.patch.object(
        helpers.api_client.company, 'retrieve_private_profile',
        return_value=create_response(404)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_confirm_verification_code():
    response = create_response(200)
    patch = mock.patch.object(
        helpers.sso_api_client.user, 'verify_verification_code',
        return_value=response
    )
    response.cookies = RequestsCookieJar()
    response.cookies['debug_sso_session_cookie'] = 'a'
    response.cookies['sso_display_logged_in'] = 'true'
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_notify_already_registered():
    patch = mock.patch.object(helpers, 'notify_already_registered')
    yield patch.start()
    patch.stop()


@pytest.fixture
def steps_data(captcha_stub):
    data = {
        views.USER_ACCOUNT: {
            'email': 'test@a.com',
            'password': 'thing',
            'password_confirmed': 'thing',
            'captcha': captcha_stub,
            'terms_agreed': True
        },
        views.COMPANY_SEARCH: {
            'company_name': 'Example corp',
            'company_number': '12345678',
        },
        views.PERSONAL_INFO: {
            'given_name': 'Foo',
            'family_name': 'Example',
            'job_title': 'Exampler',
            'phone_number': '1232342',
            'confirmed_is_company_representative': True,
            'confirmed_background_checks': True,
        },
        views.VERIFICATION: {
            'code': '12345',
        },
    }
    return data


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


@pytest.mark.parametrize('choice,expected_url', (
    (
        constants.COMPANIES_HOUSE_COMPANY,
        views.BusinessTypeRoutingView.url_companies_house_enrolment
    ),
    (
        constants.SOLE_TRADER,
        views.BusinessTypeRoutingView.url_sole_trader_enrolment
    ),
))
def test_enrolment_routing(client, choice, expected_url):
    url = reverse('enrolment-business-type')

    response = client.post(url, {'choice': choice})

    assert response.status_code == 302
    assert response.url == expected_url


def test_companies_house_enrolment(
    client, submit_companies_house_step, mock_session_user, steps_data
):
    response = submit_companies_house_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_companies_house_step(steps_data[views.COMPANY_SEARCH])
    assert response.status_code == 302

    response = submit_companies_house_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.PERSONAL_INFO])
    assert response.status_code == 302


def test_companies_house_enrolment_change_company_name(
    client, submit_companies_house_step, mock_session_user, steps_data
):
    response = submit_companies_house_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_companies_house_step(steps_data[views.COMPANY_SEARCH])
    assert response.status_code == 302

    # given the user has submitted their company details
    response = submit_companies_house_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    # when they go back and changed their company
    response = submit_companies_house_step(
        data={
            'company_name': 'Bar corp',
            'company_number': '12345679',
        },
        step_name=views.COMPANY_SEARCH
    )
    assert response.status_code == 302

    # then the company name is not overwritten by the previously submitted one.
    response = client.get(response.url)

    assert response.context_data['form']['company_name'].data == 'Example corp'


def test_companies_house_enrolment_expose_company(
    client, submit_companies_house_step, mock_session_user, steps_data
):
    response = submit_companies_house_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_companies_house_step(steps_data[views.COMPANY_SEARCH])
    assert response.status_code == 302

    response = submit_companies_house_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.context_data['company'] == {
        'company_name': 'Example corp',
        'company_number': '12345678',
        'sic': '1234',
        'date_of_creation': '2001-01-01',
        'postal_code': 'EDG 4DF',
        'address': '555 fake street, London',
        'address_line_1': '555 fake street',
        'address_line_2': 'London',
        'industry': 'AEROSPACE',
        'website_address': ''
    }


def test_companies_house_enrolment_redirect_to_start(client):
    url = reverse(
        'enrolment-companies-house', kwargs={'step': views.COMPANY_SEARCH}
    )
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('enrolment-business-type')


def test_companies_house_enrolment_submit_end_to_end(
    client, submit_companies_house_step, mock_session_user,
    mock_enrolment_send, steps_data
):
    response = submit_companies_house_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_companies_house_step(steps_data[views.COMPANY_SEARCH])
    assert response.status_code == 302

    response = submit_companies_house_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.PERSONAL_INFO])
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 200
    assert response.template_name == 'enrolment/success-companies-house.html'
    assert mock_enrolment_send.call_count == 1
    assert mock_enrolment_send.call_args == mock.call({
        'sso_id': '123',
        'company_email': 'test@a.com',
        'contact_email_address': 'test@a.com',
        'company_name': 'Example corp',
        'company_number': '12345678',
        'sic': '1234',
        'date_of_creation': '2001-01-01',
        'postal_code': 'EDG 4DF',
        'address_line_1': '555 fake street',
        'address_line_2': 'London',
        'industry': 'AEROSPACE',
        'given_name': 'Foo',
        'family_name': 'Example',
        'job_title': 'Exampler',
        'phone_number': '1232342',
        'company_type': 'COMPANIES_HOUSE',
    })


def test_companies_house_enrolment_submit_end_to_end_logged_in(
    client, captcha_stub, submit_companies_house_step,
    mock_session_user, mock_enrolment_send, steps_data
):
    mock_session_user.login()

    url = reverse(
        'enrolment-companies-house', kwargs={'step': views.USER_ACCOUNT}
    )
    response = client.get(url)
    assert response.status_code == 302

    step = resolve(response.url).kwargs['step']

    assert step == views.COMPANY_SEARCH

    response = submit_companies_house_step(
        steps_data[views.COMPANY_SEARCH],
        step_name=step,
    )

    assert response.status_code == 302

    step = resolve(response.url).kwargs['step']
    response = submit_companies_house_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    }, step_name=step)
    assert response.status_code == 302

    step = resolve(response.url).kwargs['step']
    response = submit_companies_house_step(
        steps_data[views.PERSONAL_INFO],
        step_name=step
    )
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 200
    assert response.template_name == 'enrolment/success-companies-house.html'
    assert mock_enrolment_send.call_count == 1
    assert mock_enrolment_send.call_args == mock.call({
        'sso_id': '123',
        'company_email': 'test@a.com',
        'contact_email_address': 'test@a.com',
        'company_name': 'Example corp',
        'company_number': '12345678',
        'sic': '1234',
        'date_of_creation': '2001-01-01',
        'postal_code': 'EDG 4DF',
        'address_line_1': '555 fake street',
        'address_line_2': 'London',
        'industry': 'AEROSPACE',
        'given_name': 'Foo',
        'family_name': 'Example',
        'job_title': 'Exampler',
        'phone_number': '1232342',
        'company_type': 'COMPANIES_HOUSE',
    })


@pytest.mark.parametrize(
    'step', [name for name, _ in views.CompaniesHouseEnrolmentView.form_list]
)
def test_companies_house_enrolment_has_company(
    client, step, mock_user_has_company, mock_session_user
):
    mock_session_user.login()

    mock_user_has_company.return_value = create_response(200)

    url = reverse('enrolment-companies-house', kwargs={'step': step})
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('about')


@pytest.mark.parametrize(
    'step', [name for name, _ in views.CompaniesHouseEnrolmentView.form_list]
)
def test_companies_house_enrolment_has_company_error(
    client, step, mock_user_has_company, mock_session_user
):
    mock_session_user.login()

    mock_user_has_company.return_value = create_response(500)

    url = reverse('enrolment-companies-house', kwargs={'step': step})

    with pytest.raises(HTTPError):
        client.get(url)


@mock.patch('enrolment.views.helpers.request_collaboration')
def test_companies_house_enrolment_submit_end_to_end_company_has_account(
    mock_request_collaboration, client, steps_data,
    submit_companies_house_step, mock_session_user, mock_enrolment_send,
    mock_validate_company_number
):
    mock_validate_company_number.return_value = create_response(400)

    response = submit_companies_house_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_companies_house_step(steps_data[views.COMPANY_SEARCH])
    assert response.status_code == 302

    response = submit_companies_house_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.PERSONAL_INFO])
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 200
    assert response.template_name == 'enrolment/success-companies-house.html'
    assert mock_enrolment_send.call_count == 0

    assert mock_request_collaboration.call_count == 1
    assert mock_request_collaboration.call_args == mock.call(
        company_number='12345678',
        email='test@a.com',
        name='Foo Example',
        form_url=(
            reverse('enrolment-companies-house', kwargs={'step': 'finished'})
        )
    )


def test_companies_house_search_has_company_not_found_url(
    submit_companies_house_step, mock_session_user, client, steps_data
):
    response = submit_companies_house_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()
    response = client.get(response.url)

    not_found_url = constants_url.build_great_url(
        'contact/triage/great-account/company-not-found/'
    )

    assert response.context_data['company_not_found_url'] == not_found_url


def test_disable_select_company(client, settings):
    settings.FEATURE_FLAGS[
        'NEW_ACCOUNT_JOURNEY_SELECT_BUSINESS_ON'
    ] = False

    url = reverse('enrolment-business-type')
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        'enrolment-companies-house', kwargs={'step': 'user-account'}
    )


def test_user_has_company_redirect_on_start(
    client, mock_user_has_company, mock_session_user
):
    mock_session_user.login()
    mock_user_has_company.return_value = create_response(200)

    url = reverse('enrolment-start')
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')


def test_user_has_no_company_redirect_on_start(
    client, mock_user_has_company, mock_session_user
):
    mock_session_user.login()
    mock_user_has_company.return_value = create_response(404)

    url = reverse('enrolment-start')
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.parametrize('company_type', company_types)
def test_create_user_enrolment(
    client, steps_data, submit_step_builder, company_type
):
    submit_step = submit_step_builder(company_type)
    response = submit_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302


@pytest.mark.parametrize(
    'company_type,form_url_name',
    zip(company_types, ['enrolment-companies-house', 'enrolment-sole-trader'])
)
def test_create_user_enrolment_already_exists(
    company_type, form_url_name, steps_data, mock_create_user,
    submit_step_builder, mock_notify_already_registered
):
    mock_create_user.return_value = create_response(400)

    submit_step = submit_step_builder(company_type)

    response = submit_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302
    assert mock_notify_already_registered.call_count == 1
    assert mock_notify_already_registered.call_args == mock.call(
        email='test@a.com',
        form_url=reverse(form_url_name, kwargs={'step': views.USER_ACCOUNT})
    )


@pytest.mark.parametrize('company_type', company_types)
@freeze_time('2012-01-14 12:00:02')
def test_user_verification_passes_cookies(
    company_type, submit_step_builder, client, steps_data
):
    submit_step = submit_step_builder(company_type)

    response = submit_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    assert str(response.cookies['debug_sso_session_cookie']) == (
        'Set-Cookie: debug_sso_session_cookie=a; '
        'Comment=None; '
        'expires=Sat, 14 Jan 2012 12:00:02 GMT; '
        'Path=/; '
        'Version=0'
    )
    assert str(response.cookies['sso_display_logged_in']) == (
        'Set-Cookie: sso_display_logged_in=true; '
        'Comment=None; '
        'expires=Sat, 14 Jan 2012 12:00:02 GMT; '
        'Path=/; '
        'Version=0'
    )


@pytest.mark.parametrize('company_type', company_types)
def test_confirm_user_verify_code_incorrect_code(
    client, company_type, submit_step_builder, mock_session_user,
    mock_confirm_verification_code, steps_data
):
    submit_step = submit_step_builder(company_type)

    mock_session_user.return_value = create_response(404)
    mock_confirm_verification_code.return_value = create_response(400)

    response = submit_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_step(steps_data[views.VERIFICATION])

    assert response.status_code == 200
    assert response.context_data['form'].errors['code'] == ['Invalid code']


@pytest.mark.parametrize('company_type', company_types)
def test_confirm_user_verify_code_remote_error(
    company_type, submit_step_builder, mock_session_user,
    mock_confirm_verification_code, steps_data
):
    submit_step = submit_step_builder(company_type)

    mock_session_user.return_value = create_response(404)
    mock_confirm_verification_code.return_value = create_response(500)

    response = submit_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    with pytest.raises(HTTPError):
        submit_step(steps_data[views.VERIFICATION])


@pytest.mark.parametrize('company_type', company_types)
def test_confirm_user_verify_code(
    client, company_type, submit_step_builder, mock_session_user,
    mock_confirm_verification_code, steps_data
):
    submit_step = submit_step_builder(company_type)

    mock_session_user.return_value = create_response(404)

    response = submit_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_step(steps_data[views.VERIFICATION])

    mock_session_user.login()

    assert response.status_code == 302
    assert mock_confirm_verification_code.call_count == 1
    assert mock_confirm_verification_code.call_args == mock.call({
        'email': 'test@a.com', 'code': '12345'
    })


def test_sole_trader_enrolment_expose_company(
    client, submit_sole_trader_step, mock_session_user, steps_data
):
    response = submit_sole_trader_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_sole_trader_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_sole_trader_step({
        'company_name': 'Test company',
        'postal_code': 'EEA 3AD',
        'address': '555 fake street, London',
    })

    assert response.status_code == 302

    response = submit_sole_trader_step({
        'company_name': 'Test company',
        'postal_code': 'EEA 3AD',
        'address': '555 fake street, London',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.context_data['company'] == {
        'company_name': 'Test company',
        'postal_code': 'EEA 3AD',
        'address': '555 fake street\nLondon',
        'address_line_1': '555 fake street',
        'address_line_2': 'London',
        'industry': 'AEROSPACE',
        'website_address': ''
    }


def test_sole_trader_enrolment_redirect_to_start(client):
    url = reverse(
        'enrolment-sole-trader', kwargs={'step': views.COMPANY_SEARCH}
    )
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('enrolment-business-type')


def test_sole_trader_enrolment_submit_end_to_end_logged_in(
    client, submit_sole_trader_step, mock_session_user, steps_data,
    mock_enrolment_send
):
    mock_session_user.login()

    url = reverse('enrolment-sole-trader', kwargs={'step': views.USER_ACCOUNT})
    response = client.get(url)

    assert response.status_code == 302

    response = submit_sole_trader_step(
        {
            'company_name': 'Test company',
            'postal_code': 'EEA 3AD',
            'address': '555 fake street, London',
        },
        step_name=resolve(response.url).kwargs['step'],
    )

    assert response.status_code == 302

    response = submit_sole_trader_step(
        {
            'company_name': 'Test company',
            'postal_code': 'EEA 3AD',
            'address': '555 fake street, London',
            'industry': 'AEROSPACE',
        },
        step_name=resolve(response.url).kwargs['step']
    )
    assert response.status_code == 302

    response = submit_sole_trader_step(
        steps_data[views.PERSONAL_INFO],
        step_name=resolve(response.url).kwargs['step']
    )
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 200
    assert response.template_name == 'enrolment/success-sole-trader.html'
    assert mock_enrolment_send.call_count == 1
    assert mock_enrolment_send.call_args == mock.call({
        'sso_id': '123',
        'company_email': 'test@a.com',
        'contact_email_address': 'test@a.com',
        'company_name': 'Test company',
        'postal_code': 'EEA 3AD',
        'address_line_1': '555 fake street',
        'address_line_2': 'London',
        'industry': 'AEROSPACE',
        'given_name': 'Foo',
        'family_name': 'Example',
        'job_title': 'Exampler',
        'phone_number': '1232342',
        'company_type': 'SOLE_TRADER',
    })


@pytest.mark.parametrize(
    'step', [name for name, _ in views.SoleTraderEnrolmentView.form_list]
)
def test_sole_trader_enrolment_has_company(
    client, step, mock_user_has_company, mock_session_user
):
    mock_session_user.login()

    mock_user_has_company.return_value = create_response(200)

    url = reverse('enrolment-sole-trader', kwargs={'step': step})
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('about')


@pytest.mark.parametrize(
    'step', [name for name, _ in views.SoleTraderEnrolmentView.form_list]
)
def test_sole_trader_enrolment_has_company_error(
    client, step, mock_user_has_company, mock_session_user
):
    mock_session_user.login()

    mock_user_has_company.return_value = create_response(500)

    url = reverse('enrolment-sole-trader', kwargs={'step': step})

    with pytest.raises(HTTPError):
        client.get(url)


def test_sole_trader_search_address_not_found_url(
    submit_sole_trader_step, mock_session_user, client, steps_data
):
    response = submit_sole_trader_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_sole_trader_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()
    response = client.get(response.url)

    not_found_url = constants_url.build_great_url(
        'contact/triage/great-account/sole-trader-address-not-found/'
    )
    assert response.context_data['address_not_found_url'] == not_found_url
