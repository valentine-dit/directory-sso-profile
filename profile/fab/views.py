from django.views.generic import TemplateView


class FindABuyerView(TemplateView):
    template_name = 'find-a-buyer.html'

    def get_context_data(self):
        return {
            'sso_user_email': self.request.sso_user.email,
            'fab_tab_classes': 'active',
        }
