from datetime import datetime

from directory_ch_client.client import ch_search_api_client
from directory_sso_api_client.client import sso_api_client


COMPANIES_HOUSE_DATE_FORMAT = '%Y-%m-%d'


def get_company_profile(number):
    response = ch_search_api_client.company.get_company_profile(number)
    response.raise_for_status()
    return response.json()


def create_user(email, password):
    response = sso_api_client.user.create_user(email, password)
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
            date_format = COMPANIES_HOUSE_DATE_FORMAT
            return datetime.strptime(date, date_format).strftime('%m %B %Y')

    @property
    def address(self):
        return ' '.join(
            self.data.get('registered_office_address', {}).values()
        )
