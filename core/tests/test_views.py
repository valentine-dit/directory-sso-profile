from unittest import mock

import pytest
import requests

from django.urls import reverse

from core.tests.helpers import create_response


def test_companies_house_search_validation_error(client, settings):
    url = reverse('api:companies-house-search')
    response = client.get(url)  # notice absense of `term`

    assert response.status_code == 400


@mock.patch('core.views.ch_search_api_client.company.search_companies')
def test_companies_house_search_api_error(mock_search, client, settings):

    mock_search.return_value = create_response(400)
    url = reverse('api:companies-house-search')

    with pytest.raises(requests.HTTPError):
        client.get(url, data={'term': 'thing'})


@mock.patch('core.views.ch_search_api_client.company.search_companies')
def test_companies_house_search_api_success(mock_search, client, settings):

    mock_search.return_value = create_response(
        200, {'items': [{'name': 'Smashing corp'}]}
    )
    url = reverse('api:companies-house-search')

    response = client.get(url, data={'term': 'thing'})

    assert response.status_code == 200
    assert response.content == b'[{"name":"Smashing corp"}]'


@mock.patch('core.views.ch_search_api_client.company.search_companies')
def test_companies_house_search(mock_search, client, settings):

    mock_search.return_value = create_response(
        200, {'items': [{'name': 'Smashing corp'}]}
    )
    url = reverse('api:companies-house-search')

    response = client.get(url, data={'term': 'thing'})

    assert response.status_code == 200
    assert response.content == b'[{"name":"Smashing corp"}]'
