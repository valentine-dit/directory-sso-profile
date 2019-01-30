import pytest
from unittest import mock

from django.urls import reverse

from enrolment import constants, helpers, views

urls = (
    reverse('enrolment', kwargs={'step': 'business-type'}),
    reverse('enrolment-success'),
)


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
    steps = iter([name for name, form in view_class.form_list])

    def submit_step(data):
        step_name = next(steps)
        return client.post(
            reverse(url_name, kwargs={'step': step_name}),
            {
                view_name + '-current_step': step_name,
                **{
                    step_name + '-' + key: value
                    for key, value in data.items()
                }
            }
        )
    return submit_step


@mock.patch('captcha.fields.ReCaptchaField.clean')
@mock.patch.object(helpers, 'get_company_profile')
def test_companies_house_enrolment(
    mock_get_company_profile, mock_clean ,client, captcha_stub
):
    mock_get_company_profile.return_value = {
        'company_number': '12345678',
        'company_name': 'Example corp',
        'sic_codes': ['1234'],
        'date_of_creation': '2001-01-20',
        'registered_office_address': {'one': '555', 'two': 'fake street'},
    }

    submit_step = submit_step_factory(
        client=client,
        url_name='enrolment',
        view_name='enrolment_view',
        view_class=views.EnrolmentView,
    )

    response = submit_step({
        'choice': constants.COMPANIES_HOUSE_COMPANY
    })
    assert response.status_code == 302
    import pdb;
    pdb.set_trace()
    response = submit_step({
        'email': 'text@example.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

    response = submit_step({
        'code': '123'
    })
    assert response.status_code == 302

    response = submit_step({
        'company_name': 'Example corp',
        'company_number': '12345678',
    })
    assert response.status_code == 302

    response = submit_step({
        'company_name': 'Example corp',
        'industry': 'AEROSPACE',
    })
    assert response.status_code == 302

    response = submit_step({
        'given_name': 'Foo',
        'family_name': 'Example',
        'job_title': 'Exampler',
        'phone_number': '1232342',
        'confirmed_is_company_representative': True,
        'confirmed_background_checks': True,
    })
    assert response.status_code == 302


@mock.patch('captcha.fields.ReCaptchaField.clean')
def test_new_user_enrolment(mock_clean, client, captcha_stub):
    '''
    mock_create_user.return_value = {
        'email': 'test@test.com',
        'password': '123456',
    }
    '''

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
        'email': 'text2@example.com',
        'password': 'thing',
        'password_confirmed': 'thing',
        'captcha': captcha_stub,
        'terms_agreed': True
    })
    assert response.status_code == 302

