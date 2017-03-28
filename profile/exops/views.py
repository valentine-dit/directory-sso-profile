from django.views.generic import TemplateView

from sso.utils import SSOLoginRequiredMixin


class ExportOpportunitiesView(SSOLoginRequiredMixin, TemplateView):
    template_name = 'export-opportunities.html'

    def get_context_data(self):
        return {
            'exops_tab_classes': 'active',
        }
