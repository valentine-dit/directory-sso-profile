from django.views.generic import TemplateView


class LandingPageView(TemplateView):
    template_name = 'landing-page.html'

    def get_context_data(self):
    	return {
    		'sso_user_email': self.request.sso_user.email
    	}
