from django.views.generic import TemplateView

from sso.utils import SSOLoginRequiredMixin


class SellingOnlineOverseasView(SSOLoginRequiredMixin, TemplateView):
    template_name = 'selling-online-overseas.html'

    def get_context_data(self):
        return {
            'soo_tab_classes': 'active'
        }
