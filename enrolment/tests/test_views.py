from unittest import mock

from formtools.wizard.views import NamedUrlSessionWizardView
from freezegun import freeze_time
import pytest
from requests.exceptions import HTTPError

from django.urls import resolve, reverse
from django.views.generic import TemplateView

from core.tests.helpers import create_response, submit_step_factory

from enrolment import constants, forms, helpers, views
from directory_constants.constants import urls as constants_url
from django.contrib.sessions.backends import signed_cookies


urls = (
    reverse('enrolment-business-type'),
    reverse('enrolment-start'),
    reverse('enrolment-companies-house', kwargs={'step': views.USER_ACCOUNT}),
    reverse('enrolment-sole-trader', kwargs={'step': views.USER_ACCOUNT}),
)
company_types = (constants.COMPANIES_HOUSE_COMPANY, constants.SOLE_TRADER)


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
def submit_pre_verified_step(client):
    return submit_step_factory(
        client=client,
        url_name='enrolment-pre-verified',
        view_name='pre_verified_enrolment_view',
        view_class=views.PreVerifiedEnrolmentView,
    )


@pytest.fixture
def submit_step_builder(submit_companies_house_step, submit_sole_trader_step):
    def inner(choice):
        if choice == constants.COMPANIES_HOUSE_COMPANY:
            return submit_companies_house_step
        elif choice == constants.SOLE_TRADER:
            return submit_sole_trader_step
    return inner


@pytest.fixture
def submit_resend_verification_house_step(client):
    return submit_step_factory(
        client=client,
        url_name='resend-verification',
        view_name='resend_verification_code_view',
        view_class=views.ResendVerificationCodeView,
    )


@pytest.fixture
def preverified_company_data():
    return {
        'address_line_1': '23 Example lane',
        'address_line_2': 'Example land',
        'company_type': 'COMPANIES_HOUSE',
        'name': 'Example corp',
        'number': '1234567',
        'po_box': '',
        'postal_code': 'EE3 3EE',
    }


@pytest.fixture(autouse=True)
def mock_retrieve_preverified_company(preverified_company_data):
    patch = mock.patch.object(
        helpers.api_client.enrolment, 'retrieve_prepeveried_company',
        return_value=create_response(200, preverified_company_data)
    )
    yield patch.start()
    patch.stop()


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
        'company_status': 'active',
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
def mock_claim_company(client):
    patch = mock.patch.object(
        helpers.api_client.enrolment, 'claim_prepeveried_company',
        return_value=create_response(200)
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
def mock_create_user_profile():
    response = create_response(200, {
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'job_title': 'Director',
        'mobile_phone_number': '08888888888',
    })
    patch = mock.patch.object(
        helpers.sso_api_client.user, 'create_user_profile',
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
    response.headers['set-cookie'] = (
        'debug_sso_session_cookie=foo-bar; '
        'Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; '
        'HttpOnly; '
        'Max-Age=1209600; '
        'Path=/; '
        'Secure, '
        'sso_display_logged_in=true; '
        'Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; '
        'Max-Age=1209600; '
        'Path=/'
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_regenerate_verification_code():
    response = create_response(200, {
        'code': '12345',
        'expiration_date': '2018-01-17T12:00:01Z'
    })
    patch = mock.patch.object(
        helpers.sso_api_client.user, 'regenerate_verification_code',
        return_value=response
    )
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
        },
        views.VERIFICATION: {
            'code': '12345',
        },
        views.RESEND_VERIFICATION: {
            'email': 'test@a.com',
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


@pytest.fixture
def session_client_company_factory(client, settings):

    def session_client(company_choice):
        session = signed_cookies.SessionStore()
        session.save()
        session[views.SESSION_KEY_COMPANY_CHOICE] = company_choice
        session.save()
        client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        return client
    return session_client


@pytest.fixture
def session_client_referrer_factory(client, settings):

    def session_client(referrer_url):
        session = signed_cookies.SessionStore()
        session.save()
        session[views.SESSION_KEY_REFERRER] = referrer_url
        session.save()
        client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        return client
    return session_client


@pytest.mark.parametrize('choice,expected_url', (
    (
        constants.COMPANIES_HOUSE_COMPANY,
        views.URL_COMPANIES_HOUSE_ENROLMENT
    ),
    (
        constants.SOLE_TRADER,
        views.URL_SOLE_TRADER_ENROLMENT
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
        'sectors': 'AEROSPACE',
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
        'sectors': 'AEROSPACE',
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
        'sectors': 'AEROSPACE',
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
        'sectors': ['AEROSPACE'],
        'website': ''
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
    mock_enrolment_send, steps_data, session_client_referrer_factory
):
    session_client_referrer_factory(constants_url.SERVICES_FAB)
    response = submit_companies_house_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_companies_house_step(steps_data[views.COMPANY_SEARCH])
    assert response.status_code == 302

    response = submit_companies_house_step({
        'company_name': 'Example corp',
        'sectors': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = submit_companies_house_step(steps_data[views.PERSONAL_INFO])
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 200
    assert response.context_data['fab_referrer'] is True
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
        'sectors': ['AEROSPACE'],
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
        'sectors': 'AEROSPACE',
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
        'sectors': ['AEROSPACE'],
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
        'sectors': 'AEROSPACE',
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


def test_verification_missing_url(
    submit_companies_house_step, mock_session_user, client, steps_data
):
    response = submit_companies_house_step(steps_data[views.USER_ACCOUNT])
    response = client.get(response.url)

    verification_missing_url = constants_url.build_great_url(
        'contact/triage/great-account/verification-missing/'
    )

    assert response.context_data[
               'verification_missing_url'
           ] == verification_missing_url


def test_disable_select_company(client, settings):
    settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON'] = False

    url = reverse('enrolment-business-type')
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse(
        'enrolment-companies-house', kwargs={'step': 'user-account'}
    )

    response = client.get(response.url)
    assert response.status_code == 200


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
        'Set-Cookie: debug_sso_session_cookie=foo-bar; Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; HttpOnly; Max-Age=1209600; '
        'Path=/; Secure'
    )
    assert str(response.cookies['sso_display_logged_in']) == (
        'Set-Cookie: sso_display_logged_in=true; Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; Max-Age=1209600; Path=/'
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

    assert response.status_code == 302

    response = client.get(response.url)
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


def test_confirm_user_resend_verification_code(
        mock_regenerate_verification_code,
        mock_send_verification_code_email,
        submit_resend_verification_house_step,
        steps_data,
):
    response = submit_resend_verification_house_step(
        steps_data[views.RESEND_VERIFICATION]
    )
    assert response.status_code == 302

    assert mock_regenerate_verification_code.call_count == 1
    assert mock_regenerate_verification_code.call_args == mock.call({
        'email': 'test@a.com',
    })

    assert mock_send_verification_code_email.call_count == 1
    assert mock_send_verification_code_email.call_args == mock.call(
        email='test@a.com',
        form_url='/profile/enrol/resend-verification/resend/',
        verification_code={
            'code': '12345', 'expiration_date': '2018-01-17T12:00:01Z'
        },
    )


def test_confirm_user_resend_verification_code_user_verified(
        mock_regenerate_verification_code,
        mock_send_verification_code_email,
        submit_resend_verification_house_step,
        steps_data,
):

    mock_regenerate_verification_code.return_value = create_response(404)

    response = submit_resend_verification_house_step(
        steps_data[views.RESEND_VERIFICATION]
    )

    assert response.status_code == 302

    assert mock_regenerate_verification_code.call_count == 1
    assert mock_regenerate_verification_code.call_args == mock.call({
        'email': 'test@a.com',
    })

    assert mock_send_verification_code_email.call_count == 0


def test_confirm_user_resend_verification_code_no_user(
        mock_regenerate_verification_code,
        mock_send_verification_code_email,
        submit_resend_verification_house_step,
        steps_data,
):

    mock_regenerate_verification_code.return_value = create_response(404)

    response = submit_resend_verification_house_step(
        steps_data[views.RESEND_VERIFICATION]
    )

    assert response.status_code == 302

    assert mock_regenerate_verification_code.call_count == 1
    assert mock_regenerate_verification_code.call_args == mock.call({
        'email': 'test@a.com',
    })

    assert mock_send_verification_code_email.call_count == 0


@freeze_time('2012-01-14 12:00:02')
def test_confirm_user_resend_verification_code_complete(
        client,
        submit_resend_verification_house_step,
        steps_data,
):

    response = submit_resend_verification_house_step(
        steps_data[views.RESEND_VERIFICATION]
    )

    assert response.status_code == 302

    response = submit_resend_verification_house_step(
        steps_data[views.VERIFICATION],
        step_name=resolve(response.url).kwargs['step']
    )
    assert response.status_code == 302
    assert response.url == reverse('enrolment-business-type')

    assert str(response.cookies['debug_sso_session_cookie']) == (
        'Set-Cookie: debug_sso_session_cookie=foo-bar; Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; HttpOnly; Max-Age=1209600; '
        'Path=/; Secure'
    )
    assert str(response.cookies['sso_display_logged_in']) == (
        'Set-Cookie: sso_display_logged_in=true; Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; Max-Age=1209600; Path=/'
    )


@freeze_time('2012-01-14 12:00:02')
def test_confirm_user_resend_verification_code_choice_companies_house(
        session_client_company_factory,
        submit_resend_verification_house_step,
        steps_data,
):
    session_client_company_factory(constants.COMPANIES_HOUSE_COMPANY)

    response = submit_resend_verification_house_step(
        steps_data[views.RESEND_VERIFICATION]
    )

    assert response.status_code == 302

    response = submit_resend_verification_house_step(
        steps_data[views.VERIFICATION],
        step_name=resolve(response.url).kwargs['step'],
    )

    assert response.status_code == 302

    assert response.url == reverse(
        'enrolment-companies-house', kwargs={'step': views.USER_ACCOUNT}
    )

    assert str(response.cookies['debug_sso_session_cookie']) == (
        'Set-Cookie: debug_sso_session_cookie=foo-bar; Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; HttpOnly; Max-Age=1209600; '
        'Path=/; Secure'
    )
    assert str(response.cookies['sso_display_logged_in']) == (
        'Set-Cookie: sso_display_logged_in=true; Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; Max-Age=1209600; Path=/'
    )


@freeze_time('2012-01-14 12:00:02')
def test_confirm_user_resend_verification_code_choice_sole_trader(
        session_client_company_factory,
        submit_resend_verification_house_step,
        steps_data,
):
    session_client_company_factory(constants.SOLE_TRADER)

    response = submit_resend_verification_house_step(
        steps_data[views.RESEND_VERIFICATION]
    )

    assert response.status_code == 302

    response = submit_resend_verification_house_step(
        steps_data[views.VERIFICATION],
        step_name=resolve(response.url).kwargs['step'],
    )

    assert response.status_code == 302

    assert response.url == reverse(
        'enrolment-sole-trader', kwargs={'step': views.USER_ACCOUNT}
    )

    assert str(response.cookies['debug_sso_session_cookie']) == (
        'Set-Cookie: debug_sso_session_cookie=foo-bar; Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; HttpOnly; Max-Age=1209600; '
        'Path=/; Secure'
    )
    assert str(response.cookies['sso_display_logged_in']) == (
        'Set-Cookie: sso_display_logged_in=true; Domain=.trade.great; '
        'expires=Thu, 07-Mar-2019 10:17:38 GMT; Max-Age=1209600; Path=/'
    )


def test_confirm_user_resend_verification_logged_in(client, mock_session_user):
    mock_session_user.login()

    url = reverse(
        'resend-verification', kwargs={'step': views.RESEND_VERIFICATION}
    )

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('about')


def test_confirm_user_resend_verification_context_urls(client):
    url = reverse(
        'resend-verification', kwargs={'step': views.RESEND_VERIFICATION}
    )

    response = client.get(url)

    missing_url = constants_url.build_great_url(
        'contact/triage/great-account/verification-missing/'
    )
    contact_url = constants_url.build_great_url(
        'contact/domestic/'
    )

    assert response.status_code == 200
    assert response.context_data['verification_missing_url'] == missing_url
    assert response.context_data['contact_url'] == contact_url


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
        'sectors': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.context_data['company'] == {
        'company_name': 'Test company',
        'postal_code': 'EEA 3AD',
        'address': '555 fake street\nLondon\nEEA 3AD',
        'address_line_1': '555 fake street',
        'address_line_2': 'London',
        'sectors': ['AEROSPACE'],
        'website': ''
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
            'sectors': 'AEROSPACE',
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
        'sectors': ['AEROSPACE'],
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


def test_claim_preverified_no_key(
    client, submit_pre_verified_step, steps_data, mock_session_user
):
    response = submit_pre_verified_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_pre_verified_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    url = reverse(
        'enrolment-pre-verified', kwargs={'step': views.PERSONAL_INFO}
    )
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('enrolment-start')


def test_claim_preverified_bad_key(client, mock_retrieve_preverified_company):
    mock_retrieve_preverified_company.return_value = create_response(404)

    url = reverse('enrolment-pre-verified', kwargs={'step': 'user-account'})
    response = client.get(url, {'key': '123'})

    assert response.status_code == 302
    assert response.url == reverse('enrolment-start')


def test_claim_preverified_exposes_company(
    submit_pre_verified_step, mock_claim_company, client, steps_data,
    mock_session_user, preverified_company_data
):
    url = reverse('enrolment-pre-verified', kwargs={'step': 'user-account'})
    response = client.get(url, {'key': 'some-key'})

    assert response.status_code == 200

    response = submit_pre_verified_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_pre_verified_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    url = reverse(
        'enrolment-pre-verified', kwargs={'step': views.PERSONAL_INFO}
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['company'] == preverified_company_data


def test_claim_preverified_success(
    submit_pre_verified_step, mock_claim_company, client, steps_data,
    mock_session_user
):
    url = reverse('enrolment-pre-verified', kwargs={'step': 'user-account'})
    response = client.get(url, {'key': 'some-key'})

    assert response.status_code == 200

    response = submit_pre_verified_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_pre_verified_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_pre_verified_step(steps_data[views.PERSONAL_INFO])
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 200
    assert response.template_name == 'enrolment/success-pre-verified.html'
    assert mock_claim_company.call_count == 1
    assert mock_claim_company.call_args == mock.call(
        data={'name': 'Foo Example'},
        key='some-key',
        sso_session_id='foo-bar',
    )


def test_claim_preverified_failure(
    submit_pre_verified_step, mock_claim_company, client, steps_data,
    mock_session_user
):
    mock_claim_company.return_value = create_response(400)

    url = reverse('enrolment-pre-verified', kwargs={'step': 'user-account'})
    response = client.get(url, {'key': 'some-key'})

    assert response.status_code == 200

    response = submit_pre_verified_step(steps_data[views.USER_ACCOUNT])
    assert response.status_code == 302

    response = submit_pre_verified_step(steps_data[views.VERIFICATION])
    assert response.status_code == 302

    mock_session_user.login()

    response = submit_pre_verified_step(steps_data[views.PERSONAL_INFO])
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 200
    assert response.template_name == 'enrolment/failure-pre-verified.html'


@pytest.mark.parametrize('is_anon,is_feature_enabled,expected', (
    (
        True,
        True,
        [
            views.PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            views.PROGRESS_STEP_LABEL_USER_ACCOUNT,
            views.PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ]
    ),
    (
        True,
        False,
        [
            views.PROGRESS_STEP_LABEL_USER_ACCOUNT,
            views.PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ]
    ),
    (
        False,
        True,
        [
            views.PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            views.PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
        ],
    ),
    (
        False,
        False,
        [
            views.PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
        ]
    ),
))
def test_steps_list_mixin(
    is_anon, is_feature_enabled, expected, rf, settings
):
    settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON'] = is_feature_enabled

    class TestView(views.StepsListMixin, TemplateView):
        template_name = 'directory_components/base.html'

        steps_list_conf = helpers.StepsListConf(
            form_labels_user=[
                views.PROGRESS_STEP_LABEL_BUSINESS_TYPE,
                views.PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            ],
            form_labels_anon=[
                views.PROGRESS_STEP_LABEL_BUSINESS_TYPE,
                views.PROGRESS_STEP_LABEL_USER_ACCOUNT,
                views.PROGRESS_STEP_LABEL_PERSONAL_INFO,
            ],
        )

    request = rf.get('/')
    request.sso_user = None if is_anon else mock.Mock()
    view = TestView.as_view()

    response = view(request)
    assert response.context_data['step_labels'] == expected


def test_steps_list_mixin_no_business_type(rf, settings):
    settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON'] = False

    class TestView(views.StepsListMixin, TemplateView):
        template_name = 'directory_components/base.html'

        steps_list_conf = helpers.StepsListConf(
            form_labels_user=[
                views.PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            ],
            form_labels_anon=[
                views.PROGRESS_STEP_LABEL_USER_ACCOUNT,
                views.PROGRESS_STEP_LABEL_PERSONAL_INFO,
            ],
        )

    request = rf.get('/')
    request.sso_user = None
    view = TestView.as_view()

    response = view(request)
    assert response.context_data['step_labels'] == [
        views.PROGRESS_STEP_LABEL_USER_ACCOUNT,
        views.PROGRESS_STEP_LABEL_PERSONAL_INFO,
    ]


@pytest.mark.parametrize('is_anon,is_feature_enabled,expected', (
    (True, True, 2),
    (True, False, 1),
    (False, True, 2),
    (False, False, 1),
))
def test_wizard_progress_indicator_mixin(
    is_anon, is_feature_enabled, expected, rf, settings, client
):
    settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON'] = is_feature_enabled

    class TestView(views.ProgressIndicatorMixin, NamedUrlSessionWizardView):
        def get_template_names(self):
            return ['enrolment/user-account-resend-verification.html']

        form_list = (
            (views.USER_ACCOUNT, forms.UserAccount),
            (views.COMPANY_SEARCH, forms.UserAccount),
        )

        progress_conf = helpers.ProgressIndicatorConf(
            step_counter_user={views.USER_ACCOUNT: 2},
            step_counter_anon={views.USER_ACCOUNT: 2},
            first_step=views.USER_ACCOUNT,
        )

    request = rf.get('/')
    request.session = client.session
    request.sso_user = None if is_anon else mock.Mock()
    view = TestView.as_view(
        url_name='enrolment-companies-house'
    )
    response = view(request, step=views.USER_ACCOUNT)

    assert response.context_data['step_number'] == expected


def test_session_referral_mixin_allowed_entry(rf, client):

    class TestView(views.ServicesRefererDetectorMixin, TemplateView):
        template_name = 'enrolment/start.html'

    request = rf.get('/')
    request.session = client.session
    request.META['HTTP_REFERER'] = constants_url.SERVICES_FAB
    view = TestView.as_view()
    view(request)

    assert request.session[
        views.SESSION_KEY_REFERRER
    ] == constants_url.SERVICES_FAB


def test_session_referral_mixin_not_allowed_entry(rf, client):

    class TestView(views.ServicesRefererDetectorMixin, TemplateView):
        template_name = 'enrolment/start.html'

    request = rf.get('/')
    request.session = client.session
    request.META['HTTP_REFERER'] = constants_url.CONTACT_US
    view = TestView.as_view()
    view(request)

    assert request.session.get(views.SESSION_KEY_REFERRER) is None
