from django.conf import settings

from directory_sso_api_client.client import DirectorySSOAPIClient


sso_api_client = DirectorySSOAPIClient(
    base_url=settings.SSO_API_CLIENT_BASE_URL,
    api_key=settings.SSO_API_CLIENT_KEY,
)


class SSOUser:

    def __init__(self, id, email):
        self.id = id
        self.email = email
