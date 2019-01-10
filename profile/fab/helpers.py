import http

from directory_api_external.client import api_client


def get_supplier_company_profile(sso_sesison_id):
    response = api_client.supplier.retrieve_supplier_company(sso_sesison_id)
    if response.status_code == http.client.NOT_FOUND:
        return None
    elif response.status_code == http.client.OK:
        return response.json()
    response.raise_for_status()
