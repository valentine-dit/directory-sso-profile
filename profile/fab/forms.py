from directory_components import fields, forms
import directory_validators.company
import directory_validators.enrolment

from django.conf import settings
from django.forms import ImageField, Textarea

from profile.fab import validators


class SocialLinksForm(forms.Form):
    HELP_URLS = 'Use a full web address (URL) including http:// or https://'

    facebook_url = fields.URLField(
        label='URL for your Facebook company page (optional):',
        help_text=HELP_URLS,
        max_length=255,
        required=False,
        validators=[
            directory_validators.company.case_study_social_link_facebook
        ],
    )
    twitter_url = fields.URLField(
        label='URL for your Twitter company profile (optional):',
        help_text=HELP_URLS,
        max_length=255,
        required=False,
        validators=[
            directory_validators.company.case_study_social_link_twitter
        ],
    )
    linkedin_url = fields.URLField(
        label='URL for your LinkedIn company profile (optional):',
        help_text=HELP_URLS,
        max_length=255,
        required=False,
        validators=[
            directory_validators.company.case_study_social_link_linkedin
        ],
    )


class EmailAddressForm(forms.Form):
    email_address = fields.EmailField(
        label='Email address'
    )


class DescriptionForm(forms.Form):
    summary = fields.CharField(
        label='Brief summary to make your company stand out to buyers:',
        help_text='Maximum 250 characters.',
        max_length=250,
        widget=Textarea(attrs={'rows': 5}),
        validators=[
            validators.does_not_contain_email,
            directory_validators.company.no_html,
        ],
    )
    description = fields.CharField(
        label='Describe your business to overseas buyers:',
        help_text='Maximum 2,000 characters.',
        max_length=2000,
        widget=Textarea(attrs={'rows': 5}),
        validators=[
            validators.does_not_contain_email,
            directory_validators.company.no_html,
        ],
    )


class LogoForm(forms.Form):
    logo = ImageField(
        help_text=(
            'For best results this should be a transparent PNG file of 600 x '
            '600 pixels and no more than 2MB'.format(
                int(settings.VALIDATOR_MAX_LOGO_SIZE_BYTES / 1024 / 1014)
            )
        ),
        required=True,
        validators=[
            directory_validators.enrolment.logo_filesize,
            directory_validators.company.image_format,
        ]
    )
