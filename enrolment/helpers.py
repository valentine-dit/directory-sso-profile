from http import cookies
from datetime import datetime
import time

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
    return {
        'cookies': response.cookies,
        **response.json()
    }


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


def cookiekjar_to_simple_cookie(cookiejar):
    simple_cookies = cookies.SimpleCookie()
    for cookie in cookiejar:
        simple_cookies[cookie.name] = cookie.value
        for attr in ('path', 'comment', 'domain', 'secure', 'version'):
            simple_cookies[cookie.name][attr] = getattr(cookie, attr)
        # Cookies thinks an int expires x seconds in future,
        # cookielib thinks it is x seconds from epoch,
        # so doing the conversion to string for Cookies
        simple_cookies[cookie.name]['expires'] = time.strftime(
            '%a, %d %b %Y %H:%M:%S GMT',
            time.gmtime(cookie.expires)
        )
    return simple_cookies
