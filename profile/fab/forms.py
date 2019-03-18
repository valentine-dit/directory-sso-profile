from directory_constants.constants import choices
from directory_components import fields, forms
import directory_validators.company
import directory_validators.enrolment

from django.conf import settings
from django.forms import ImageField, Textarea

from enrolment.fields import DateField
from profile.fab import validators


INDUSTRY_CHOICES = [('', 'Select Industry')] + list(choices.INDUSTRIES)


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


class CaseStudyBasicInfoForm(forms.Form):
    title = fields.CharField(
        label='Showcase title',
        max_length=60,
        validators=[directory_validators.company.no_html],
    )
    short_summary = fields.CharField(
        label='Summary of your case study or project',
        help_text=(
            'Summarise your case study in 200 characters or fewer. This will'
            ' appear on your main business profile page.'
        ),
        max_length=200,
        validators=[
            validators.does_not_contain_email,
            directory_validators.company.no_html,
        ],
        widget=Textarea,
    )
    description = fields.CharField(
        label='Describe your case study or project',
        help_text=(
            'Describe the project or case study in 1,000 characters or fewer. '
            'Use this space to demonstrate the value of your '
            'company to an international business audience.'
        ),
        max_length=1000,
        validators=[
            validators.does_not_contain_email,
            directory_validators.company.no_html,
        ],
        widget=Textarea,
    )
    sector = fields.ChoiceField(
        label='Industry most relevant to your showcase',
        choices=INDUSTRY_CHOICES
    )
    website = fields.URLField(
        label='The web address for your case study (optional)',
        help_text='Enter a full URL including http:// or https://',
        max_length=255,
        required=False,
    )
    keywords = fields.CharField(
        label=(
            'Enter up to 10 keywords that describe your case study. '
            'Keywords should be separated by commas.'
        ),
        help_text=(
            'These keywords will be used to help potential overseas buyers '
            'find your case study.'
        ),
        max_length=1000,
        widget=Textarea,
        validators=[
            directory_validators.company.keywords_word_limit,
            directory_validators.company.keywords_special_characters,
            directory_validators.company.no_html,
        ]
    )


class DynamicHelptextFieldsMixin:
    """
    Set the help_text and label to different values depending on if
    the field has an initial value.

    """

    def __init__(self, *args, **kwargs):
        assert hasattr(self, 'help_text_maps')
        super().__init__(*args, **kwargs)
        self.set_help_text()

    def set_help_text(self):
        for help_text_map in self.help_text_maps:
            field = self[help_text_map['field_name']]
            if self.initial.get(field.name):
                help_text = help_text_map['update_help_text'].format(
                    initial_value=self.initial.get(field.name)
                )
                field.help_text = help_text
                field.label = help_text_map['update_label']
            else:
                field.help_text = help_text_map['create_help_text']
                field.label = help_text_map['create_label']


class CaseStudyRichMediaForm(DynamicHelptextFieldsMixin, forms.Form):

    image_help_text_create = (
        'This image will be shown at full width on your case study page and '
        'must be at least 700 pixels wide and in landscape format. For best '
        'results, upload an image at 1820 x 682 pixels.'
    )
    image_help_text_update = (
        'Select a different image to replace the '
        '<a href="{initial_value}" target="_blank" alt="View current image">'
        'current one</a>. ' + image_help_text_create
    )
    help_text_maps = [
        {
            'field_name': 'image_one',
            'create_help_text': image_help_text_create,
            'update_help_text': image_help_text_update,
            'create_label': 'Upload a main image for this case study',
            'update_label': (
                'Replace the main image for this case study (optional)'
            )
        },
        {
            'field_name': 'image_two',
            'create_help_text': image_help_text_create,
            'update_help_text': image_help_text_update,
            'create_label': 'Upload a second image (optional)',
            'update_label': 'Replace the second image (optional)',
        },
        {
            'field_name': 'image_three',
            'create_help_text': image_help_text_create,
            'update_help_text': image_help_text_update,
            'create_label': 'Upload a third image (optional)',
            'update_label': 'Replace the third image (optional)',
        },
    ]

    image_one = ImageField(
        validators=[
            directory_validators.company.case_study_image_filesize,
            directory_validators.company.image_format,
        ],
    )
    image_one_caption = fields.CharField(
        label=(
            'Add a caption that tells visitors what the main image represents'
        ),
        help_text='Maximum 120 characters',
        max_length=120,
        widget=Textarea,
        validators=[directory_validators.company.no_html],
    )
    image_two = ImageField(
        required=False,
        validators=[
            directory_validators.company.case_study_image_filesize,
            directory_validators.company.image_format,
        ]
    )
    image_two_caption = fields.CharField(
        label=(
            'Add a caption that tells visitors what this second image '
            'represents'
        ),
        help_text='Maximum 120 characters',
        max_length=120,
        widget=Textarea,
        required=False,
        validators=[directory_validators.company.no_html],
    )
    image_three = ImageField(
        required=False,
        validators=[
            directory_validators.company.case_study_image_filesize,
            directory_validators.company.image_format,
        ]
    )
    image_three_caption = fields.CharField(
        label=(
            'Add a caption that tells visitors what this third image '
            'represents'
        ),
        help_text='Maximum 120 characters',
        max_length=120,
        widget=Textarea,
        required=False,
        validators=[directory_validators.company.no_html],
    )
    testimonial = fields.CharField(
        label='Testimonial or block quote (optional)',
        help_text=(
            'Add testimonial from a satisfied client or use this space'
            ' to highlight an important part of your case study.'
        ),
        max_length=1000,
        required=False,
        widget=Textarea,
        validators=[directory_validators.company.no_html],
    )
    testimonial_name = fields.CharField(
        label='Full name of the source of the testimonial (optional)',
        help_text=(
            'Add the source to make the quote more credible and to '
            'help buyers understand the importance of the testimonial.'
        ),
        max_length=255,
        required=False,
        validators=[directory_validators.company.no_html],
    )
    testimonial_job_title = fields.CharField(
        label='Job title of the source (optional)',
        max_length=255,
        required=False,
        validators=[directory_validators.company.no_html],
    )
    testimonial_company = fields.CharField(
        label="Company name of the source (optional)",
        max_length=255,
        required=False,
        validators=[directory_validators.company.no_html],
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


class ProductsServicesForm(forms.Form):
    keywords = fields.CharField(
        label=(
            'Enter up to 10 keywords that describe your company '
            '(separated by commas):'
        ),
        help_text=(
            'These keywords will be used to help potential overseas buyers '
            'find your company.'
        ),
        widget=Textarea,
        max_length=1000,
        validators=[
            directory_validators.company.keywords_word_limit,
            directory_validators.company.keywords_special_characters,
            directory_validators.company.no_html,
        ]
    )


class PublishForm(forms.Form):

    LABEL_UNPUBLISH_FAS = 'Untick to remove your profile from this service'
    LABEL_UNPUBLISH_ISD = 'Untick the box to cancel publication'
    LABEL_ISD = 'Ready to publish on UK Investment Support Directory'
    LABEL_FAS = 'Publish profile on great.gov.uk/trade/'

    def __init__(self, company, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if company.get('is_published_investment_support_directory'):
            field = self.fields['is_published_investment_support_directory']
            field.widget.label = self.LABEL_UNPUBLISH_ISD
        if company.get('is_published_find_a_supplier'):
            field = self.fields['is_published_find_a_supplier']
            field.widget.label = self.LABEL_UNPUBLISH_FAS

    is_published_investment_support_directory = fields.BooleanField(
        label=LABEL_ISD,
        required=False
    )
    is_published_find_a_supplier = fields.BooleanField(
        label=LABEL_FAS,
        required=False
    )


class CompaniesHouseBusinessDetailsForm(forms.Form):
    name = fields.CharField(
        label='Trading name'
    )
    number = fields.CharField(
        disabled=True,
    )
    date_of_creation = DateField(
        label='Incorporated on',
        input_formats=['%d %B %Y'],
        disabled=True,
        required=False,
    )
    address = fields.CharField(
        disabled=True,
        required=False,
    )
    website = fields.URLField(
        label='Business URL (optional)',
        help_text='The website address must start with http:// or https://',
        required=False,
    )
    employees = fields.ChoiceField(
        choices=choices.EMPLOYEES,
        label='How many employees are in your business?',
    )
    sectors = fields.ChoiceField(
        label='What industry is your business in?',
        choices=INDUSTRY_CHOICES,
    )

    def clean_sectors(self):
        return [self.cleaned_data['sectors']]

    def clean(self):
        super().clean()
        self.cleaned_data.pop('clean_number', None)
        self.cleaned_data.pop('date_of_creation', None)


class SoleTraderBusinessDetailsForm(forms.Form):
    name = fields.CharField(
        label='Trading name'
    )
    address_line_1 = fields.CharField(
        required=False,
    )
    address_line_2 = fields.CharField(
        required=False,
    )
    locality = fields.CharField(
        required=False,
    )
    postal_code = fields.CharField(
        required=False,
    )

    website_address = fields.URLField(
        label='Business URL (optional)',
        help_text='The website address must start with http:// or https://',
        required=False,
    )
    employees = fields.ChoiceField(
        choices=choices.EMPLOYEES,
        label='How many employees are in your business?',
    )
    sectors = fields.ChoiceField(
        label='What industry is your business in?',
        choices=INDUSTRY_CHOICES,
    )

    def clean_sectors(self):
        return [self.cleaned_data['sectors']]
