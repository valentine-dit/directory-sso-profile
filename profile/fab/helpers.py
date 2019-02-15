import http

from directory_api_client.client import api_client


def get_company_profile(sso_sesison_id):
    response = api_client.company.retrieve_private_profile(
        sso_session_id=sso_sesison_id
    )
    if response.status_code == http.client.NOT_FOUND:
        return None
    elif response.status_code == http.client.OK:
        return response.json()
    response.raise_for_status()
