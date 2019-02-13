from directory_api_external.client import api_client
from requests.exceptions import HTTPError

from django.conf import settings
from django.views.generic import TemplateView

from profile.eig_apps.views import RedirectToAboutPageMixin
from profile.fab import helpers
from sso.utils import SSOLoginRequiredMixin


class FindABuyerView(
    RedirectToAboutPageMixin, SSOLoginRequiredMixin, TemplateView
):
    template_name_fab_user = 'fab/is-fab-user.html'
    template_name_not_fab_user = 'fab/is-not-fab-user.html'
    template_name_error = 'fab/supplier-company-retrieve-error.html'

    company = None
    company_retrieve_error = False

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
        sso_session_id = request.sso_user.session_id
        try:
            self.company = helpers.get_supplier_company_profile(sso_session_id)
        except HTTPError:
            self.company_retrieve_error = True
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        if self.company is not None:
            if settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON']:
                template_name = 'fab/profile.html'
            else:
                template_name = self.template_name_fab_user
        elif self.company_retrieve_error is True:
            template_name = self.template_name_error
        else:
            template_name = self.template_name_not_fab_user
        return [template_name]

    def is_company_profile_owner(self):
        if not self.company:
            return False
        response = api_client.supplier.retrieve_supplier(
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
