from django.core.urlresolvers import reverse


def test_selling_online_overseas_exposes_context(client, mock_session_user):
    mock_session_user.login()
    url = reverse('selling-online-overseas')
    response = client.get(url)

    assert response.context_data['soo_tab_classes'] == 'active'
