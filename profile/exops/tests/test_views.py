from unittest.mock import patch

from django.core.urlresolvers import reverse

from profile.exops import views


def test_export_opportunities_exposes_context(client, sso_user_middleware):
    url = reverse('export-opportunities-applications')
    response = client.get(url)

    assert response.context_data['exops_tab_classes'] == 'active'


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_applications_retrieve_not_found(
    mock_retrieve_opportunities, api_response_403, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_403

    response = client.get(reverse('export-opportunities-applications'))

    assert response.template_name == [
        views.ExportOpportunitiesApplicationsView.template_name_not_exops_user
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_applications_retrieve_found(
    mock_retrieve_opportunities, api_response_200, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_200

    response = client.get(reverse('export-opportunities-applications'))

    assert response.template_name == [
        views.ExportOpportunitiesApplicationsView.template_name_exops_user
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_applications_retrieve_error(
    mock_retrieve_opportunities, api_response_500, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_500

    response = client.get(reverse('export-opportunities-applications'))

    assert response.template_name == [
        views.ExportOpportunitiesApplicationsView.template_name_error
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_email_alerts_retrieve_not_found(
    mock_retrieve_opportunities, api_response_403, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_403

    response = client.get(reverse('export-opportunities-email-alerts'))

    assert response.template_name == [
        views.ExportOpportunitiesEmailAlertsView.template_name_not_exops_user
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_email_alerts_retrieve_found(
    mock_retrieve_opportunities, api_response_200, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_200

    response = client.get(reverse('export-opportunities-email-alerts'))

    assert response.template_name == [
        views.ExportOpportunitiesEmailAlertsView.template_name_exops_user
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_email_alerts_retrieve_error(
    mock_retrieve_opportunities, api_response_500, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_500

    response = client.get(reverse('export-opportunities-email-alerts'))

    assert response.template_name == [
        views.ExportOpportunitiesEmailAlertsView.template_name_error
    ]
