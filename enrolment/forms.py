from captcha.fields import ReCaptchaField
from directory_components import forms, fields, widgets
from directory_constants.constants import choices, urls
from requests.exceptions import HTTPError
from directory_validators.company import (
    no_company_with_insufficient_companies_house_data as compant_type_validator
)
from directory_validators.enrolment import (
    company_number as company_number_validator
)

from django.forms import HiddenInput, PasswordInput, Textarea, ValidationError
from django.utils.safestring import mark_safe
from django.http.request import QueryDict

from enrolment import constants, helpers
from enrolment.fields import DateField


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
    choice = fields.ChoiceField(
        label='',
        widget=widgets.RadioSelect(),
        choices=CHOICES,
    )


class UserAccount(forms.Form):
    PASSWORD_HELP_TEXT = (
        '<p>Your password must:</p>'
        '<ul class="list list-bullet">'
        '<li>be at least 10 characters</li>'
        '<li>contain at least 1 letter</li>'
        '<li>contain at least 1 number</li>'
        '<li>not contain the word "password"</li>'
        '</ul>'
    )
    MESSAGE_NOT_MATCH = "Passwords don't match"
    MESSAGE_PASSWORD_INVALID = 'Invalid Password'

    email = fields.EmailField(
        label='Your email address'
    )
    password = fields.CharField(
        help_text=mark_safe(PASSWORD_HELP_TEXT),
        widget=PasswordInput
    )
    password_confirmed = fields.CharField(
        label='Confirm password',
        widget=PasswordInput,
    )

    captcha = ReCaptchaField(
        label='',
        label_suffix='',
    )

    terms_agreed = fields.BooleanField(
        label=mark_safe(
            'Tick this box to accept the '
            f'<a href="{urls.TERMS_AND_CONDITIONS}" target="_blank">terms and '
            'conditions</a> of the great.gov.uk service.'
        ),
    )

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

    email = fields.CharField(label='', widget=HiddenInput, disabled=True)
    code = fields.CharField(
        label='',
        min_length=5,
        max_length=5,
        error_messages={'required': MESSAGE_INVALID_CODE}
    )


class CompaniesHouseSearch(forms.Form):
    MESSAGE_COMPANY_NOT_FOUND = (
        "<p>Your business name is not listed.</p>"
        "<p>Check that you've entered the right name.</p>"
    )
    MESSAGE_COMPANY_NOT_ACTIVE = 'Company not active.'
    company_name = fields.CharField(
        label='Registered company name',
    )
    company_number = fields.CharField(
        validators=[company_number_validator],
    )

    def __init__(self, session, *args, **kwargs):
        self.session = session
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if 'company_number' in cleaned_data:
            try:
                compant_type_validator(cleaned_data['company_number'])
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
    company_name = fields.CharField(
        label='Registered company name'
    )
    company_number = fields.CharField(
        disabled=True,
        required=False,
    )
    sic = fields.CharField(
        label='Nature of business',
        disabled=True,
        required=False,
    )
    date_of_creation = DateField(
        label='Incorporated on',
        input_formats=['%m %B %Y'],
        disabled=True,
        required=False,
    )
    postal_code = fields.CharField(
        label='Business postcode',
        required=False,
    )
    address = fields.CharField(
        disabled=True,
        required=False,
    )
    sectors = fields.ChoiceField(
        label='What industry is your company in?',
        choices=INDUSTRY_CHOICES,
    )
    website = fields.URLField(
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
        company = helpers.CompanyProfileFormatter(company_profile)
        self.initial['company_name'] = company.name
        self.initial['company_number'] = company.number
        self.initial['sic'] = company.sic_code
        self.initial['date_of_creation'] = company.date_created
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


class PersonalDetails(forms.Form):

    given_name = fields.CharField(
        label='First name',
    )
    family_name = fields.CharField(
        label='Last name',
    )
    job_title = fields.CharField()
    phone_number = fields.CharField(
        label='Phone number (optional)',
        required=False
    )
    confirmed_is_company_representative = fields.BooleanField(
        label=(
            'I confirm that I have the right to act for this business. I '
            'understand that great.gov.uk might write to this business to '
            'confirm I can create an account.'
        )
    )


class SoleTraderSearch(forms.Form):

    MESSAGE_INVALID_ADDRESS = 'Address should be at least two lines.'

    company_name = fields.CharField(
        label='Business name'
    )
    postal_code = fields.CharField(
        label='Business postcode',
    )
    address = fields.CharField(
        help_text='Type your business address',
        widget=Textarea(attrs={'rows': 4}),
    )

    def clean_address(self):
        value = self.cleaned_data['address'].strip().replace(', ', '\n')
        postal_code = self.cleaned_data['postal_code']
        if value.count('\n') == 0:
            raise ValidationError(self.MESSAGE_INVALID_ADDRESS)
        if postal_code not in value:
            value = f'{value}\n{postal_code}'
        return value


class SoleTraderBusinessDetails(forms.Form):
    company_name = fields.CharField(
        label='Business name'
    )
    postal_code = fields.CharField(
        label='Business postcode',
        required=False,
        disabled=True
    )
    address = fields.CharField(
        disabled=True,
        required=False,
        widget=Textarea(attrs={'rows': 3}),
    )
    sectors = fields.ChoiceField(
        label='What industry is your business in?',
        choices=INDUSTRY_CHOICES,
    )
    website = fields.URLField(
        label='What\'s your business web address (optional)',
        help_text='The website address must start with http:// or https://',
        required=False,
    )

    def __init__(self, initial, *args, **kwargs):
        super().__init__(initial=initial, *args, **kwargs)
        # force the form to use the initial value rather than the value
        # the user submitted in previous sessions
        # on GET the data structure is a MultiValueDict. on POST the data
        # structure is a QueryDict
        if self.data and not isinstance(self.data, QueryDict):
            self.initial_to_data('company_name')
            self.initial_to_data('postal_code')
            self.initial_to_data('address')

    def initial_to_data(self, field_name):
        self.data.setlist(
            self.add_prefix(field_name),
            [self.initial[field_name]]
        )

    def clean_address(self):
        address_parts = self.cleaned_data['address'].split('\n')
        self.cleaned_data['address_line_1'] = address_parts[0].strip()
        self.cleaned_data['address_line_2'] = address_parts[1].strip()
        return self.cleaned_data['address']

    def clean_sectors(self):
        return [self.cleaned_data['sectors']]


class ResendVerificationCode(forms.Form):
    email = fields.EmailField(
        label='Your email address'
    )
