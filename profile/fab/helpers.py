from datetime import datetime

import http

from directory_api_client.client import api_client
from directory_constants.constants import choices
from directory_validators.helpers import tokenize_keywords


SECTOR_CHOICES = {key: value for key, value in choices.INDUSTRIES}
EMPLOYEE_CHOICES = {key: value for key, value in choices.EMPLOYEES}


def get_company_profile(sso_sesison_id):
    response = api_client.company.retrieve_private_profile(
        sso_session_id=sso_sesison_id
    )
    if response.status_code == http.client.NOT_FOUND:
        return None
    elif response.status_code == http.client.OK:
        return response.json()
    response.raise_for_status()


class ProfileParser:
    def __init__(self, data):
        self.data = data

    def __bool__(self):
        return bool(self.data)

    @property
    def date_of_creation(self):
        if self.data.get('date_of_creation'):
            date = datetime.strptime(self.data['date_of_creation'], '%Y-%m-%d')
            return date.strftime('%d %B %Y')

    @property
    def address(self):
        address = []
        fields = [
            'address_line_1', 'address_line_2', 'locality', 'postal_code'
        ]
        for field in fields:
            value = self.data.get(field)
            if value:
                address.append(value)
        return ', '.join(address)

    @property
    def keywords(self):
        if self.data.get('keywords'):
            return tokenize_keywords(self.data['keywords'])
        return []

    @property
    def sectors_label(self):
        if self.data.get('sectors'):
            return [SECTOR_CHOICES.get(item) for item in self.data['sectors']]
        return []

    @property
    def employees_label(self):
        if self.data.get('employees'):
            return EMPLOYEE_CHOICES.get(self.data['employees'])

    @property
    def is_sole_trader(self):
        return self.data['company_type'] != 'COMPANIES_HOUSE'

    def serialize_for_template(self):
        if not self.data:
            return {}
        return {
            **self.data,
            'date_of_creation': self.date_of_creation,
            'address': self.address,
            'sectors': self.sectors_label,
            'keywords': self.keywords,
            'employees': self.employees_label,
        }

    def serialize_for_form(self):
        if not self.data:
            return {}
        return {
            **self.data,
            'date_of_creation': self.date_of_creation,
            'address': self.address,
        }
