from captcha.fields import ReCaptchaField
from directory_components import forms
from directory_constants import choices
from requests.exceptions import HTTPError
from directory_validators.company import (
    no_company_with_insufficient_companies_house_data as company_type_validator
)
from directory_validators.enrolment import (
    company_number as company_number_validator
)

from django.forms import HiddenInput, PasswordInput, Textarea, ValidationError
from django.utils.safestring import mark_safe
from django.http.request import QueryDict

from enrolment import constants, helpers
from enrolment.widgets import PostcodeInput
import core.forms

INDUSTRY_CHOICES = (
    (('', 'Please select'),) + choices.INDUSTRIES + (('OTHER', 'Other'),)
)


class BusinessType(forms.Form):
    CHOICES = (
        (
            constants.COMPANIES_HOUSE_COMPANY,
            (
                'My business is registered with Companies House.  '
                'For example, a limited company (Ltd), a public limited  '
                'company (PLC) or a Royal Charter company'
            )
        ),
        (
            constants.SOLE_TRADER,
            (
                'I\'m a sole trader or I represent another type of UK '
                'business not registered with Companies House'
            )
        ),
        (
            constants.NOT_COMPANY,
            (
                'I\'m a UK taxpayer but do not represent a business'
            )
        ),
        (
            constants.OVERSEAS_COMPANY,
            (
                'My business or organisation is not registered in the UK'
            )
        ),
    )
    choice = forms.ChoiceField(
        label='',
        widget=forms.RadioSelect(),
        choices=CHOICES,
    )


class UserAccount(forms.Form):
    PASSWORD_HELP_TEXT = (
        '<p>Your password must:</p>'
        '<ul class="list list-bullet margin-l-30-m">'
        '<li>be at least 10 characters</li>'
        '<li>have at least 1 letter</li>'
        '<li>have at least 1 number</li>'
        '<li>not contain the words which are easy to guess such as "password"'
        '</li>'
        '</ul>'
    )
    MESSAGE_NOT_MATCH = "Passwords don't match"
    MESSAGE_PASSWORD_INVALID = 'Invalid Password'

    email = forms.EmailField(
        label='Your email address'
    )
    password = forms.CharField(
        label='Set a password',
        help_text=mark_safe(PASSWORD_HELP_TEXT),
        widget=PasswordInput
    )
    password_confirmed = forms.CharField(
        label='Confirm password',
        widget=PasswordInput,
    )
    captcha = ReCaptchaField(
        label='',
        label_suffix='',
    )
    terms_agreed = forms.BooleanField(label=core.forms.TERMS_LABEL)

    def clean_password_confirmed(self):
        value = self.cleaned_data['password_confirmed']
        if value != self.cleaned_data['password']:
            raise ValidationError(self.MESSAGE_NOT_MATCH)
        return value

    def clean(self):
        cleaned_data = super().clean()
        if not self.errors:
            try:
                cleaned_data['user_details'] = helpers.create_user(
                    email=cleaned_data['email'],
                    password=cleaned_data['password'],
                )
            except HTTPError as error:
                if error.response.status_code == 400:
                    self.add_error('password', self.MESSAGE_PASSWORD_INVALID)
                else:
                    raise
        return None


class UserAccountVerification(forms.Form):

    MESSAGE_INVALID_CODE = 'Invalid code'
    # email field can be overridden in __init__ to allow user to enter email
    email = forms.CharField(label='', widget=HiddenInput, disabled=True)
    code = forms.CharField(
        label='Confirmation Code',
        min_length=5,
        max_length=5,
        error_messages={'required': MESSAGE_INVALID_CODE}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get('email') is None:
            self.fields['email'] = forms.EmailField(
                label='Your email address'
            )


class CompaniesHouseSearch(forms.Form):
    MESSAGE_COMPANY_NOT_FOUND = (
        "<p>Your business name is not listed.</p>"
        "<p>Check that you've entered the right name.</p>"
    )
    MESSAGE_COMPANY_NOT_ACTIVE = 'Company not active.'
    company_name = forms.CharField(
        label='Registered company name',
    )
    company_number = forms.CharField(
        validators=[company_number_validator],
    )

    def __init__(self, session, *args, **kwargs):
        self.session = session
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if 'company_number' in cleaned_data:
            try:
                company_type_validator(cleaned_data['company_number'])
            except ValidationError as error:
                raise ValidationError({
                    'company_name': error
                })
            company_data = helpers.get_company_profile(
                number=self.cleaned_data['company_number'],
                session=self.session,
            )
            if company_data['company_status'] != 'active':
                raise ValidationError(
                    {'company_name': self.MESSAGE_COMPANY_NOT_ACTIVE}
                )
        elif 'company_name' in cleaned_data:
            raise ValidationError(
                {'company_name': mark_safe(self.MESSAGE_COMPANY_NOT_FOUND)}
            )


class CompaniesHouseBusinessDetails(forms.Form):
    company_name = forms.CharField(
        label='Registered company name',
    )
    company_number = forms.CharField(
        disabled=True,
        required=False,
        container_css_classes='border-active-blue read-only-input-container'
    )
    sic = forms.CharField(
        label='Nature of business',
        disabled=True,
        required=False,
        container_css_classes='border-active-blue read-only-input-container'
    )
    date_of_creation = forms.DateField(
        label='Incorporated on',
        input_formats=['%d %B %Y'],
        disabled=True,
        required=False,
        container_css_classes='border-active-blue read-only-input-container'
    )
    postal_code = forms.CharField(
        disabled=True,
        required=False,
        container_css_classes='hidden-input-container',
    )
    address = forms.CharField(
        disabled=True,
        required=False,
        container_css_classes='border-active-blue read-only-input-container'
        )
    sectors = forms.ChoiceField(
        label='What industry is your company in?',
        choices=INDUSTRY_CHOICES,
    )
    website = forms.URLField(
        label='What\'s your business web address (optional)',
        help_text='The website address must start with http:// or https://',
        required=False,
    )

    def __init__(
        self, initial, company_data=None, is_enrolled=False, *args, **kwargs
    ):
        super().__init__(initial=initial, *args, **kwargs)
        if company_data:
            self.set_form_initial(company_data)
        if is_enrolled:
            self.delete_already_enrolled_fields()
        # force the form to use the initial value rather than the value
        # the user submitted in previous sessions
        # on GET the data structure is a MultiValueDict. on POST the data
        # structure is a QueryDict
        if self.data and not isinstance(self.data, QueryDict):
            self.initial_to_data('company_name')
            if not self.data.get('postal_code'):
                self.initial_to_data('postal_code')

    def delete_already_enrolled_fields(self):
        del self.fields['sectors']
        del self.fields['website']

    def set_form_initial(self, company_profile):
        company = helpers.CompanyParser(company_profile)
        self.initial['company_name'] = company.name
        self.initial['company_number'] = company.number
        self.initial['sic'] = company.nature_of_business
        self.initial['date_of_creation'] = company.date_of_creation
        self.initial['address'] = company.address
        self.initial['postal_code'] = company.postcode

    def initial_to_data(self, field_name):
        self.data.setlist(
            self.add_prefix(field_name),
            [self.initial[field_name]]
        )

    def clean_date_of_creation(self):
        return self.cleaned_data['date_of_creation'].isoformat()

    def clean_address(self):
        address_parts = self.cleaned_data['address'].split(',')
        for i, address_part in enumerate(address_parts, start=1):
            field_name = f'address_line_{i}'
            self.cleaned_data[field_name] = address_part.strip()
        return self.cleaned_data['address']

    def clean_sectors(self):
        return [self.cleaned_data['sectors']]


class SoleTraderSearch(forms.Form):

    MESSAGE_INVALID_ADDRESS = 'Address should be at least two lines.'

    company_type = forms.ChoiceField(
        label='Business category',
        choices=[
            (value, label) for value, label in choices.COMPANY_TYPES
            if value != 'COMPANIES_HOUSE'
        ]
    )
    company_name = forms.CharField(
        label='Business name'
    )
    postal_code = forms.CharField(
        label='Business postcode',
        widget=PostcodeInput,
    )
    address = forms.CharField(
        help_text='Type your business address',
        widget=Textarea(attrs={'rows': 4}),
        required=False,
    )
    sectors = forms.ChoiceField(
        label='What industry is your business in?',
        choices=INDUSTRY_CHOICES,
    )
    website = forms.URLField(
        label='What\'s your business web address (optional)',
        help_text='The website address must start with http:// or https://',
        required=False,
    )

    def clean_sectors(self):
        return [self.cleaned_data['sectors']]

    def clean_address(self):
        value = self.cleaned_data['address'].strip().replace(', ', '\n')
        parts = value.split('\n')

        postal_code = self.cleaned_data['postal_code']
        if value.count('\n') == 0:
            raise ValidationError(self.MESSAGE_INVALID_ADDRESS)
        if postal_code not in value:
            value = f'{value}\n{postal_code}'
        self.cleaned_data['address_line_1'] = parts[0].strip()
        self.cleaned_data['address_line_2'] = parts[1].strip()
        return value


class ResendVerificationCode(forms.Form):
    email = forms.EmailField(
        label='Your email address'
    )
