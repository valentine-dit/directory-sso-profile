from requests.exceptions import HTTPError

from django.conf import settings
from django.views.generic import TemplateView

from profile.eig_apps.views import RedirectToAboutPageMixin
from profile.exops import helpers
from sso.utils import SSOLoginRequiredMixin


class ExportOpportunitiesBaseView(
    RedirectToAboutPageMixin, SSOLoginRequiredMixin, TemplateView
):
    template_name_not_exops_user = 'exops/is-not-exops-user.html'
    template_name_error = 'exops/opportunities-retrieve-error.html'

    opportunities = None
    opportunities_retrieve_error = False

    def dispatch(self, request, *args, **kwargs):
        if request.sso_user is None:
            return self.handle_no_permission()
        sso_id = request.sso_user.id
        try:
            self.opportunities = helpers.get_opportunities(sso_id)
        except HTTPError:
            self.opportunities_retrieve_error = True
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        if self.opportunities is not None:
            template_name = self.template_name_exops_user
        elif self.opportunities_retrieve_error is True:
            template_name = self.template_name_error
        else:
            template_name = self.template_name_not_exops_user
        return [template_name]

    def get_context_data(self):
        search_url = settings.EXPORTING_OPPORTUNITIES_SEARCH_URL
        return {
            'exops_tab_classes': 'active',
            'opportunities': self.opportunities,
            'EXPORTING_OPPORTUNITIES_SEARCH_URL': search_url,
        }


class ExportOpportunitiesApplicationsView(ExportOpportunitiesBaseView):
    template_name_exops_user = 'exops/is-exops-user-applications.html'


class ExportOpportunitiesEmailAlertsView(ExportOpportunitiesBaseView):
    template_name_exops_user = 'exops/is-exops-user-email-alerts.html'
