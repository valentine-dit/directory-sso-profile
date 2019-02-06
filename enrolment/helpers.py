from http import cookies
from datetime import datetime
import time

from django.conf import settings
from directory_ch_client.client import ch_search_api_client
from directory_sso_api_client.client import sso_api_client
from directory_forms_api_client import actions

COMPANIES_HOUSE_DATE_FORMAT = '%Y-%m-%d'
SESSION_KEY_COMPANY_PROFILE = 'COMPANY_PROFILE'


def get_company_profile(number, session):
    session_key = f'{SESSION_KEY_COMPANY_PROFILE}-{number}'
    if session_key not in session:
        response = ch_search_api_client.company.get_company_profile(number)
        response.raise_for_status()
        session[session_key] = response.json()
    return session[session_key]


def create_user(email, password, cookies):
    response = sso_api_client.user.create_user(email, password)
    response.raise_for_status()
    cookies.update(cookiekjar_to_simple_cookie(response.cookies))
    return response.json()


def send_verification_code_email(email, verification_code, from_url):
    action = actions.GovNotifyAction(
        template_id=settings.CONFIRM_VERIFICATION_CODE_TEMPLATE_ID,
        email_address=email,
        form_url=from_url,
    )

    response = action.save({
        'code': verification_code,
        'expiry_days': settings.VERIFICATION_EXPIRY_DAYS,
    })
    response.raise_for_status()
    return response


def confirm_verification_code(sso_session_id, verification_code):
    response = sso_api_client.user.verify_verification_code(
        sso_session_id=sso_session_id,
        code=verification_code,
    )
    response.raise_for_status()
    return response


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
        address = []
        if self.data.get('registered_office_address'):
            for field in ['address_line_1', 'address_line_2', 'locality']:
                value = self.data['registered_office_address'].get(field)
                if value:
                    address.append(value)
        return ', '.join(address)

    @property
    def postcode(self):
        if self.data.get('registered_office_address'):
            return self.data['registered_office_address']['postal_code']


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
