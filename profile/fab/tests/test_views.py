from unittest.mock import patch

from django.core.urlresolvers import reverse

from profile.fab import views


def test_find_a_buyer_exposes_context(client, sso_user_middleware, settings):
    settings.FAB_EDIT_COMPANY_LOGO_URL = 'http://logo'
    settings.FAB_EDIT_PROFILE_URL = 'http://profile'
    settings.FAB_ADD_CASE_STUDY_URL = 'http://case'

    response = client.get(reverse('find-a-buyer'))

    assert response.context_data['fab_tab_classes'] == 'active'
    assert response.context_data['FAB_EDIT_COMPANY_LOGO_URL'] == 'http://logo'
    assert response.context_data['FAB_EDIT_PROFILE_URL'] == 'http://profile'
    assert response.context_data['FAB_ADD_CASE_STUDY_URL'] == 'http://case'


@patch('profile.fab.helpers.api_client.buyer.retrieve_supplier_company')
def test_supplier_company_retrieve_not_found(
    mock_retrieve_supplier_company, api_response_404, sso_user_middleware,
    client
):
    mock_retrieve_supplier_company.return_value = api_response_404
    expected_template_name = views.FindABuyerView.template_name_not_fab_user

    response = client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]


@patch('profile.fab.helpers.api_client.buyer.retrieve_supplier_company')
def test_supplier_company_retrieve_found(
    mock_retrieve_supplier_company, api_response_200, sso_user_middleware,
    client
):
    mock_retrieve_supplier_company.return_value = api_response_200
    expected_template_name = views.FindABuyerView.template_name_fab_user

    response = client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]


@patch('profile.fab.helpers.api_client.buyer.retrieve_supplier_company')
def test_supplier_company_retrieve_error(
    mock_retrieve_supplier_company, api_response_500, sso_user_middleware,
    client
):
    mock_retrieve_supplier_company.return_value = api_response_500
    expected_template_name = views.FindABuyerView.template_name_error

    response = client.get(reverse('find-a-buyer'))

    assert response.template_name == [expected_template_name]
