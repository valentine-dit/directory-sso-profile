from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse


@patch('profile.api.views.api_client.supplier.retrieve_supplier')
def test_external_supplier_get(
    mock_get_supplier_profile, api_client, sso_user, api_response_200
):
    api_response_200.json = lambda: {'foo': 'bar'}
    mock_get_supplier_profile.return_value = api_response_200

    url = reverse('api:external-supplier')
    response = api_client.get(
        url, HTTP_AUTHORIZATION='Bearer {token}'.format(token='1234')
    )

    assert response.json() == {'foo': 'bar'}
    assert response.status_code == status.HTTP_200_OK


@patch('profile.api.views.api_client.supplier.retrieve_supplier')
def test_external_supplier_client_error(
    mock_get_supplier_profile, api_client, api_response_500
):
    mock_get_supplier_profile.return_value = api_response_500

    url = reverse('api:external-supplier')

    response = api_client.get(
        url, HTTP_AUTHORIZATION='Bearer {token}'.format(token='1234')
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@patch('profile.api.views.api_client.supplier.retrieve_supplier')
def test_external_supplier_incorrect_bearer_token(
    mock_get_supplier_profile, api_client, api_response_401
):
    mock_get_supplier_profile.return_value = api_response_401

    url = reverse('api:external-supplier')

    response = api_client.get(
        url, HTTP_AUTHORIZATION='Bearer {token}'.format(token='1234')
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_external_supplier_missing_bearer_token(api_client):

    url = reverse('api:external-supplier')

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
