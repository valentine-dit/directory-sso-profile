from django.views.generic import TemplateView

from sso.utils import SSOLoginRequiredMixin


class LandingPageView(SSOLoginRequiredMixin, TemplateView):
    template_name = 'landing-page.html'
