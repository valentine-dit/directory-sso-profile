from django.views.generic import TemplateView


class LandingPageView(TemplateView):
    template_name = 'landing-page.html'


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self):
        return {
            'about_tab_classes': 'active'
        }
