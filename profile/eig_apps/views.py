from django.views.generic import RedirectView, TemplateView


class LandingPageView(RedirectView):
    pattern_name = 'about'


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self):
        return {
            'about_tab_classes': 'active'
        }
