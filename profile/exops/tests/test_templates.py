from django.template.loader import render_to_string


def test_email_alert_with_term():
    context = {
        'opportunities': {
            'email_alerts': [
                {
                    'term': '--example term--',
                    'created_on': '2000-01-01T01:01:01.000001Z',
                }
            ],
        }
    }
    html = render_to_string('exops/is-exops-user-email-alerts.html', context)

    assert '--example term--' in html


def test_email_alert_without_term():
    context = {
        'opportunities': {
            'email_alerts': [
                {
                    'term': '',
                    'created_on': '2000-01-01T01:01:01.000001Z',
                }
            ],
        }
    }
    html = render_to_string('exops/is-exops-user-email-alerts.html', context)

    assert '<empty>' in html
