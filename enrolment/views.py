from formtools.wizard.views import NamedUrlSessionWizardView

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView

import core.mixins
from enrolment import forms, helpers
from directory_constants.constants import urls

SESSION_KEY_ENROL_EMAIL = 'ENROL_EMAIL'


class NotFoundOnDisabledFeature:
    def dispatch(self, *args, **kwargs):
        if not settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_ON']:
            raise Http404()
        return super().dispatch(*args, **kwargs)


class EnrolmentStartView(TemplateView):
    template_name = 'enrolment/start.html'

    def dispatch(self, request, *args, **kwargs):
        if request.sso_user:
            if helpers.user_has_company(request.sso_user.session_id):
                return redirect('find-a-buyer')
        return super().dispatch(request, *args, **kwargs)


class EnrolmentView(
    NotFoundOnDisabledFeature,
    core.mixins.PreventCaptchaRevalidationMixin,
    NamedUrlSessionWizardView
):
    success_url = reverse_lazy('enrolment-success')

    BUSINESS_TYPE = 'business-type'
    USER_ACCOUNT = 'user-account'
    USER_ACCOUNT_VERIFICATION = 'verification'
    COMPANY_SEARCH = 'companies-house-search'
    BUSINESS_DETAILS = 'companies-house-business-details'
    PERSONAL_DETAILS = 'personal-details'

    form_list = (
        (BUSINESS_TYPE, forms.BusinessType),
        (USER_ACCOUNT, forms.UserAccount),
        (USER_ACCOUNT_VERIFICATION, forms.UserAccountVerification),
        (COMPANY_SEARCH, forms.CompaniesHouseSearch),
        (BUSINESS_DETAILS, forms.CompaniesHouseBusinessDetails),
        (PERSONAL_DETAILS, forms.PersonalDetails),
    )

    step_labels = (
        'Select your business type',
        'Enter your email and set a password',
        'Confirm the validation code from your email',
        'Confirm your business details',
        'Enter personal details',
    )

    step_counter = {
        BUSINESS_TYPE: 1,
        USER_ACCOUNT: 2,
        USER_ACCOUNT_VERIFICATION: 3,
        COMPANY_SEARCH: 4,
        BUSINESS_DETAILS: 4,
        PERSONAL_DETAILS: 5,
    }

    templates = {
        BUSINESS_TYPE: 'enrolment/business-type.html',
        USER_ACCOUNT: 'enrolment/user-account.html',
        USER_ACCOUNT_VERIFICATION: 'enrolment/user-account-verification.html',
        COMPANY_SEARCH: 'enrolment/companies-house-search.html',
        BUSINESS_DETAILS: 'enrolment/companies-house-business-details.html',
        PERSONAL_DETAILS: 'enrolment/personal-details.html',
    }

    def user_account_condition(self):
        return self.request.sso_user is None

    def select_company_condition(self):
        return settings.FEATURE_FLAGS[
            'NEW_ACCOUNT_JOURNEY_SELECT_BUSINESS_ON']

    condition_dict = {
        USER_ACCOUNT: user_account_condition,
        USER_ACCOUNT_VERIFICATION: user_account_condition,
        BUSINESS_TYPE: select_company_condition,
    }

    def dispatch(self, request, *args, **kwargs):
        if request.sso_user:
            if helpers.user_has_company(request.sso_user.session_id):
                return redirect('about')
        return super().dispatch(request, *args, **kwargs)

    def render(self, *args, **kwargs):
        prev = self.steps.prev
        if prev and not self.get_cleaned_data_for_step(prev):
            url = reverse(self.url_name, kwargs={'step': self.steps.first})
            return redirect(url)
        return super().render(*args, **kwargs)

    def get_form_kwargs(self, step=None):
        form_kwargs = super().get_form_kwargs(step=step)
        if step == self.BUSINESS_DETAILS:
            previous_data = self.get_cleaned_data_for_step(self.COMPANY_SEARCH)
            if previous_data:
                form_kwargs['company_data'] = helpers.get_company_profile(
                    number=previous_data['company_number'],
                    session=self.request.session,
                )
                form_kwargs['is_enrolled'] = helpers.get_is_enrolled(
                    company_number=previous_data['company_number'],
                    session=self.request.session,
                )
        return form_kwargs

    def get_form_initial(self, step):
        form_initial = super().get_form_initial(step)
        if step == self.USER_ACCOUNT_VERIFICATION:
            data = self.get_cleaned_data_for_step(self.USER_ACCOUNT)
            if data:
                form_initial['email'] = data['email']
        return form_initial

    def render_next_step(self, form, **kwargs):
        response = super().render_next_step(form, **kwargs)
        if form.prefix == self.USER_ACCOUNT:
            user_details = helpers.create_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            # Check if we have a user, else the user is already registered
            if user_details:
                helpers.send_verification_code_email(
                    email=form.cleaned_data['email'],
                    verification_code=user_details['verification_code'],
                    form_url=self.request.path,
                )
            else:
                helpers.notify_already_registered(
                    email=form.cleaned_data['email'],
                    form_url=self.request.path
                )
        elif form.prefix == self.USER_ACCOUNT_VERIFICATION:
            response.cookies.update(form.cleaned_data['cookies'])
        return response

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(
            form=form,
            step_labels=self.step_labels,
            step_number=self.step_counter[self.steps.current],
            **kwargs
        )
        if self.steps.current == self.PERSONAL_DETAILS:
            step = self.BUSINESS_DETAILS
            context['company'] = self.get_cleaned_data_for_step(step)
        if self.steps.current == self.COMPANY_SEARCH:
            context['company_not_found_url'] = urls.build_great_url(
                'contact/triage/great-account/company-not-found/'
            )

        return context

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, **kwargs):
        data = self.serialize_form_list(form_list)
        is_enrolled = helpers.get_is_enrolled(
            company_number=data['company_number'],
            session=self.request.session,
        )
        if is_enrolled:
            helpers.request_collaboration(
                company_number=data['company_number'],
                email=self.request.sso_user.email,
                name=f"{data['given_name']} {data['family_name']}",
                form_url=self.request.path,
            )
        else:
            helpers.create_company_profile({
                'sso_id': self.request.sso_user.id,
                'company_email': self.request.sso_user.email,
                'contact_email_address': self.request.sso_user.email,
                **data,
            })
        return redirect(self.success_url)

    def serialize_form_list(self, form_list):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)
        whitelist = [
            'address_line_1',
            'address_line_2',
            'company_name',
            'company_number',
            'date_of_creation',
            'family_name',
            'given_name',
            'industry',
            'job_title',
            'phone_number',
            'postal_code',
            'sic',
            'website_address',
        ]
        return {key: value for key, value in data.items() if key in whitelist}


class EnrolmentSuccess(NotFoundOnDisabledFeature, TemplateView):
    template_name = 'enrolment/success.html'
