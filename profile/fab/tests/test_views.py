import http
from unittest.mock import patch

from directory_api_client.client import api_client
import pytest
import requests

from django.core.urlresolvers import reverse

from profile.fab import views


@pytest.fixture
def api_response_supplier_profile_owner_200():
    response = requests.Response()
    response.status_code = 200
    response.json = lambda: {'is_company_owner': True}
    return response


@pytest.fixture
def api_response_supplier_profile_non_owner_200():
    response = requests.Response()
    response.status_code = 200
    response.json = lambda: {'is_company_owner': False}
    return response


@pytest.fixture
def api_response_company_profile_200():
    response = requests.Response()
    response.status_code = 200
    response.json = lambda: {'name': 'Cool Company'}
    return response


@patch.object(api_client.supplier, 'retrieve_profile')
@patch.object(api_client.company, 'retrieve_private_profile')
def test_find_a_buyer_redirect_first_time_user(
    mock_retrieve_company, mock_retrieve_supplier, sso_user_middleware, client,
    api_response_company_profile_200, api_response_supplier_profile_owner_200
):
    mock_retrieve_company.return_value = api_response_company_profile_200
    mock_retrieve_supplier.return_value = (
        api_response_supplier_profile_owner_200
    )
    response = client.get(reverse('find-a-buyer'))

    assert response.status_code == http.client.FOUND
    assert response.get('Location') == reverse('about')


@patch.object(api_client.supplier, 'retrieve_profile')
@patch.object(api_client.company, 'retrieve_private_profile')
def test_find_a_buyer_exposes_context(
    mock_retrieve_company, mock_retrieve_supplier, returned_client,
    sso_user_middleware, settings, api_response_company_profile_200,
    api_response_supplier_profile_owner_200
):
    mock_retrieve_company.return_value = api_response_company_profile_200
    mock_retrieve_supplier.return_value = (
        api_response_supplier_profile_owner_200
    )
    settings.FAB_EDIT_COMPANY_LOGO_URL = 'http://logo'
    settings.FAB_EDIT_PROFILE_URL = 'http://profile'
    settings.FAB_ADD_CASE_STUDY_URL = 'http://case'
    settings.FAB_REGISTER_URL = 'http://register'

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.context_data['fab_tab_classes'] == 'active'
    assert response.context_data['FAB_EDIT_COMPANY_LOGO_URL'] == 'http://logo'
    assert response.context_data['FAB_EDIT_PROFILE_URL'] == 'http://profile'
    assert response.context_data['FAB_ADD_CASE_STUDY_URL'] == 'http://case'
    assert response.context_data['FAB_REGISTER_URL'] == 'http://register'


def test_find_a_buyer_unauthenticated(
    sso_user_middleware_unauthenticated, returned_client
):
    response = returned_client.get(reverse('find-a-buyer'))

    assert response.status_code == http.client.FOUND


@patch.object(api_client.company, 'retrieve_private_profile')
def test_supplier_company_retrieve_not_found(
    mock_retrieve_supplier_company, api_response_404, sso_user_middleware,
    returned_client
):
    mock_retrieve_supplier_company.return_value = api_response_404
    expected_template_name = views.FindABuyerView.template_name_not_fab_user

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]


@patch.object(api_client.company, 'retrieve_private_profile')
def test_supplier_company_retrieve_found(
    mock_retrieve_supplier_company, api_response_200, sso_user_middleware,
    returned_client, settings
):
    settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON'] = False

    mock_retrieve_supplier_company.return_value = api_response_200
    expected_template_name = views.FindABuyerView.template_name_fab_user

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]


@patch.object(api_client.company, 'retrieve_private_profile')
def test_supplier_company_retrieve_found_business_profile_on(
    mock_retrieve_supplier_company, api_response_200, sso_user_middleware,
    returned_client, settings
):
    settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON'] = True

    mock_retrieve_supplier_company.return_value = api_response_200

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.template_name == ['fab/profile.html']


@patch.object(api_client.company, 'retrieve_private_profile')
@patch.object(api_client.supplier, 'retrieve_profile')
def test_company_owner(
    mock_mock_retrieve_supplier, mock_retrieve_supplier_company,
    api_response_supplier_profile_owner_200, api_response_company_profile_200,
    sso_user_middleware, returned_client
):
    mock_retrieve_supplier_company.return_value = (
        api_response_company_profile_200
    )
    mock_mock_retrieve_supplier.return_value = (
        api_response_supplier_profile_owner_200
    )

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.context_data['is_profile_owner'] is True


@patch.object(api_client.company, 'retrieve_private_profile')
@patch.object(api_client.supplier, 'retrieve_profile')
def test_non_company_owner(
    mock_mock_retrieve_supplier, mock_retrieve_supplier_company,
    api_response_supplier_profile_non_owner_200, api_response_200,
    sso_user_middleware, returned_client
):
    mock_retrieve_supplier_company.return_value = api_response_200
    mock_mock_retrieve_supplier.return_value = (
        api_response_supplier_profile_non_owner_200
    )

    response = returned_client.get(reverse('find-a-buyer'))

    assert response.context_data['is_profile_owner'] is False


@pytest.mark.parametrize('param', (
    'owner-transferred', 'user-added', 'user-removed'
))
@patch.object(api_client.company, 'retrieve_private_profile')
@patch.object(api_client.supplier, 'retrieve_profile')
def test_success_message(
    mock_mock_retrieve_supplier, mock_retrieve_supplier_company,
    api_response_supplier_profile_non_owner_200, api_response_200,
    sso_user_middleware, returned_client, param
):
    mock_retrieve_supplier_company.return_value = api_response_200
    mock_mock_retrieve_supplier.return_value = (
        api_response_supplier_profile_non_owner_200
    )

    url = reverse('find-a-buyer')
    response = returned_client.get(url, {param: True})

    assert response.context_data['success_message'] == (
        views.FindABuyerView.SUCCESS_MESSAGES[param]
    )
