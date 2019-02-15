from profile.fab import forms
from profile.fab import validators


def test_description_form_contains_enmail():
    form = forms.DescriptionForm({
        'summary': 'contact foo@example.com',
        'description': 'contact foo@example.com',
    })

    assert form.is_valid() is False
    assert form.errors == {
        'summary': [validators.MESSAGE_REMOVE_EMAIL],
        'description': [validators.MESSAGE_REMOVE_EMAIL],
    }
