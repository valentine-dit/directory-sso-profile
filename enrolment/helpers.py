import collections
from http import cookies
import re

from directory_api_client.client import api_client
from directory_ch_client.client import ch_search_api_client
from directory_constants import choices
from directory_sso_api_client.client import sso_api_client
from directory_forms_api_client import actions
from directory_constants import urls
import directory_components

from django.utils import formats
from django.utils.dateparse import parse_datetime
from django.conf import settings

COMPANIES_HOUSE_DATE_FORMAT = '%Y-%m-%d'
SESSION_KEY_COMPANY_PROFILE = 'COMPANY_PROFILE'
SESSION_KEY_IS_ENROLLED = 'IS_ENROLLED'


ProgressIndicatorConf = collections.namedtuple(
    'ProgressIndicatorConf',
    ['step_counter_user', 'step_counter_anon']
)


def retrieve_preverified_company(enrolment_key):
    response = api_client.enrolment.retrieve_prepeveried_company(enrolment_key)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def claim_company(enrolment_key, personal_name, sso_session_id):
    response = api_client.enrolment.claim_prepeveried_company(
        data={'name': personal_name},
        key=enrolment_key,
        sso_session_id=sso_session_id,
    )
    response.raise_for_status()


def get_company_profile(number, session):
    session_key = f'{SESSION_KEY_COMPANY_PROFILE}-{number}'
    if session_key not in session:
        response = ch_search_api_client.company.get_company_profile(number)
        response.raise_for_status()
        session[session_key] = response.json()
    return session[session_key]


def create_user(email, password):
    response = sso_api_client.user.create_user(email, password)
    if response.status_code == 400:
        # Check for non-password errors and ignore since we want to proceed
        # For example we don't want to inform user of existing accounts
        if not response.json().get('password'):
            return None
    response.raise_for_status()
    return response.json()


def user_has_company(sso_session_id):
    response = api_client.company.retrieve_private_profile(sso_session_id)
    if response.status_code == 404:
        return False
    elif response.status_code == 200:
        return True
    response.raise_for_status()


def get_is_enrolled(company_number, session):
    session_key = f'{SESSION_KEY_IS_ENROLLED}-{company_number}'
    if session_key not in session:
        response = api_client.company.validate_company_number(company_number)
        if response.status_code == 400:
            session[session_key] = True
        else:
            response.raise_for_status()
            session[session_key] = False
    return session[session_key]


def create_company_profile(data):
    response = api_client.enrolment.send_form(data)
    response.raise_for_status()
    return response


def send_verification_code_email(email, verification_code, form_url):
    action = actions.GovNotifyEmailAction(
        template_id=settings.CONFIRM_VERIFICATION_CODE_TEMPLATE_ID,
        email_address=email,
        form_url=form_url,
    )

    expiry_date = parse_datetime(verification_code['expiration_date'])
    formatted_expiry_date = formats.date_format(
        expiry_date, "DATETIME_FORMAT"
    )
    response = action.save({
        'code': verification_code['code'],
        'expiry_date': formatted_expiry_date,
    })
    response.raise_for_status()
    return response


def notify_already_registered(email, form_url):
    action = actions.GovNotifyEmailAction(
        email_address=email,
        template_id=settings.GOV_NOTIFY_ALREADY_REGISTERED_TEMPLATE_ID,
        form_url=form_url,
    )

    response = action.save({
        'login_url': settings.SSO_PROXY_LOGIN_URL,
        'password_reset_url': settings.SSO_PROXY_PASSWORD_RESET_URL,
        'contact_us_url': urls.FEEDBACK,
    })

    response.raise_for_status()
    return response


def confirm_verification_code(email, verification_code):
    response = sso_api_client.user.verify_verification_code({
        'email': email,
        'code': verification_code,
    })
    response.raise_for_status()
    return response


def regenerate_verification_code(email):
    response = sso_api_client.user.regenerate_verification_code({
        'email': email,
    })
    if response.status_code == 400 or response.status_code == 404:
        # 400 indicates the email is already verified
        # 404 is returned if the email account doesn't exist
        return None
    response.raise_for_status()
    return response.json()


def request_collaboration(company_number, email, name, form_url):
    response = api_client.company.request_collaboration(
        company_number=company_number,
        collaborator_email=email,
    )
    response.raise_for_status()
    action = actions.GovNotifyEmailAction(
        email_address=response.json()['company_email'],
        template_id=settings.GOV_NOTIFY_REQUEST_COLLABORATION_TEMPLATE_ID,
        form_url=form_url,
    )
    response = action.save({
        'name': name,
        'email': email,
        'add_collaborator_url': settings.FAB_ADD_USER_URL,
        'report_abuse_url': urls.FEEDBACK,
    })
    response.raise_for_status()


class CompanyParser(directory_components.helpers.CompanyParser):

    SIC_CODES = dict(choices.SIC_CODES)

    @property
    def number(self):
        return self.data['company_number']

    @property
    def name(self):
        return self.data['company_name']

    @property
    def nature_of_business(self):
        return directory_components.helpers.values_to_labels(
            values=self.data.get('sic_codes', []),
            choices=self.SIC_CODES
        )

    @property
    def address(self):
        address = self.data.get('registered_office_address', {})
        names = ['address_line_1', 'address_line_2', 'locality', 'postal_code']
        return ', '.join([address[name] for name in names if name in address])

    @property
    def postcode(self):
        if self.data.get('registered_office_address'):
            return self.data['registered_office_address'].get('postal_code')


def parse_set_cookie_header(cookie_header):
    # parse a `set-cookies` header, returning http.cookies.SimpleCookie
    simple_cookies = cookies.SimpleCookie()
    # set-cookie header can contain multiple cookies, but `SimpleCookie.load`
    # expects only one cookie, so loop over them.
    # split on any ", " that is followed by any word character and =
    split = re.split(r', (?=\w*=)', cookie_header)
    for cookie in split:
        simple_cookies.load(cookie)
    return simple_cookies
