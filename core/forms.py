from directory_constants import urls
from directory_components import forms

from django.utils.safestring import mark_safe


TERMS_LABEL = mark_safe(
    'Tick this box to accept the '
    f'<a href="{urls.TERMS_AND_CONDITIONS}" target="_blank">terms and '
    'conditions</a> of the great.gov.uk service.'
)


class PersonalDetails(forms.Form):

    given_name = forms.CharField(
        label='First name',
    )
    family_name = forms.CharField(
        label='Last name',
    )
    job_title = forms.CharField()
    phone_number = forms.CharField(
        label='Phone number (optional)',
        required=False
    )
    confirmed_is_company_representative = forms.BooleanField(
        label=(
            'I confirm that I have the right to act for this business. I '
            'understand that great.gov.uk might write to this business to '
            'confirm I can create an account.'
        )
    )
    terms_agreed = forms.BooleanField(label=TERMS_LABEL)
