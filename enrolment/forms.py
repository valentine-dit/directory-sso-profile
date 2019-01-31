from captcha.fields import ReCaptchaField
from directory_components import forms, fields, widgets
from directory_constants.constants import choices, urls

from django.forms import PasswordInput, ValidationError
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http.request import QueryDict

from enrolment import constants
from enrolment.fields import DateField


class BusinessType(forms.Form):
    CHOICES = (
        (
            constants.COMPANIES_HOUSE_COMPANY,
            (
                'A business registered with Companies House, for example, a '
                'limited company (ltd), a public limited company (PLC) or a '
                'Royal Charter company (RC)'
            )
        ),
        (
            constants.SOLE_TRADER,
            (
                'A UK sole trader or another type of UK business not '
                'registered with Companies House'
            )
        ),
        (
            constants.NOT_COMPANY,
            'I\'m a UK taxpayer but don\'t represent a business'
        ),
        (
            constants.OVERSEAS_COMPANY,
            'My business or organisation is not registered in the UK'
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
        '<li>contain at least one letter</li>'
        '<li>contain at least one number</li>'
        '<li>not contain the word "password"</li>'
        '</ul>'
    )

    email = fields.EmailField(
        label='Your email'
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
        )
    )


class UserAccountVerification(forms.Form):
    code = fields.CharField(label='')


class CompaniesHouseSearch(forms.Form):
    MESSAGE_COMPANY_NOT_FOUND = (
        "<p>Your company name can't be found.</p>"
        "<p>Check that you entered the registered company name correctly "
        "and select the matching company name from the list.</p>"
        "<p>If your company is not registered with Companies House "
        "<a href='{url}'>change type of business</a></p>"
    )

    company_name = fields.CharField(
        label='Registered company name'
    )
    company_number = fields.CharField()

    def clean(self):
        cleaned_data = super().clean()
        if 'company_number' not in cleaned_data:
            url = reverse('enrolment', kwargs={'step': 'business-type'})
            message = self.MESSAGE_COMPANY_NOT_FOUND.format(url=url)
            raise ValidationError({'company_name': mark_safe(message)})


class CompaniesHouseBusinessDetails(forms.Form):
    INDUSTRY_CHOICES = (
        (('', 'Please select'),) + choices.INDUSTRIES + (('OTHER', 'Other'),)
    )
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
    date_created = DateField(
        label='Incorporated on',
        input_formats=['%m %B %Y'],
        disabled=True,
        required=False,
    )
    address_finder = fields.CharField(
        required=False,
    )
    address = fields.CharField(
        disabled=True,
        required=False,
    )
    industry = fields.ChoiceField(
        label='What industry is your company in?',
        choices=INDUSTRY_CHOICES,
    )
    website_address = fields.URLField(
        label='Company website (optional)',
        help_text='The website address must start with http:// or https://',
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # force the form to use the initial value rather than the value
        # the user submitted in previous sessions
        # on GET the data structure is a MultiValueDict. on POST the data
        # structure is a QueryDict
        if not isinstance(self.data, QueryDict):
            self.data.setlist(
                self.add_prefix('company_name'),
                [self.initial['company_name']]
            )


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
        label='I verify that I am an official representative of...'
    )
    confirmed_background_checks = fields.BooleanField(
        label='I understand that DIT may run background checks...'
    )
