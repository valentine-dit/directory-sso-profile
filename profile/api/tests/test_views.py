from unittest.mock import patch

from requests import Response
from rest_framework import status
from rest_framework.reverse import reverse


@patch('profile.api.views.api_client.buyer.retrieve_supplier')
def test_external_supplier_get(
    mock_retrieve_supplier, sso_user_middleware, api_client,
    sso_user
):
    client_response = Response()
    client_response.json = lambda: {'foo': 'bar'}
    client_response.status_code = status.HTTP_200_OK
    mock_retrieve_supplier.return_value = client_response

    url = reverse('api-external-supplier')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'foo': 'bar'}
    assert response.status_code == status.HTTP_200_OK


def test_external_supplier_unauthenticated(
    sso_user_middleware_unauthenticated, api_client,
):
    url = reverse('api-external-supplier')

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch('profile.api.views.api_client.buyer.retrieve_supplier')
def test_external_supplier_client_erorr(
    mock_retrieve_supplier, sso_user_middleware, api_client,
):
    client_response = Response()
    client_response._content = b"Not good"
    client_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_retrieve_supplier.return_value = client_response

    url = reverse('api-external-supplier')

    response = api_client.get(url)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == 'Not good'
