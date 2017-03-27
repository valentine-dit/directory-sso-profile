from django.views.generic import TemplateView


class ExportOpportunitiesView(TemplateView):
    template_name = 'export-opportunities.html'

    def get_context_data(self):
        return {
            'exops_tab_classes': 'active',
        }
