import os

from directory_api_client.client import api_client
from formtools.wizard.views import NamedUrlSessionWizardView
from raven.contrib.django.raven_compat.models import client as sentry_client
from requests.exceptions import HTTPError

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect
from django.utils.functional import cached_property
from django.views.generic import TemplateView, FormView

from profile.eig_apps.views import RedirectToAboutPageMixin
from profile.fab import forms, helpers
from sso.utils import SSOLoginRequiredMixin


class CompanyProfileMixin:
    @cached_property
    def company(self):
        return helpers.get_company_profile(self.request.sso_user.session_id)


class FindABuyerView(
    RedirectToAboutPageMixin, SSOLoginRequiredMixin, CompanyProfileMixin,
    TemplateView
):
    template_name_fab_user = 'fab/is-fab-user.html'
    template_name_not_fab_user = 'fab/is-not-fab-user.html'

    SUCCESS_MESSAGES = {
        'owner-transferred': (
            'We’ve sent a confirmation email to the new profile owner.'
        ),
        'user-added': (
            'We’ve sent an invitation to the user you want added to your '
            'profile.'
        ),
        'user-removed': 'User successfully removed from your profile.'
    }

    def dispatch(self, request, *args, **kwargs):
        if request.sso_user is None:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        if self.company is not None:
            if settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON']:
                template_name = 'fab/profile.html'
            else:
                template_name = self.template_name_fab_user
        else:
            template_name = self.template_name_not_fab_user
        return [template_name]

    def is_company_profile_owner(self):
        if not self.company:
            return False
        response = api_client.supplier.retrieve_profile(
            sso_session_id=self.request.sso_user.session_id,
        )
        response.raise_for_status()
        parsed = response.json()
        return parsed['is_company_owner']

    def get_context_data(self):
        return {
            'fab_tab_classes': 'active',
            'is_profile_owner': self.is_company_profile_owner(),
            'company': self.company,
            'FAB_EDIT_COMPANY_LOGO_URL': settings.FAB_EDIT_COMPANY_LOGO_URL,
            'FAB_EDIT_PROFILE_URL': settings.FAB_EDIT_PROFILE_URL,
            'FAB_ADD_CASE_STUDY_URL': settings.FAB_ADD_CASE_STUDY_URL,
            'FAB_REGISTER_URL': settings.FAB_REGISTER_URL,
            'FAB_ADD_USER_URL': settings.FAB_ADD_USER_URL,
            'FAB_REMOVE_USER_URL': settings.FAB_REMOVE_USER_URL,
            'FAB_TRANSFER_ACCOUNT_URL': settings.FAB_TRANSFER_ACCOUNT_URL,
            'success_message': self.get_success_messages()
        }

    def get_success_messages(self):
        for key, value in self.SUCCESS_MESSAGES.items():
            if key in self.request.GET:
                return value


class BaseFormView(CompanyProfileMixin, FormView):
    def get_initial(self):
        return self.company

    def form_valid(self, form):
        response = api_client.company.update_profile(
            sso_session_id=self.request.sso_user.session_id,
            data=self.serialize_form(form)
        )
        try:
            response.raise_for_status()
        except HTTPError:
            self.send_update_error_to_sentry(
                sso_user=self.request.sso_user,
                api_response=response
            )
            raise
        else:
            return redirect('find-a-buyer')

    def serialize_form(self, form):
        return form.cleaned_data

    @staticmethod
    def send_update_error_to_sentry(sso_user, api_response):
        # This is needed to not include POST data (e.g. binary image), which
        # was causing sentry to fail at sending
        sentry_client.context.clear()
        sentry_client.user_context(
            {'sso_id': sso_user.id, 'sso_user_email': sso_user.email}
        )
        sentry_client.captureMessage(
            message='Updating company profile failed',
            data={},
            extra={'api_response': str(api_response.content)}
        )


class SocialLinksFormView(BaseFormView):
    template_name = 'fab/social-links-form.html'
    form_class = forms.SocialLinksForm


class EmailAddressFormView(BaseFormView):
    template_name = 'fab/email-address-form.html'
    form_class = forms.EmailAddressForm


class DescriptionFormView(BaseFormView):
    form_class = forms.DescriptionForm
    template_name = 'fab/description-form.html'


class LogoFormView(BaseFormView):
    form_class = forms.LogoForm
    template_name = 'fab/logo-form.html'


class BaseCaseStudyWizardView(NamedUrlSessionWizardView):
    done_step_name = 'finished'

    BASIC = 'details'
    RICH_MEDIA = 'images'

    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'tmp-supplier-media')
    )

    form_list = (
        (BASIC, forms.CaseStudyBasicInfoForm),
        (RICH_MEDIA, forms.CaseStudyRichMediaForm),
    )
    templates = {
        BASIC: 'fab/case-study-basic-form.html',
        RICH_MEDIA: 'fab/case-study-media-form.html',
    }

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def serialize_form_data(self, form_list):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)
        # the case studies edit view pre-populates the image fields with the
        # url of the existing value (rather than the real file). Things would
        # get confused if we send a string instead of a file here.
        for field in ['image_one', 'image_two', 'image_three']:
            if isinstance(data.get(field), str):
                del data[field]
        return data


class CaseStudyWizardEditView(BaseCaseStudyWizardView):
    def get_form_initial(self, step):
        response = api_client.company.retrieve_private_case_study(
            sso_session_id=self.request.sso_user.session_id,
            case_study_id=self.kwargs['id'],
        )
        if response.status_code == 404:
            raise Http404()
        response.raise_for_status()
        return response.json()

    def done(self, *args, **kwags):
        response = api_client.company.update_case_study(
            data=self.serialize_form_data(),
            case_study_id=self.kwargs['id'],
            sso_session_id=self.request.sso_user.session_id,
        )
        response.raise_for_status()
        return redirect('find-a-buyer')


class CaseStudyWizardCreateView(BaseCaseStudyWizardView):
    def done(self, *args, **kwags):
        response = api_client.company.create_case_study(
            sso_session_id=self.request.sso_user.session_id,
            data=self.serialize_form_data(),
        )
        response.raise_for_status()
        return redirect('find-a-buyer')
