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


def test_case_study_rich_media_image_one_update_help_text():
    form = forms.CaseStudyRichMediaForm(initial={'image_one': '123'})
    expected_values = forms.CaseStudyRichMediaForm.help_text_maps[0]

    assert form['image_one'].label == expected_values['update_label']
    assert form['image_one'].help_text == (
        expected_values['update_help_text'].format(initial_value='123')
    )


def test_case_study_rich_media_image_one_create_help_text():
    form = forms.CaseStudyRichMediaForm(initial={'image_one': None})
    expected_values = forms.CaseStudyRichMediaForm.help_text_maps[0]

    assert form['image_one'].label == expected_values['create_label']
    assert form['image_one'].help_text == expected_values['create_help_text']


def test_case_study_rich_media_image_two_update_help_text():
    form = forms.CaseStudyRichMediaForm(initial={'image_two': '123'})
    expected_values = forms.CaseStudyRichMediaForm.help_text_maps[1]

    assert form['image_two'].label == expected_values['update_label']
    assert form['image_two'].help_text == (
        expected_values['update_help_text'].format(initial_value='123')
    )


def test_case_study_rich_media_image_two_create_help_text():
    form = forms.CaseStudyRichMediaForm(initial={'image_two': None})
    expected_values = forms.CaseStudyRichMediaForm.help_text_maps[1]

    assert form['image_two'].label == expected_values['create_label']
    assert form['image_two'].help_text == expected_values['create_help_text']


def test_case_study_rich_media_image_three_update_help_text():
    form = forms.CaseStudyRichMediaForm(initial={'image_three': '123'})
    expected_values = forms.CaseStudyRichMediaForm.help_text_maps[2]

    assert form['image_three'].label == expected_values['update_label']
    assert form['image_three'].help_text == (
        expected_values['update_help_text'].format(initial_value='123')
    )


def test_case_study_rich_media_image_three_create_help_text():
    form = forms.CaseStudyRichMediaForm(initial={'image_three': None})
    expected_values = forms.CaseStudyRichMediaForm.help_text_maps[2]

    assert form['image_three'].label == expected_values['create_label']
    assert form['image_three'].help_text == expected_values['create_help_text']
