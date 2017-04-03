import http

from django.core.urlresolvers import reverse

from profile.eig_apps import views
from profile.eig_apps import constants


def test_about_view_exposes_context_and_template(client):
    response = client.get(reverse('about'))

    assert response.context_data['about_tab_classes'] == 'active'
    assert response.template_name == [views.AboutView.template_name]


def test_about_view_sets_session(client):
    client.get(reverse('about'))
    session_key = constants.HAS_VISITED_ABOUT_PAGE_SESSION_KEY

    assert client.session[session_key] == 'true'


def test_landing_page_redirect(client):
    response = client.get(reverse('index'))

    assert response.status_code == http.client.FOUND
    assert response.get('Location') == reverse('about')
