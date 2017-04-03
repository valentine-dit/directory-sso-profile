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


def test_signed_in_as_displays_email(client, sso_user_middleware):
    response = client.get(reverse('about'))

    assert 'You are signed in as jim@example.com' in str(response.content)


def test_not_signed_in_does_not_display_email(client):
    response = client.get(reverse('about'))

    assert 'You are signed in as' not in str(response.content)
