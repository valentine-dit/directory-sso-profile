from unittest.mock import patch

from rest_framework.reverse import reverse


@patch('profile.api.helpers.get_supplier_profile')
def test_external_supplier_get(mock_get_supplier_profile, client):
    mock_get_supplier_profile.return_value = {'foo': 'bar'}

    url = reverse('api-external-supplier', kwargs={'sso_id': 2})
    response = client.get(url)
    assert response.json() == {'foo': 'bar'}
