from io import BytesIO
import http
from unittest import mock

from directory_api_client.client import api_client
from formtools.wizard.views import normalize_name
import pytest
from PIL import Image, ImageDraw
from requests.exceptions import HTTPError

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse

from core.tests.helpers import create_response, submit_step_factory
from profile.fab import constants, forms, helpers, views


def create_test_image(extension):
    image = Image.new("RGB", (300, 50))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), "This text is drawn on image")
    byte_io = BytesIO()
    image.save(byte_io, extension)
    byte_io.seek(0)
    return byte_io


@pytest.fixture
def default_company_profile():
    return {
        'name': 'Cool Company',
        'is_publishable': True,
        'expertise_products_services': {},
        'is_identity_check_message_sent': False,
    }


@pytest.fixture
def default_private_case_study(case_study_data):
    return {
        **case_study_data[views.BASIC],
        **case_study_data[views.MEDIA],
        'image_one': 'https://example.com/image-one.png',
        'image_two': 'https://example.com/image-two.png',
        'image_three': 'https://example.com/image-three.png',
    }


@pytest.fixture(autouse=True)
def mock_retrieve_private_case_study(default_private_case_study):
    patch = mock.patch.object(
        api_client.company, 'retrieve_private_case_study',
        return_value=create_response(200, default_private_case_study)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_update_case_study():
    patch = mock.patch.object(
        api_client.company, 'update_case_study',
        return_value=create_response(200)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_create_case_study():
    patch = mock.patch.object(
        api_client.company, 'create_case_study',
        return_value=create_response(201)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_retrieve_company(default_company_profile):
    patch = mock.patch.object(
        api_client.company, 'retrieve_private_profile',
        return_value=create_response(200, default_company_profile)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_update_company(default_company_profile):
    patch = mock.patch.object(
        api_client.company, 'update_profile',
        return_value=create_response(200)
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_retrieve_supplier():
    patch = mock.patch.object(
        api_client.supplier, 'retrieve_profile',
        return_value=create_response(200, {'is_company_owner': True})
    )
    yield patch.start()
    patch.stop()


@pytest.fixture(autouse=True)
def mock_retrieve_collaborators():
    patch = mock.patch.object(
        api_client.company, 'retrieve_collaborators',
        return_value=create_response(200, {'ssoID': '12345'})
    )
    yield patch.start()
    patch.stop()


@pytest.fixture
def submit_case_study_create_step(client):
    return submit_step_factory(
        client=client,
        url_name='find-a-buyer-case-study',
        view_class=views.CaseStudyWizardCreateView,
    )


@pytest.fixture
def submit_case_study_edit_step(client):
    url_name = 'find-a-buyer-case-study-edit'
    view_class = views.CaseStudyWizardEditView
    view_name = normalize_name(view_class.__name__)
    step_names = iter([name for name, form in view_class.form_list])

    def submit_step(data, step_name=None):
        step_name = step_name or next(step_names)
        url = reverse(url_name, kwargs={'step': step_name, 'id': 1})
        response = client.get(url)
        assert response.status_code == 200
        return client.post(
            url,
            {
                view_name + '-current_step': step_name,
                **{step_name + '-' + key: value for key, value in data.items()}
            },
        )
    return submit_step


@pytest.fixture
def case_study_data():
    return {
        views.BASIC: {
            'title': 'Example',
            'description': 'Great',
            'short_summary': 'Nice',
            'sector': 'AEROSPACE',
            'website': 'http://www.example.com',
            'keywords': 'good, great',
        },
        views.MEDIA: {
            'testimonial': 'Great',
            'testimonial_name': 'Neville',
            'testimonial_job_title': 'Abstract hat maker',
            'testimonial_company': 'Imaginary hats Ltd',
            'image_one': SimpleUploadedFile(
                name='image-one.png',
                content=create_test_image('png').read(),
                content_type='image/png',
            ),
            'image_two': SimpleUploadedFile(
                name='image-two.png',
                content=create_test_image('png').read(),
                content_type='image/png',
            ),
            'image_three': None,
            'image_one_caption': 'nice image',
            'image_two_caption': 'thing',
            'image_three_caption': 'thing',
        }
    }


def test_find_a_buyer_exposes_context(client, settings, user):
    client.force_login(user)
    response = client.get(reverse('find-a-buyer'))
    context = response.context_data

    assert context['fab_tab_classes'] == 'active'
    assert context['FAB_EDIT_COMPANY_LOGO_URL'] == (
        settings.FAB_EDIT_COMPANY_LOGO_URL
    )
    assert context['FAB_EDIT_PROFILE_URL'] == settings.FAB_EDIT_PROFILE_URL
    assert context['FAB_ADD_CASE_STUDY_URL'] == settings.FAB_ADD_CASE_STUDY_URL
    assert context['FAB_REGISTER_URL'] == settings.FAB_REGISTER_URL


def test_find_a_buyer_unauthenticated_enrolment(client, settings):
    profile_url = reverse('find-a-buyer')
    enrolment_url = reverse('enrolment-start')
    response = client.get(profile_url)

    assert response.status_code == http.client.FOUND
    assert response.url == f'{enrolment_url}?next={profile_url}'


def test_supplier_company_retrieve_found_business_profile_on(
    mock_retrieve_company, client, settings,
    default_company_profile, user
):
    client.force_login(user)
    mock_retrieve_company.return_value = create_response(
        200, default_company_profile
    )

    response = client.get(reverse('find-a-buyer'))

    assert response.template_name == ['fab/profile.html']


def test_company_owner(client, user):
    client.force_login(user)
    response = client.get(reverse('find-a-buyer'))

    assert response.context_data['is_profile_owner'] is True


def test_non_company_owner(mock_retrieve_supplier, client, user):
    client.force_login(user)
    mock_retrieve_supplier.return_value = create_response(
        200, {'is_company_owner': False}
    )
    response = client.get(reverse('find-a-buyer'))

    assert response.context_data['is_profile_owner'] is False


@pytest.mark.parametrize('param', (
    'owner-transferred', 'user-added', 'user-removed'
))
def test_success_message(
    mock_retrieve_supplier, client, param, user
):
    client.force_login(user)
    mock_retrieve_supplier.return_value = create_response(
        200, {'is_company_owner': False}
    )

    url = reverse('find-a-buyer')
    response = client.get(url, {param: True})
    for message in response.context['messages']:
        assert str(message) == views.FindABuyerView.SUCCESS_MESSAGES[param]


edit_urls = (
    reverse('find-a-buyer-description'),
    reverse('find-a-buyer-email'),
    reverse('find-a-buyer-social'),
    reverse('find-a-buyer-website'),
    reverse('find-a-buyer-expertise-regional'),
    reverse('find-a-buyer-expertise-countries'),
    reverse('find-a-buyer-expertise-industries'),
    reverse('find-a-buyer-expertise-languages'),
)

edit_data = (
    {'description': 'A description', 'summary': 'A summary'},
    {'email_address': 'email@example.com'},
    {
        'facebook_url': 'https://www.facebook.com/thing/',
        'twitter_url': 'https://www.twitter.com/thing/',
        'linkedin_url': 'https://www.linkedin.com/thing/',
    },
    {'website': 'https://www.mycompany.com/'},
    {'expertise_regions': ['WEST_MIDLANDS']},
    {'expertise_countries': ['AL']},
    {'expertise_industries': ['POWER']},
    {'expertise_languages': ['ab']},
)


@pytest.mark.parametrize('url', edit_urls)
def test_edit_page_initial_data(
    client, url, default_company_profile, user
):
    client.force_login(user)
    company = helpers.CompanyParser(default_company_profile)

    response = client.get(url)
    assert response.context_data['form'].initial == (
        company.serialize_for_form()
    )


success_urls = (
    reverse('find-a-buyer'),
    reverse('find-a-buyer'),
    reverse('find-a-buyer'),
    reverse('find-a-buyer'),
    reverse('find-a-buyer-expertise-routing'),
    reverse('find-a-buyer-expertise-routing'),
    reverse('find-a-buyer-expertise-routing'),
    reverse('find-a-buyer-expertise-routing'),
)


@pytest.mark.parametrize(
    'url,data,success_url', zip(edit_urls, edit_data, success_urls)
)
def test_edit_page_submmit_success(
    client, mock_update_company, user, url, data, success_url
):
    client.force_login(user)
    response = client.post(url, data)

    assert response.status_code == 302
    assert response.url == success_url
    assert mock_update_company.call_count == 1
    assert mock_update_company.call_args == mock.call(
        sso_session_id=user.session_id,
        data=data
    )


def test_publish_not_publishable(
    client, user, mock_retrieve_company,
    default_company_profile
):
    client.force_login(user)
    mock_retrieve_company.return_value = create_response(
        200,
        {**default_company_profile, 'is_publishable': False}
    )

    url = reverse('find-a-buyer-publish')

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')


def test_publish_publishable(client, user, mock_retrieve_company):
    client.force_login(user)
    url = reverse('find-a-buyer-publish')

    response = client.get(url)

    assert response.status_code == 200


def test_edit_page_submmit_publish_success(client, mock_update_company, user):
    client.force_login(user)
    url = reverse('find-a-buyer-publish')
    data = {
        'is_published_investment_support_directory': True,
        'is_published_find_a_supplier': True,
    }
    response = client.post(url, data)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_update_company.call_count == 1
    assert mock_update_company.call_args == mock.call(
        sso_session_id=user.session_id,
        data=data
    )


def test_edit_page_submmit_publish_context(
    client, default_company_profile, user
):
    client.force_login(user)
    company = helpers.CompanyParser(default_company_profile)

    url = reverse('find-a-buyer-publish')
    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['company'] == company.serialize_for_template()


def test_edit_page_logo_submmit_success(client, mock_update_company, user):
    client.force_login(user)
    url = reverse('find-a-buyer-logo')
    data = {
        'logo': SimpleUploadedFile(
            name='image.png',
            content=create_test_image('png').read(),
            content_type='image/png',
        )
    }

    response = client.post(url, data)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_update_company.call_count == 1
    assert mock_update_company.call_args == mock.call(
        sso_session_id=user.session_id,
        data={'logo': mock.ANY}
    )


@pytest.mark.parametrize('url,data', zip(edit_urls, edit_data))
def test_edit_page_submmit_error(
    client, mock_update_company, url, data, user
):
    client.force_login(user)
    mock_update_company.return_value = create_response(400)

    with pytest.raises(HTTPError):
        client.post(url, data)


def test_case_study_create(
    submit_case_study_create_step, mock_create_case_study, case_study_data,
    client, user
):
    client.force_login(user)

    response = submit_case_study_create_step(case_study_data[views.BASIC])
    assert response.status_code == 302

    response = submit_case_study_create_step(case_study_data[views.MEDIA])
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.url == reverse('find-a-buyer')

    assert mock_create_case_study.call_count == 1


def test_case_study_edit_foo(
    submit_case_study_edit_step, mock_retrieve_private_case_study, client,
    mock_update_case_study, case_study_data,
    default_private_case_study, user, rf
):
    client.force_login(user)

    response = submit_case_study_edit_step(case_study_data[views.BASIC])
    assert response.status_code == 302

    response = submit_case_study_edit_step(case_study_data[views.MEDIA])
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.url == reverse('find-a-buyer')
    assert mock_update_case_study.call_count == 1
    data = {
        **default_private_case_study,
        'image_one': mock.ANY,
        'image_two': mock.ANY,
    }
    del data['image_three']

    assert mock_update_case_study.call_args == mock.call(
        case_study_id='1',
        data=data,
        sso_session_id='123'
    )


def test_case_study_edit_not_found(
    mock_retrieve_private_case_study, client, user
):
    mock_retrieve_private_case_study.return_value = create_response(404)

    client.force_login(user)
    url = reverse(
        'find-a-buyer-case-study-edit', kwargs={'id': '1', 'step': views.BASIC}
    )

    response = client.get(url)

    assert response.status_code == 404


def test_case_study_edit_found(
    mock_retrieve_private_case_study, client, user
):
    client.force_login(user)
    url = reverse(
        'find-a-buyer-case-study-edit', kwargs={'id': '1', 'step': views.BASIC}
    )

    response = client.get(url)

    assert response.status_code == 200


def test_admin_tools(settings, client, default_company_profile, user):
    client.force_login(user)

    company = helpers.CompanyParser(default_company_profile)

    url = reverse('find-a-buyer-admin-tools')

    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['FAB_ADD_USER_URL'] == (
        settings.FAB_ADD_USER_URL
    )
    assert response.context_data['FAB_REMOVE_USER_URL'] == (
        settings.FAB_REMOVE_USER_URL
    )
    assert response.context_data['FAB_TRANSFER_ACCOUNT_URL'] == (
        settings.FAB_TRANSFER_ACCOUNT_URL
    )
    assert response.context_data['has_collaborators'] is True
    assert response.context_data['company'] == company.serialize_for_template()


def test_admin_tools_no_collaborators(
    settings, client, mock_retrieve_collaborators, user
):
    client.force_login(user)

    mock_retrieve_collaborators.return_value = create_response(200, {})

    url = reverse('find-a-buyer-admin-tools')
    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['has_collaborators'] is False


def test_business_details_sole_trader(
    settings, mock_retrieve_company, client, user
):
    client.force_login(user)
    mock_retrieve_company.return_value = create_response(
        200, {'company_type': 'SOLE_TRADER'}
    )

    url = reverse('find-a-buyer-business-details')

    response = client.get(url)

    assert response.status_code == 200
    assert isinstance(
        response.context_data['form'],
        forms.NonCompaniesHouseBusinessDetailsForm
    )


def test_business_details_companies_house(
    settings, client, mock_retrieve_company, user
):
    client.force_login(user)
    mock_retrieve_company.return_value = create_response(
        200, {'company_type': 'COMPANIES_HOUSE'}
    )

    url = reverse('find-a-buyer-business-details')

    response = client.get(url)

    assert response.status_code == 200
    assert isinstance(
        response.context_data['form'], forms.CompaniesHouseBusinessDetailsForm
    )


@pytest.mark.parametrize('choice,expected_url', (
    (
        forms.ExpertiseRoutingForm.REGION,
        reverse('find-a-buyer-expertise-regional')
    ),
    (
        forms.ExpertiseRoutingForm.COUNTRY,
        reverse('find-a-buyer-expertise-countries'),
    ),
    (
        forms.ExpertiseRoutingForm.INDUSTRY,
        reverse('find-a-buyer-expertise-industries'),
    ),
    (
        forms.ExpertiseRoutingForm.LANGUAGE,
        reverse('find-a-buyer-expertise-languages'),
    ),
))
def test_add_expertise_routing(settings, choice, expected_url, client, user):
    client.force_login(user)
    settings.FEATURE_FLAGS['EXPERTISE_FIELDS_ON'] = True

    url = reverse('find-a-buyer-expertise-routing')

    response = client.post(url, {'choice': choice})

    assert response.status_code == 302
    assert response.url == expected_url


def test_expertise_routing_form(client, settings, user):
    client.force_login(user)
    url = reverse('find-a-buyer-expertise-routing')

    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['company']


def test_expertise_products_services_routing_form_context(
    client, settings, default_company_profile, user
):
    client.force_login(user)

    company = helpers.CompanyParser(default_company_profile)

    url = reverse('find-a-buyer-expertise-products-services-routing')

    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['company'] == company.serialize_for_template()


@pytest.mark.parametrize('choice', (
    item for item, _ in forms.ExpertiseProductsServicesRoutingForm.CHOICES if item
))
def test_expertise_products_services_routing_form(
    choice, client, settings, user
):
    client.force_login(user)

    url = reverse('find-a-buyer-expertise-products-services-routing')

    response = client.post(url, {'choice': choice})

    assert response.url == reverse(
        'find-a-buyer-expertise-products-services',
        kwargs={'category': choice}
    )


def test_products_services_form_prepopulate(
    mock_retrieve_company, default_company_profile, client, user
):
    client.force_login(user)
    mock_retrieve_company.return_value = create_response(
        200,
        {
            **default_company_profile,
            'expertise_products_services': {
                constants.LEGAL: [
                    'Company incorporation',
                    'Employment',
                ],
                constants.PUBLICITY: [
                    'Public Relations',
                    'Branding',
                ]
            }
        }
    )

    url = reverse(
        'find-a-buyer-expertise-products-services',
        kwargs={'category': constants.PUBLICITY}
    )
    response = client.get(url)

    assert response.context_data['form'].initial == {
        'expertise_products_services': 'Public Relations|Branding'
    }


def test_products_services_other_form(
    mock_retrieve_company, default_company_profile, client, user
):
    client.force_login(user)
    mock_retrieve_company.return_value = create_response(
        200,
        {
            **default_company_profile,
            'expertise_products_services': {
                constants.LEGAL: [
                    'Company incorporation',
                    'Employment',
                ],
                constants.OTHER: [
                    'Foo',
                    'Bar',
                ]
            }
        }
    )

    url = reverse('find-a-buyer-expertise-products-services-other')
    response = client.get(url)

    assert response.context_data['form'].initial == {
        'expertise_products_services': 'Foo, Bar'
    }


def test_products_services_other_form_update(
    client, mock_retrieve_company, mock_update_company, user,
    default_company_profile
):
    client.force_login(user)
    mock_retrieve_company.return_value = create_response(
        200,
        {
            **default_company_profile,
            'expertise_products_services': {
                constants.LEGAL: [
                    'Company incorporation',
                    'Employment',
                ],
                constants.OTHER: [
                    'Foo',
                    'Bar',
                ]
            }
        }
    )

    url = reverse('find-a-buyer-expertise-products-services-other')

    client.post(
        url,
        {'expertise_products_services': 'Baz,Zad'}
    )

    assert mock_update_company.call_count == 1
    assert mock_update_company.call_args == mock.call(
        data={
            'expertise_products_services': {
                constants.LEGAL: [
                    'Company incorporation',
                    'Employment',
                ],
                constants.OTHER: ['Baz', 'Zad']
            }
        },
        sso_session_id='123'
    )


def test_products_services_form_update(
    client, mock_retrieve_company, mock_update_company, user,
    default_company_profile
):
    client.force_login(user)
    mock_retrieve_company.return_value = create_response(
        200,
        {
            **default_company_profile,
            'expertise_products_services': {
                constants.LEGAL: [
                    'Company incorporation',
                    'Employment',
                ],
                constants.PUBLICITY: [
                    'Public Relations',
                    'Branding',
                ]
            }
        }
    )

    url = reverse(
        'find-a-buyer-expertise-products-services',
        kwargs={'category': constants.PUBLICITY}
    )
    client.post(
        url,
        {'expertise_products_services': ['Social Media']}
    )

    assert mock_update_company.call_count == 1
    assert mock_update_company.call_args == mock.call(
        data={
            'expertise_products_services': {
                constants.LEGAL: [
                    'Company incorporation',
                    'Employment'
                ],
                constants.PUBLICITY: ['Social Media']
            }
        },
        sso_session_id='123'
    )


def test_products_services_exposes_category(client, user):
    client.force_login(user)

    url = reverse(
        'find-a-buyer-expertise-products-services',
        kwargs={'category': constants.BUSINESS_SUPPORT}
    )
    response = client.get(url)

    assert response.context_data['category'] == 'business support'


def test_personal_details(client, mock_create_user_profile, user):
    client.force_login(user)

    data = {
        'given_name': 'Foo',
        'family_name': 'Example',
        'job_title': 'Exampler',
        'phone_number': '1232342',
        'confirmed_is_company_representative': True,
        'terms_agreed': True,
    }
    response = client.post(reverse('find-a-buyer-personal-details'), data)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_create_user_profile.call_count == 1
    assert mock_create_user_profile.call_args == mock.call(
        sso_session_id=user.session_id,
        data={
            'first_name': 'Foo',
            'last_name': 'Example',
            'job_title': 'Exampler',
            'mobile_phone_number': '1232342'
        }
    )


@mock.patch.object(api_client.company, 'verify_identity_request')
def test_request_identity_verification(mock_verify_identity_request, client, user):
    mock_verify_identity_request.return_value = create_response()

    client.force_login(user)

    url = reverse('find-a-buyer-request-to-verify')

    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_verify_identity_request.call_count == 1
    assert mock_verify_identity_request.call_args == mock.call(sso_session_id=user.session_id)

    response = client.get(response.url)
    assert response.status_code == 200
    for message in response.context['messages']:
        assert str(message) == views.IdentityVerificationRequestFormView.success_message


@mock.patch.object(api_client.company, 'verify_identity_request')
def test_request_identity_verification_already_sent(mock_verify_identity_request, client, user):
    user.company.data['is_identity_check_message_sent'] = True
    client.force_login(user)

    url = reverse('find-a-buyer-request-to-verify')

    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_verify_identity_request.call_count == 0


@mock.patch.object(api_client.company, 'verify_identity_request')
def test_request_identity_verification_feature_off(mock_verify_identity_request, client, user, settings):
    settings.FEATURE_FLAGS['REQUEST_VERIFICATION_ON'] = False
    user.company.data['is_identity_check_message_sent'] = False
    client.force_login(user)

    url = reverse('find-a-buyer-request-to-verify')

    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_verify_identity_request.call_count == 0
