from requests.exceptions import HTTPError

from django.views.generic import TemplateView

from profile.exops import helpers
from sso.utils import SSOLoginRequiredMixin


class ExportOpportunitiesView(SSOLoginRequiredMixin, TemplateView):
    template_name_exops_user = 'exops/is-exops-user.html'
    template_name_not_exops_user = 'exops/is-not-exops-user.html'
    template_name_error = 'exops/opportunities-retrieve-error.html'

    opportunities = None
    opportunities_retrieve_error = False

    def dispatch(self, request, *args, **kwargs):
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
        return {
            'exops_tab_classes': 'active',
            'opportunities': self.opportunities,
        }
