from formtools.wizard.views import NamedUrlSessionWizardView

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView

import core.mixins
from enrolment import forms, helpers


class NotFoundOnDisabledFeature:
    def dispatch(self, *args, **kwargs):
        if not settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_ON']:
            raise Http404()
        return super().dispatch(*args, **kwargs)


class EnrolmentView(
    NotFoundOnDisabledFeature, core.mixins.PreventCaptchaRevalidationMixin,
    NamedUrlSessionWizardView
):
    success_url = reverse_lazy('enrolment-success')

    BUSINESS_TYPE = 'business-type'
    USER_ACCOUNT = 'user-account'
    USER_ACCOUNT_VERIFICATION = 'verification'
    COMPANY_SEARCH = 'companies-house-search'
    COMPANIES_HOUSE_BUSINESS_DETAILS = 'companies-house-business-details'
    PERSONAL_DETAILS = 'personal-details'

    form_list = (
        (BUSINESS_TYPE, forms.BusinessType),
        (USER_ACCOUNT, forms.UserAccount),
        (USER_ACCOUNT_VERIFICATION, forms.UserAccountVerification),
        (COMPANY_SEARCH, forms.CompaniesHouseSearch),
        (
            COMPANIES_HOUSE_BUSINESS_DETAILS,
            forms.CompaniesHouseBusinessDetails
        ),
        (PERSONAL_DETAILS, forms.PersonalDetails),
    )

    templates = {
        BUSINESS_TYPE: 'enrolment/business-type.html',
        USER_ACCOUNT: 'enrolment/user-account.html',
        USER_ACCOUNT_VERIFICATION: 'enrolment/user-account-verification.html',
        COMPANY_SEARCH: 'enrolment/companies-house-search.html',
        COMPANIES_HOUSE_BUSINESS_DETAILS: (
            'enrolment/companies-house-business-details.html'
        ),
        PERSONAL_DETAILS: 'enrolment/personal-details.html',
    }

    def render(self, *args, **kwargs):
        prev = self.steps.prev
        if prev and not self.get_cleaned_data_for_step(prev):
            url = reverse(self.url_name, kwargs={'step': self.steps.first})
            return redirect(url)
        return super().render(*args, **kwargs)

    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        if step == self.COMPANIES_HOUSE_BUSINESS_DETAILS:
            data = self.get_cleaned_data_for_step(self.COMPANY_SEARCH)
            company_data = helpers.get_company_profile(data['company_number'])
            company = helpers.CompanyProfileFormatter(company_data)
            initial['company_name'] = company.name
            initial['company_number'] = company.number
            initial['sic'] = company.sic_code
            initial['date_created'] = company.date_created
            initial['address'] = company.address
        return initial

    def render_next_step(self, form, **kwargs):
        if self.storage.current_step == self.USER_ACCOUNT:
            password = form.cleaned_data["password"]
            email = form.cleaned_data.get("email")
            helpers.create_user(email=email, password=password)
            new_user = helpers.create_user(email, password)
            helpers.send_verification_code_email(
                email=new_user['email'],
                verification_code=new_user['verification_code'],
                from_url=self.request.path,
            )
        return super().render_next_step(form, **kwargs)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        if self.steps.current == self.PERSONAL_DETAILS:
            step = self.COMPANIES_HOUSE_BUSINESS_DETAILS
            context['company'] = self.get_cleaned_data_for_step(step)
        return context

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, **kwargs):
        return redirect(self.success_url)


class EnrolmentSuccess(NotFoundOnDisabledFeature, TemplateView):
    template_name = 'enrolment/success.html'
