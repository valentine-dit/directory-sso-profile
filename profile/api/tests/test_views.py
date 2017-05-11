from unittest.mock import patch

from requests import HTTPError, Response
from rest_framework import status
from rest_framework.reverse import reverse


@patch('profile.api.helpers.get_supplier_profile')
def test_external_supplier_get(mock_get_supplier_profile, client):
    mock_get_supplier_profile.return_value = {'foo': 'bar'}

    url = reverse('api-external-supplier', kwargs={'sso_id': 2})
    response = client.get(url)
    assert response.json() == {'foo': 'bar'}


@patch('profile.api.helpers.get_supplier_profile')
def test_external_supplier_client_error(mock_get_supplier_profile, client):
    client_response = Response()
    client_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_get_supplier_profile.side_effect = HTTPError(
        'Error',
        response=client_response
    )

    url = reverse('api-external-supplier', kwargs={'sso_id': 2})
    response = client.get(url)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == 'Error'
