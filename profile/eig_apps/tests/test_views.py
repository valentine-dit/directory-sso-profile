from django.core.urlresolvers import reverse

from profile.eig_apps import views


SIGN_OUT_LABEL = '>Sign out<'


def test_about_view_exposes_context_and_template(client):
    response = client.get(reverse('about'))

    assert response.context_data['about_tab_classes'] == 'active'
    assert response.template_name == [views.AboutView.template_name]


def test_not_signed_in_does_not_display_email(client):
    response = client.get(reverse('about'))

    assert 'You are signed in as' not in str(response.content)
    assert SIGN_OUT_LABEL not in str(response.content)
