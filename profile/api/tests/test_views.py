from requests import HTTPError
from unittest.mock import patch

from requests import Response
from rest_framework import status
from rest_framework.reverse import reverse


@patch('profile.api.views.get_sso_id_from_request')
@patch('profile.api.views.get_supplier_profile')
def test_external_supplier_get(
    mock_get_supplier_profile, mock_get_sso_id_from_request, api_client,
    sso_user
):
    mock_get_supplier_profile.return_value = {'foo': 'bar'}
    mock_get_sso_id_from_request.return_value = 123

    url = reverse('api-external-supplier')
    api_client.force_authenticate(user=sso_user)
    api_client.credentials(Authorization='Bearer {token}'.format(token='1234'))
    response = api_client.get(url)

    assert response.json() == {'foo': 'bar'}
    assert response.status_code == status.HTTP_200_OK


@patch('profile.api.views.get_sso_id_from_request')
@patch('profile.api.views.get_supplier_profile')
def test_external_supplier_client_error(
    mock_get_supplier_profile, mock_get_sso_id_from_request, api_client,
    sso_user
):
    client_response = Response()
    client_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_get_supplier_profile.side_effect = HTTPError(
        'Error',
        response=client_response
    )
    mock_get_sso_id_from_request.return_value = 123

    url = reverse('api-external-supplier')
    api_client.force_authenticate(user=sso_user)
    api_client.credentials(Authorization='Bearer {token}'.format(token='1234'))
    response = api_client.get(url)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@patch('profile.api.views.get_sso_id_from_request')
def test_external_supplier_incorrect_bearer_token(
    mock_get_sso_id_from_request, api_client, sso_user
):
    mock_get_sso_id_from_request.return_value = None
    url = reverse('api-external-supplier')

    api_client.force_authenticate(user=sso_user)
    api_client.credentials(Authorization='Bearer {token}'.format(token='1234'))

    response = api_client.get(url)

    assert response.json() == 'Unauthorized'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
