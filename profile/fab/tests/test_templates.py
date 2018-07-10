from django.conf import settings
from django.template.loader import render_to_string

import pytest


def test_company_with_logo():
    context = {
        'company': {'logo': 'logo.png'},
    }
    html = render_to_string('fab/is-fab-user.html', context)

    assert 'logo.png' in html
    assert 'logo-placeholder.png' not in html


def test_company_without_logo():
    context = {
        'company': {'logo': None},
    }
    html = render_to_string('fab/is-fab-user.html', context)
    assert 'company-logo-placeholder' in html


@pytest.mark.parametrize('url,count', (
    (settings.FAB_ADD_USER_URL, 1),
    (settings.FAB_REMOVE_USER_URL, 1),
    (settings.FAB_TRANSFER_ACCOUNT_URL, 1),
))
def test_multi_user_feature_flag_links_owner(url, count, settings):
    context = {
        'FAB_ADD_USER_URL': settings.FAB_ADD_USER_URL,
        'FAB_REMOVE_USER_URL': settings.FAB_REMOVE_USER_URL,
        'FAB_TRANSFER_ACCOUNT_URL': settings.FAB_TRANSFER_ACCOUNT_URL,
        'is_profile_owner': True,
    }

    html = render_to_string('fab/is-fab-user.html', context)
    assert html.count(str(url)) == count


@pytest.mark.parametrize('url,count', (
    (settings.FAB_ADD_USER_URL, 1),
    (settings.FAB_REMOVE_USER_URL, 1),
    (settings.FAB_TRANSFER_ACCOUNT_URL, 1),
))
def test_multi_user_feature_flag_links_non_owner(url, count, settings):
    context = {
        'FAB_ADD_USER_URL': settings.FAB_ADD_USER_URL,
        'FAB_REMOVE_USER_URL': settings.FAB_REMOVE_USER_URL,
        'FAB_TRANSFER_ACCOUNT_URL': settings.FAB_TRANSFER_ACCOUNT_URL,
        'is_profile_owner': False,
    }

    html = render_to_string('fab/is-fab-user.html', context)
    assert html.count(str(url)) == count
