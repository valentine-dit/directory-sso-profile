from django.template.loader import render_to_string


def test_new_header_footer_enabled():
    context = {
        'features': {
            'FEATURE_NEW_SHARED_HEADER_ENABLED': True,
        }
    }
    html = render_to_string('base.html', context)

    assert render_to_string('directory_header_footer/header.html') in html
    assert render_to_string('directory_header_footer/footer.html') in html


def test_new_header_footer_disabled():
    context = {
        'features': {
            'FEATURE_NEW_SHARED_HEADER_ENABLED': False,
        }
    }
    html = render_to_string('base.html', context)

    assert render_to_string('directory_header_footer/header_old.html') in html
    assert render_to_string('directory_header_footer/footer_old.html') in html
