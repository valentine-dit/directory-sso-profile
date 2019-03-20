from django.core.urlresolvers import reverse

from profile.eig_apps import views
from profile.eig_apps import constants


SIGN_OUT_LABEL = '>Sign out<'


def test_about_view_exposes_context_and_template(client):
    response = client.get(reverse('about'))

    assert response.context_data['about_tab_classes'] == 'active'
    assert response.template_name == [views.AboutView.template_name]


def test_about_view_sets_session(client):
    client.get(reverse('about'))
    session_key = constants.HAS_VISITED_ABOUT_PAGE_SESSION_KEY

    assert client.session[session_key] == 'true'


def test_signed_in_as_displays_email(client, sso_user_middleware, settings):
    settings.FEATURE_FLAGS['BUSINESS_PROFILE_ON'] = False

    response = client.get(reverse('about'))

    assert 'You are signed in as jim@example.com' in str(response.content)
    assert str(response.content).count(SIGN_OUT_LABEL) == 1


def test_not_signed_in_does_not_display_email(client):
    response = client.get(reverse('about'))

    assert 'You are signed in as' not in str(response.content)
    assert SIGN_OUT_LABEL not in str(response.content)
