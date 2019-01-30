from datetime import datetime

from django.conf import settings

from directory_ch_client.client import ch_search_api_client
from directory_sso_api_client import user

COMPANIES_HOUSE_DATE_FORMAT = '%Y-%m-%d'

user_api = user.UserAPIClient(
    base_url=settings.DIRECTORY_SSO_API_USER_BASE_URL,
    api_key=settings.DIRECTORY_SSO_API_USER_API_KEY,
    sender_id=settings.DIRECTORY_SSO_API_USER_SENDER_ID,
    timeout=settings.DIRECTORY_SSO_API_USER_DEFAULT_TIMEOUT,
)


def get_company_profile(number):
    response = ch_search_api_client.company.get_company_profile(number)
    response.raise_for_status()
    return response.json()


def create_user(email, password):
    response = user_api.create_user(email, password)
    response.raise_for_status()
    return response.json()


class CompanyProfileFormatter:
    def __init__(self, unfomatted_companies_house_data):
        self.data = unfomatted_companies_house_data

    @property
    def number(self):
        return self.data['company_number']

    @property
    def name(self):
        return self.data['company_name']

    @property
    def sic_code(self):
        return ', '.join(self.data.get('sic_codes', []))

    @property
    def date_created(self):
        date = self.data.get('date_of_creation')
        if date:
            return datetime.strptime(date, COMPANIES_HOUSE_DATE_FORMAT)

    @property
    def address(self):
        return ' '.join(
            self.data.get('registered_office_address', {}).values()
        )
