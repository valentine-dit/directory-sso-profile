import http
from unittest.mock import patch

from django.core.urlresolvers import reverse

from profile.exops import views


def test_export_opportunities_applications_exposes_context(
    client, settings, user
):
    client.force_login(user)
    settings.EXPORTING_OPPORTUNITIES_SEARCH_URL = 'http://find'
    url = reverse('export-opportunities-applications')

    response = client.get(url)
    context_data = response.context_data

    assert context_data['exops_tab_classes'] == 'active'
    assert context_data['EXPORTING_OPPORTUNITIES_SEARCH_URL'] == 'http://find'


def test_export_opportunities_email_alerts_exposes_context(
    client, settings, user
):
    client.force_login(user)

    settings.EXPORTING_OPPORTUNITIES_SEARCH_URL = 'http://find'
    url = reverse('export-opportunities-email-alerts')

    response = client.get(url)
    context_data = response.context_data

    assert context_data['exops_tab_classes'] == 'active'
    assert context_data['EXPORTING_OPPORTUNITIES_SEARCH_URL'] == 'http://find'


def test_opportunities_applications_unauthenticated(client):
    url = reverse('export-opportunities-applications')
    response = client.get(url)

    assert response.status_code == http.client.FOUND


def test_opportunities_email_alerts_unauthenticated(client):
    url = reverse('export-opportunities-email-alerts')
    response = client.get(url)

    assert response.status_code == http.client.FOUND


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_applications_retrieve_not_found(
    mock_retrieve_opportunities, api_response_403, client, user
):
    client.force_login(user)
    mock_retrieve_opportunities.return_value = api_response_403
    url = reverse('export-opportunities-applications')

    response = client.get(url)

    assert response.template_name == [
        views.ExportOpportunitiesApplicationsView.template_name_not_exops_user
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_applications_retrieve_found(
    mock_retrieve_opportunities, api_response_200, client, user
):
    client.force_login(user)
    mock_retrieve_opportunities.return_value = api_response_200

    url = reverse('export-opportunities-applications')
    response = client.get(url)

    assert response.template_name == [
        views.ExportOpportunitiesApplicationsView.template_name_exops_user
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_applications_retrieve_error(
    mock_retrieve_opportunities, api_response_500, client, user
):
    client.force_login(user)
    mock_retrieve_opportunities.return_value = api_response_500
    url = reverse('export-opportunities-applications')

    response = client.get(url)

    assert response.template_name == [
        views.ExportOpportunitiesApplicationsView.template_name_error
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_email_alerts_retrieve_not_found(
    mock_retrieve_opportunities, api_response_403, client, user
):
    client.force_login(user)
    mock_retrieve_opportunities.return_value = api_response_403

    url = reverse('export-opportunities-email-alerts')
    response = client.get(url)

    assert response.template_name == [
        views.ExportOpportunitiesEmailAlertsView.template_name_not_exops_user
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_email_alerts_retrieve_found(
    mock_retrieve_opportunities, api_response_200, client, user
):
    client.force_login(user)
    mock_retrieve_opportunities.return_value = api_response_200
    url = reverse('export-opportunities-email-alerts')

    response = client.get(url)

    assert response.template_name == [
        views.ExportOpportunitiesEmailAlertsView.template_name_exops_user
    ]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_email_alerts_retrieve_error(
    mock_retrieve_opportunities, api_response_500, client, user
):
    client.force_login(user)
    mock_retrieve_opportunities.return_value = api_response_500
    url = reverse('export-opportunities-email-alerts')

    response = client.get(url)

    assert response.template_name == [
        views.ExportOpportunitiesEmailAlertsView.template_name_error
    ]
