from unittest.mock import patch

from django.core.urlresolvers import reverse

from profile.exops import views


def test_export_opportunities_exposes_context(client, sso_user_middleware):
    url = reverse('export-opportunities')
    response = client.get(url)

    assert response.context_data['exops_tab_classes'] == 'active'


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_retrieve_not_found(
    mock_retrieve_opportunities, api_response_403, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_403
    expected = views.ExportOpportunitiesView.template_name_not_exops_user

    response = client.get(reverse('export-opportunities'))

    assert response.template_name == [expected]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_retrieve_found(
    mock_retrieve_opportunities, api_response_200, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_200
    expected = views.ExportOpportunitiesView.template_name_exops_user

    response = client.get(reverse('export-opportunities'))

    assert response.template_name == [expected]


@patch('profile.exops.helpers.exporting_is_great_client.get_opportunities')
def test_opportunities_retrieve_error(
    mock_retrieve_opportunities, api_response_500, sso_user_middleware,
    client
):
    mock_retrieve_opportunities.return_value = api_response_500
    expected = views.ExportOpportunitiesView.template_name_error

    response = client.get(reverse('export-opportunities'))

    assert response.template_name == [expected]
