from django.core.urlresolvers import reverse


def test_selling_online_overseas_exposes_context(client, sso_user_middleware):
    url = reverse('selling-online-overseas')
    response = client.get(url)

    assert response.context_data['soo_tab_classes'] == 'active'
