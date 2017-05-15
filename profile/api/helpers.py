import http

import requests
from django.conf import settings

from api_client import api_client


def get_supplier_profile(sso_id):
    response = api_client.buyer.retrieve_supplier(sso_id)
    if response.status_code == http.client.NOT_FOUND:
        return None
    elif response.status_code == http.client.OK:
        return response.json()
    raise response.raise_for_status()


def get_sso_id_from_request(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    if not token:
        return None
    url = '{base}{endpoint}'.format(
        base=settings.SSO_API_OAUTH2_BASE_URL,
        endpoint='user-profile/v1/')
    headers = {'Authorization': token}  # token is in the format 'Bearer 123'
    response = requests.get(url, headers=headers)
    if response.ok:
        return response.json()['id']
    return None
