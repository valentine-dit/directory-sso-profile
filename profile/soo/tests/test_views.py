import http

from django.core.urlresolvers import reverse


def test_selling_online_overseas_exposes_context(
    returned_client, sso_user_middleware
):
    url = reverse('selling-online-overseas')
    response = returned_client.get(url)

    assert response.context_data['soo_tab_classes'] == 'active'


def test_selling_online_overseas_redirect_first_time_user(
    sso_user_middleware, client
):
    response = client.get(reverse('selling-online-overseas'))

    assert response.status_code == http.client.FOUND
    assert response.get('Location') == reverse('about')
