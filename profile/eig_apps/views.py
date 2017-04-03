from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import RedirectView

from profile.eig_apps import constants


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self):
        return {
            'about_tab_classes': 'active'
        }


class LandingPageView(RedirectView):
    pattern_name = 'about'


class RedirectToAboutPageMixin:
    def dispatch(self, request, *args, **kwargs):
        has_visited = constants.HAS_VISITED_ABOUT_PAGE_SESSION_KEY
        if has_visited not in request.session:
            return redirect(reverse('about'))
        return super().dispatch(request, *args, **kwargs)
