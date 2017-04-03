from django.views.generic import TemplateView

from profile.eig_apps.views import RedirectToAboutPageMixin
from sso.utils import SSOLoginRequiredMixin


class SellingOnlineOverseasView(
    RedirectToAboutPageMixin, SSOLoginRequiredMixin, TemplateView
):
    template_name = 'selling-online-overseas.html'

    def get_context_data(self):
        return {
            'soo_tab_classes': 'active',
        }
