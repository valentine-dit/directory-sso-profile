import http

from api_client import api_client


def get_supplier_company_profile(sso_sesison_id):
    response = api_client.buyer.retrieve_supplier_company(sso_sesison_id)
    if response.status_code == http.client.UNAUTHORIZED:
        return None
    elif response.status_code == http.client.OK:
        return response.json()
    raise response.raise_for_status()
