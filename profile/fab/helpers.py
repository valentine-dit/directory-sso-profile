import http

from directory_api_client.client import api_client
import directory_components.helpers


def get_company_profile(sso_sesison_id):
    response = api_client.company.retrieve_private_profile(
        sso_session_id=sso_sesison_id
    )
    if response.status_code == http.client.NOT_FOUND:
        return None
    elif response.status_code == http.client.OK:
        return response.json()
    response.raise_for_status()


class CompanyParser(directory_components.helpers.CompanyParser):

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
            'expertise_industries': self.expertise_industries_label,
            'expertise_regions': self.expertise_regions_label,
            'expertise_countries': self.expertise_countries_label,
            'expertise_languages': self.expertise_languages_label,
            'has_expertise': self.has_expertise,
            'expertise_products_services': (
                self.expertise_products_services_label
            ),
        }

    def serialize_for_form(self):
        if not self.data:
            return {}
        return {
            **self.data,
            'date_of_creation': self.date_of_creation,
            'address': self.address,
        }


def unslugify(slug):
    return (slug.replace('-', ' ')).capitalize()
