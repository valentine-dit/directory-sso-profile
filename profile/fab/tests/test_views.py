from io import BytesIO
import http
from unittest import mock

from directory_api_client.client import api_client
import pytest
from PIL import Image, ImageDraw
from requests.exceptions import HTTPError

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse

from core.tests.helpers import create_response, submit_step_factory
from profile.fab import forms, helpers, views


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
    return {'name': 'Cool Company', 'is_publishable': True}


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


@pytest.fixture
def submit_case_study_create_step(client):
    return submit_step_factory(
        client=client,
        url_name='find-a-buyer-case-study',
        view_name='case_study_wizard_create_view',
        view_class=views.CaseStudyWizardCreateView,
    )


@pytest.fixture
def submit_case_study_edit_step(client):
    url_name = 'find-a-buyer-case-study-edit'
    view_name = 'case_study_wizard_edit_view'
    view_class = views.CaseStudyWizardEditView
    step_names = iter([name for name, form in view_class.form_list])

    def submit_step(data, step_name=None):
        step_name = step_name or next(step_names)
        return client.post(
            reverse(url_name, kwargs={'step': step_name, 'id': 1}),
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


def test_find_a_buyer_exposes_context(
    returned_client, sso_user_middleware, settings
):
    response = returned_client.get(reverse('find-a-buyer'))
    context = response.context_data

    assert context['fab_tab_classes'] == 'active'
    assert context['FAB_EDIT_COMPANY_LOGO_URL'] == (
        settings.FAB_EDIT_COMPANY_LOGO_URL
    )
    assert context['FAB_EDIT_PROFILE_URL'] == settings.FAB_EDIT_PROFILE_URL
    assert context['FAB_ADD_CASE_STUDY_URL'] == settings.FAB_ADD_CASE_STUDY_URL
    assert context['FAB_REGISTER_URL'] == settings.FAB_REGISTER_URL


def test_find_a_buyer_unauthenticated(
    sso_user_middleware_unauthenticated, returned_client, settings
):
    settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_ON'] = False

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.status_code == http.client.FOUND

    assert response.url == (
        'http://sso.trade.great:8004/accounts/login/'
        '?next=http%3A//testserver/profile/find-a-buyer/'
    )


def test_find_a_buyer_unauthenticated_enrolment(
    sso_user_middleware_unauthenticated, returned_client, settings
):
    settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_ON'] = True

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.status_code == http.client.FOUND
    assert response.url == reverse('enrolment-start')


def test_supplier_company_retrieve_not_found(
    mock_retrieve_company, sso_user_middleware, returned_client, settings
):
    settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON'] = False

    mock_retrieve_company.return_value = create_response(404)
    expected_template_name = views.FindABuyerView.template_name_not_fab_user

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]


def test_supplier_company_retrieve_found(
    mock_retrieve_company, sso_user_middleware, returned_client, settings
):
    settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON'] = False

    mock_retrieve_company.return_value = create_response(200, {'a': 'b'})
    expected_template_name = views.FindABuyerView.template_name_fab_user

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]


def test_supplier_company_retrieve_found_business_profile_on(
    mock_retrieve_company, sso_user_middleware, returned_client, settings
):
    settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON'] = True

    mock_retrieve_company.return_value = create_response(200, {'a': 'b'})

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.template_name == ['fab/profile.html']


def test_company_owner(sso_user_middleware, returned_client):
    response = returned_client.get(reverse('find-a-buyer'))

    assert response.context_data['is_profile_owner'] is True


def test_non_company_owner(
    mock_retrieve_supplier, sso_user_middleware, returned_client
):
    mock_retrieve_supplier.return_value = create_response(
        200, {'is_company_owner': False}
    )
    response = returned_client.get(reverse('find-a-buyer'))

    assert response.context_data['is_profile_owner'] is False


@pytest.mark.parametrize('param', (
    'owner-transferred', 'user-added', 'user-removed'
))
def test_success_message(
    mock_retrieve_supplier, sso_user_middleware, returned_client, param
):
    mock_retrieve_supplier.return_value = create_response(
        200, {'is_company_owner': False}
    )

    url = reverse('find-a-buyer')
    response = returned_client.get(url, {param: True})
    for message in response.context['messages']:
        assert str(message) == views.FindABuyerView.SUCCESS_MESSAGES[param]


edit_urls = (
    reverse('find-a-buyer-description'),
    reverse('find-a-buyer-email'),
    reverse('find-a-buyer-social'),
    reverse('find-a-buyer-products-and-services'),
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
    {'keywords': 'foo, bar, baz'},
    {'website': 'https://www.mycompany.com/'},
    {'expertise_regions': ['WEST_MIDLANDS']},
    {'expertise_countries': ['AL']},
    {'expertise_industries': ['POWER']},
    {'expertise_languages': ['ab']},
)


@pytest.mark.parametrize('url', edit_urls)
def test_edit_page_initial_data(
    returned_client, url, default_company_profile, sso_user_middleware
):
    company = helpers.ProfileParser(default_company_profile)

    response = returned_client.get(url)
    assert response.context_data['form'].initial == (
        company.serialize_for_form()
    )


@pytest.mark.parametrize('url,data', zip(edit_urls, edit_data))
def test_edit_page_submmit_success(
    returned_client, mock_update_company, sso_user, url, data,
    sso_user_middleware
):
    response = returned_client.post(url, data)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_update_company.call_count == 1
    assert mock_update_company.call_args == mock.call(
        sso_session_id=sso_user.session_id,
        data=data
    )


def test_publish_not_publishable(
    returned_client, sso_user, sso_user_middleware, mock_retrieve_company,
    default_company_profile
):
    mock_retrieve_company.return_value = create_response(
        200,
        {**default_company_profile, 'is_publishable': False}
    )

    url = reverse('find-a-buyer-publish')

    response = returned_client.get(url)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')


def test_publish_publishable(
    returned_client, sso_user, sso_user_middleware, mock_retrieve_company
):

    url = reverse('find-a-buyer-publish')

    response = returned_client.get(url)

    assert response.status_code == 200


def test_edit_page_submmit_publish_success(
    returned_client, mock_update_company, sso_user, sso_user_middleware
):
    url = reverse('find-a-buyer-publish')
    data = {
        'is_published_investment_support_directory': True,
        'is_published_find_a_supplier': True,
    }
    response = returned_client.post(url, data)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_update_company.call_count == 1
    assert mock_update_company.call_args == mock.call(
        sso_session_id=sso_user.session_id,
        data=data
    )


def test_edit_page_submmit_publish_context(
    returned_client, sso_user_middleware, default_company_profile
):
    company = helpers.ProfileParser(default_company_profile)

    url = reverse('find-a-buyer-publish')
    response = returned_client.get(url)

    assert response.status_code == 200
    assert response.context_data['company'] == company.serialize_for_template()


def test_edit_page_logo_submmit_success(
    returned_client, mock_update_company, sso_user,
    sso_user_middleware
):
    url = reverse('find-a-buyer-logo')
    data = {
        'logo': SimpleUploadedFile(
            name='image.png',
            content=create_test_image('png').read(),
            content_type='image/png',
        )
    }

    response = returned_client.post(url, data)

    assert response.status_code == 302
    assert response.url == reverse('find-a-buyer')
    assert mock_update_company.call_count == 1
    assert mock_update_company.call_args == mock.call(
        sso_session_id=sso_user.session_id,
        data={'logo': mock.ANY}
    )


@pytest.mark.parametrize('url,data', zip(edit_urls, edit_data))
def test_edit_page_submmit_error(
    returned_client, mock_update_company, url, data, sso_user_middleware
):
    mock_update_company.return_value = create_response(400)

    with pytest.raises(HTTPError):
        returned_client.post(url, data)


def test_case_study_create(
    submit_case_study_create_step, mock_create_case_study, mock_session_user,
    case_study_data, client
):
    mock_session_user.login()

    response = submit_case_study_create_step(case_study_data[views.BASIC])
    assert response.status_code == 302

    response = submit_case_study_create_step(case_study_data[views.MEDIA])
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.url == reverse('find-a-buyer')

    assert mock_create_case_study.call_count == 1


def test_case_study_edit(
    submit_case_study_edit_step, mock_retrieve_private_case_study, client,
    mock_update_case_study, mock_session_user, case_study_data,
    default_private_case_study
):
    mock_session_user.login()

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
    mock_retrieve_private_case_study, client, mock_session_user
):
    mock_retrieve_private_case_study.return_value = create_response(404)

    mock_session_user.login()
    url = reverse(
        'find-a-buyer-case-study-edit', kwargs={'id': '1', 'step': views.BASIC}
    )

    response = client.get(url)

    assert response.status_code == 404


def test_case_study_edit_found(
    mock_retrieve_private_case_study, client, mock_session_user
):
    mock_session_user.login()
    url = reverse(
        'find-a-buyer-case-study-edit', kwargs={'id': '1', 'step': views.BASIC}
    )

    response = client.get(url)

    assert response.status_code == 200


def test_admin_tools(
    settings, client, mock_session_user, default_company_profile
):
    mock_session_user.login()

    company = helpers.ProfileParser(default_company_profile)

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
    assert response.context_data['company'] == company.serialize_for_template()


def test_business_details_sole_trader(
    settings, mock_session_user, mock_retrieve_company, client
):
    mock_session_user.login()
    mock_retrieve_company.return_value = create_response(
        200, {'company_type': 'SOLE_TRADER'}
    )

    url = reverse('find-a-buyer-business-details')

    response = client.get(url)

    assert response.status_code == 200
    assert isinstance(
        response.context_data['form'], forms.SoleTraderBusinessDetailsForm
    )


def test_business_details_companies_house(
    settings, mock_session_user, client, mock_retrieve_company
):
    mock_session_user.login()
    mock_retrieve_company.return_value = create_response(
        200, {'company_type': 'COMPANIES_HOUSE'}
    )

    url = reverse('find-a-buyer-business-details')

    response = client.get(url)

    assert response.status_code == 200
    assert isinstance(
        response.context_data['form'], forms.CompaniesHouseBusinessDetailsForm
    )


@pytest.mark.parametrize('url', (
    reverse('find-a-buyer-expertise-routing'),
    reverse('find-a-buyer-expertise-regional'),
    reverse('find-a-buyer-expertise-countries'),
    reverse('find-a-buyer-expertise-languages'),
))
def test_add_expertise_feature_fag_off(settings, url, client):
    settings.FEATURE_FLAGS['EXPERTISE_FIELDS_ON'] = False

    response = client.get(url)

    assert response.status_code == 404


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
def test_add_expertise_routing(
    settings, choice, expected_url, client, mock_session_user
):
    mock_session_user.login()
    settings.FEATURE_FLAGS['EXPERTISE_FIELDS_ON'] = True

    url = reverse('find-a-buyer-expertise-routing')

    response = client.post(url, {'choice': choice})

    assert response.status_code == 302
    assert response.url == expected_url


def test_expertise_routing_form(client, settings, sso_user_middleware):
    url = reverse('find-a-buyer-expertise-routing')

    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['company']
