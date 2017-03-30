from requests.exceptions import HTTPError

from django.views.generic import TemplateView
from django.conf import settings

from profile.fab import helpers
from sso.utils import SSOLoginRequiredMixin


class FindABuyerView(SSOLoginRequiredMixin, TemplateView):
    template_name_fab_user = 'fab/is-fab-user.html'
    template_name_not_fab_user = 'fab/is-not-fab-user.html'
    template_name_error = 'fab/supplier-company-retrieve-error.html'

    company = None
    company_retrieve_error = False

    def dispatch(self, request, *args, **kwargs):
        if request.sso_user is None:
            return self.handle_no_permission()
        sso_id = request.sso_user.id
        try:
            self.company = helpers.get_supplier_company_profile(sso_id)
        except HTTPError:
            self.company_retrieve_error = True
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        if self.company is not None:
            template_name = self.template_name_fab_user
        elif self.company_retrieve_error is True:
            template_name = self.template_name_error
        else:
            template_name = self.template_name_not_fab_user
        return [template_name]

    def get_context_data(self):
        return {
            'fab_tab_classes': 'active',
            'company': self.company,
            'FAB_EDIT_COMPANY_LOGO_URL': settings.FAB_EDIT_COMPANY_LOGO_URL,
            'FAB_EDIT_PROFILE_URL': settings.FAB_EDIT_PROFILE_URL,
            'FAB_ADD_CASE_STUDY_URL': settings.FAB_ADD_CASE_STUDY_URL,
        }
