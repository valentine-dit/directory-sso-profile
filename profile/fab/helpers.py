from datetime import datetime
import http

from directory_api_client.client import api_client
from directory_constants.constants import choices
from directory_validators.helpers import tokenize_keywords

from profile.fab import forms


SECTOR_CHOICES = dict(choices.INDUSTRIES)
EMPLOYEE_CHOICES = dict(choices.EMPLOYEES)
INDUSTRY_CHOICES = dict(choices.INDUSTRIES)
COUNTRY_CHOICES = dict(choices.COUNTRY_CHOICES)
REGION_CHOICES = dict(forms.REGION_CHOICES)
LANGUAGES_CHOICES = dict(forms.LANGUAGES_CHOICES)


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
    def is_publishable(self):
        return self.data['is_publishable']

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
            return ', '.join(tokenize_keywords(self.data['keywords']))
        return ''

    @property
    def sectors_label(self):
        return values_to_labels(
            values=self.data.get('sectors') or [],
            choices=SECTOR_CHOICES
        )

    @property
    def employees_label(self):
        if self.data.get('employees'):
            return EMPLOYEE_CHOICES.get(self.data['employees'])

    @property
    def expertise_industries_label(self):
        return values_to_labels(
            values=self.data.get('expertise_industries') or [],
            choices=INDUSTRY_CHOICES
        )

    @property
    def expertise_regions_label(self):
        return values_to_labels(
            values=self.data.get('expertise_regions') or [],
            choices=REGION_CHOICES
        )

    @property
    def expertise_countries_label(self):
        return values_to_labels(
            values=self.data.get('expertise_countries') or [],
            choices=COUNTRY_CHOICES
        )

    @property
    def expertise_languages_label(self):
        return values_to_labels(
            values=self.data.get('expertise_languages') or [],
            choices=LANGUAGES_CHOICES
        )

    @property
    def is_sole_trader(self):
        return self.data['company_type'] != 'COMPANIES_HOUSE'

    @property
    def has_expertise(self):
        fields = [
            'expertise_industries',
            'expertise_regions',
            'expertise_countries',
            'expertise_languages',
        ]
        return any(self.data.get(field) for field in fields)

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
            'expertise_industries': self.expertise_industries_label,
            'expertise_regions': self.expertise_regions_label,
            'expertise_countries': self.expertise_countries_label,
            'expertise_languages': self.expertise_languages_label,
            'has_expertise': self.has_expertise,
        }

    def serialize_for_form(self):
        if not self.data:
            return {}
        return {
            **self.data,
            'date_of_creation': self.date_of_creation,
            'address': self.address,
        }


def values_to_labels(values, choices):
    return ', '.join([choices.get(item) for item in values if item in choices])
