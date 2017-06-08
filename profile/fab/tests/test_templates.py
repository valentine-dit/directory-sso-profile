from django.template.loader import render_to_string


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
