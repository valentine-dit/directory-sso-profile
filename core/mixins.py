from django.utils.functional import cached_property


class PreventCaptchaRevalidationMixin:
    """When get_all_cleaned_data() is called the forms are revalidated,
    which causes captcha to fail becuase the same captcha response from google
    is posted to google multiple times. This captcha response is a nonce, and
    so google complains the second time it's seen.

    This is worked around by removing captcha from the form before the view
    calls get_all_cleaned_data

    """

    @cached_property
    def captcha_step_index(self):
        for step_name, form_class in self.get_form_list().items():
            if 'captcha' in form_class.base_fields:
                return self.get_step_index(step_name)
        # this can happen if the step with a captcha is optional
        return -1

    def get_form(self, step=None, *args, **kwargs):
        form = super().get_form(step=step, *args, **kwargs)
        fields = form.fields
        if 'captcha' in fields and self.steps.index > self.captcha_step_index:
            del fields['captcha']
        return form
