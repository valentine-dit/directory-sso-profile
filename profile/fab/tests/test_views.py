from io import BytesIO
import http
from unittest import mock

from directory_api_client.client import api_client
import pytest
from PIL import Image, ImageDraw
from requests.exceptions import HTTPError

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse

from core.tests.helpers import create_response
from profile.fab import views


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
    return {'name': 'Cool Company'}


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


def test_find_a_buyer_redirect_first_time_user(sso_user_middleware, client):
    response = client.get(reverse('find-a-buyer'))

    assert response.status_code == http.client.FOUND
    assert response.get('Location') == reverse('about')


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
    sso_user_middleware_unauthenticated, returned_client
):
    response = returned_client.get(reverse('find-a-buyer'))

    assert response.status_code == http.client.FOUND


def test_supplier_company_retrieve_not_found(
    mock_retrieve_company, sso_user_middleware, returned_client
):
    mock_retrieve_company.return_value = create_response(404)
    expected_template_name = views.FindABuyerView.template_name_not_fab_user

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]


def test_supplier_company_retrieve_found(
    mock_retrieve_company, sso_user_middleware, returned_client, settings
):
    settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON'] = False

    mock_retrieve_company.return_value = create_response(200)
    expected_template_name = views.FindABuyerView.template_name_fab_user

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]


def test_supplier_company_retrieve_found_business_profile_on(
    mock_retrieve_company, sso_user_middleware, returned_client, settings
):
    settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON'] = True

    mock_retrieve_company.return_value = create_response(200)

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

    assert response.context_data['success_message'] == (
        views.FindABuyerView.SUCCESS_MESSAGES[param]
    )


edit_urls = (
    reverse('find-a-buyer-description'),
    reverse('find-a-buyer-email'),
    reverse('find-a-buyer-social'),
)

edit_data = (
    {'description': 'A description', 'summary': 'A summary'},
    {'email_address': 'email@example.com'},
    {
        'facebook_url': 'https://www.facebook.com/thing/',
        'twitter_url': 'https://www.twitter.com/thing/',
        'linkedin_url': 'https://www.linkedin.com/thing/',
    },
)


@pytest.mark.parametrize('url', edit_urls)
def test_edit_page_initial_data(
    returned_client, url, default_company_profile, sso_user_middleware
):
    response = returned_client.get(url)
    assert response.context_data['form'].initial == default_company_profile


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
