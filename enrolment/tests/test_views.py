from unittest import mock

from freezegun import freeze_time
import pytest
from requests.cookies import RequestsCookieJar
from requests.exceptions import HTTPError

from django.urls import resolve, reverse

from core.tests.helpers import create_response
from enrolment import constants, helpers, views


urls = (
    reverse('enrolment', kwargs={'step': 'business-type'}),
    reverse('enrolment-success'),
)


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
def mock_retrieve_public_profile(client):
    patch = mock.patch.object(
        helpers.api_client.company, 'retrieve_public_profile',
        return_value=create_response(404)
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
    mock_clean, client, captcha_stub, submit_enrolment_step, mock_session_user
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '12345'
    })
    assert response.status_code == 302

    mock_session_user.login()

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
    mock_clean, client, captcha_stub, submit_enrolment_step, mock_session_user
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '12345'
    })
    assert response.status_code == 302

    mock_session_user.login()

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
def test_create_user_enrolment(mock_clean, client, captcha_stub):
    submit_step = submit_step_factory(
        client=client,
        url_name='enrolment',
        view_name='enrolment_view',
        view_class=views.EnrolmentView,
    )

    response = submit_step({
        'choice': constants.SOLE_TRADER
    })
    assert response.status_code == 302

    response = submit_step({
        'email': 'tex4566eqw34e7@example.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_create_user_enrolment_already_exists(
        mock_clean, client, captcha_stub, mock_create_user,
        mock_notify_already_registered
):
    submit_step = submit_step_factory(
        client=client,
        url_name='enrolment',
        view_name='enrolment_view',
        view_class=views.EnrolmentView,
    )

    response = submit_step({
        'choice': constants.SOLE_TRADER
    })
    assert response.status_code == 302
    mock_create_user.return_value = create_response(400)

    response = submit_step({
        'email': 'tex4566eqw34e7@example.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302
    assert mock_notify_already_registered.call_count == 1
    assert mock_notify_already_registered.call_args == mock.call(
        email='tex4566eqw34e7@example.com',
        from_url='/profile/enrol/user-account/'
    )


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_companies_house_enrolment_expose_company(
    mock_clean, client, captcha_stub, submit_enrolment_step, mock_session_user
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '12345'
    })
    assert response.status_code == 302

    mock_session_user.login()

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
        'date_of_creation': '2001-01-01',
        'postal_code': 'EDG 4DF',
        'address': '555 fake street, London',
        'address_line_1': '555 fake street',
        'address_line_2': 'London',
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


@freeze_time('2012-01-14 12:00:02')
@mock.patch('captcha.fields.ReCaptchaField.clean', mock.Mock)
def test_companies_house_verification_passes_cookies(
    submit_enrolment_step, client, captcha_stub
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '12345'
    })
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


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_companies_house_enrolment_submit_end_to_end(
    mock_clean, client, captcha_stub, submit_enrolment_step, mock_session_user,
    mock_enrolment_send
):
    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '12345'
    })
    assert response.status_code == 302

    mock_session_user.login()

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
        'family_name': 'Bar',
        'job_title': 'Fooer',
        'phone_number': '1234567',
        'confirmed_is_company_representative': True,
        'confirmed_background_checks': True,
    })
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.url == reverse('enrolment-success')
    assert mock_enrolment_send.call_count == 1
    assert mock_enrolment_send.call_args == mock.call({
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
        'website_address': '',
        'given_name': 'Foo',
        'family_name': 'Bar',
        'job_title': 'Fooer',
        'phone_number': '1234567',
        'sso_id': '123'
    })


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_confirm_user_verify_code_incorrect_code(
    mock_clean, client, captcha_stub, submit_enrolment_step,
    mock_session_user, mock_confirm_verification_code
):
    mock_session_user.return_value = create_response(404)
    mock_confirm_verification_code.return_value = create_response(400)

    response = submit_enrolment_step({
        'choice': constants.SOLE_TRADER
    })

    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '12345',
    })

    assert response.status_code == 200
    assert response.context_data['form'].errors['code'] == ['Invalid code']


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_confirm_user_verify_code_remote_error(
    mock_clean, client, captcha_stub, submit_enrolment_step,
    mock_session_user, mock_confirm_verification_code
):
    mock_session_user.return_value = create_response(404)
    mock_confirm_verification_code.return_value = create_response(500)

    response = submit_enrolment_step({
        'choice': constants.SOLE_TRADER
    })

    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    with pytest.raises(HTTPError):
        submit_enrolment_step({'code': '12345'})


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_confirm_user_verify_code(
    mock_clean, client, captcha_stub, submit_enrolment_step,
    mock_session_user, mock_confirm_verification_code
):
    mock_session_user.return_value = create_response(404)

    response = submit_enrolment_step({
        'choice': constants.SOLE_TRADER
    })

    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '12345',
    })

    mock_session_user.login()

    assert response.status_code == 302
    assert mock_confirm_verification_code.call_count == 1
    assert mock_confirm_verification_code.call_args == mock.call({
        'email': 'test@a.com', 'code': '12345'
    })


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_companies_house_enrolment_submit_end_to_end_logged_in(
    mock_clean, client, captcha_stub, submit_enrolment_step, mock_session_user,
    mock_enrolment_send
):
    mock_session_user.login()

    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302
    step = resolve(response.url).kwargs['step']

    assert step == views.EnrolmentView.COMPANY_SEARCH

    response = submit_enrolment_step({
        'company_name': 'Example corp',
        'company_number': '12345678',
    }, step_name=step)

    assert response.status_code == 302

    step = resolve(response.url).kwargs['step']
    response = submit_enrolment_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    }, step_name=step)
    assert response.status_code == 302

    step = resolve(response.url).kwargs['step']
    response = submit_enrolment_step({
        'given_name': 'Foo',
        'family_name': 'Bar',
        'job_title': 'Fooer',
        'phone_number': '1234567',
        'confirmed_is_company_representative': True,
        'confirmed_background_checks': True,
    }, step_name=step)
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.url == reverse('enrolment-success')
    assert mock_enrolment_send.call_count == 1
    assert mock_enrolment_send.call_args == mock.call({
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
        'website_address': '',
        'given_name': 'Foo',
        'family_name': 'Bar',
        'job_title': 'Fooer',
        'phone_number': '1234567',
        'sso_id': '123'
    })


@pytest.mark.parametrize(
    'step', [name for name, _ in views.EnrolmentView.form_list]
)
def test_companies_house_enrolment_has_company(
    client, step, mock_user_has_company, mock_session_user
):
    mock_session_user.login()

    mock_user_has_company.return_value = create_response(200)

    url = reverse('enrolment', kwargs={'step': step})
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('about')


@pytest.mark.parametrize(
    'step', [name for name, _ in views.EnrolmentView.form_list]
)
def test_companies_house_enrolment_has_company_error(
    client, step, mock_user_has_company, mock_session_user
):
    mock_session_user.login()

    mock_user_has_company.return_value = create_response(500)

    url = reverse('enrolment', kwargs={'step': step})

    with pytest.raises(HTTPError):
        client.get(url)


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_companies_house_enrolment_submit_end_to_end_company_has_account(
    mock_clean, client, captcha_stub, submit_enrolment_step, mock_session_user,
    mock_enrolment_send, mock_retrieve_public_profile
):
    mock_retrieve_public_profile.return_value = create_response(200)

    response = submit_enrolment_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'email': 'test@a.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_enrolment_step({
        'code': '12345'
    })
    assert response.status_code == 302

    mock_session_user.login()

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
        'family_name': 'Bar',
        'job_title': 'Fooer',
        'phone_number': '1234567',
        'confirmed_is_company_representative': True,
        'confirmed_background_checks': True,
    })
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.url == reverse('enrolment-success')
    assert mock_enrolment_send.call_count == 0
