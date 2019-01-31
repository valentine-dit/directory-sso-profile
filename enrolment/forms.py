from captcha.fields import ReCaptchaField
from directory_components import forms, fields, widgets
from directory_constants.constants import choices, urls

from django.forms import PasswordInput
from django.utils.safestring import mark_safe

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

    def clean(self):
        cleaned_data = super(UserAccount, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("password_confirmed")

        if password != confirm_password:
            self.add_error('password_confirmed', "Passwords don't match")

        return cleaned_data


class UserAccountVerification(forms.Form):
    code = fields.CharField(label='')


class CompaniesHouseSearch(forms.Form):
    company_name = fields.CharField(
        label='Registered company name'
    )
    company_number = fields.CharField()


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
