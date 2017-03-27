from django.core.urlresolvers import reverse


def test_export_opportunities_exposes_context(client, sso_user_middleware):
    url = reverse('export-opportunities')
    response = client.get(url)

    assert response.context_data['exops_tab_classes'] == 'active'
