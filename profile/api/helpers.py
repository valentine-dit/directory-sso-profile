import http

from api_client import api_client


def get_supplier_profile(sso_id):
    response = api_client.buyer.retrieve_supplier(sso_id)
    if response.status_code == http.client.NOT_FOUND:
        return None
    elif response.status_code == http.client.OK:
        return response.json()
    raise response.raise_for_status()
