from django.core.urlresolvers import reverse


def test_find_a_buyer_exposes_context(client, sso_user_middleware):
    url = reverse('find-a-buyer')
    response = client.get(url)

    assert response.context_data['fab_tab_classes'] == 'active'
