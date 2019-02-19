from formtools.wizard.views import NamedUrlSessionWizardView

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView
from django.template.response import TemplateResponse

import core.mixins
from enrolment import constants, forms, helpers
from directory_constants.constants import urls


SESSION_KEY_ENROL_EMAIL = 'ENROL_EMAIL'

PROGRESS_STEP_LABELS = (
    'Select your business type',
    'Enter your business email address and set a password',
    'Enter your confirmation code',
    'Enter your business details',
    'Enter your details',
)

USER_ACCOUNT = 'user-account'
VERIFICATION = 'verification'
COMPANY_SEARCH = 'search'
BUSINESS_INFO = 'business-details'
PERSONAL_INFO = 'personal-details'
FINISHED = 'finished'


class NotFoundOnDisabledFeature:
    def dispatch(self, *args, **kwargs):
        if not settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_ON']:
            raise Http404()
        return super().dispatch(*args, **kwargs)


class RedirectAlreadyEnrolledMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.sso_user:
            if helpers.user_has_company(request.sso_user.session_id):
                return redirect('about')
        return super().dispatch(request, *args, **kwargs)


class ProgressIndicatorMixin:
    step_labels = PROGRESS_STEP_LABELS

    step_counter = {
        USER_ACCOUNT: 2,
        VERIFICATION: 3,
        COMPANY_SEARCH: 4,
        BUSINESS_INFO: 4,
        PERSONAL_INFO: 5,
    }

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            step_labels=self.step_labels,
            step_number=self.step_counter[self.steps.current],
            *args,
            **kwargs,
        )


class RestartOnStepSkipped:
    def render(self, *args, **kwargs):
        prev = self.steps.prev
        if prev and not self.get_cleaned_data_for_step(prev):
            return redirect(reverse('enrolment-business-type'))
        return super().render(*args, **kwargs)


class UserAccountEnrolmentHandlerMixin:

    def user_account_condition(self):
        return self.request.sso_user is None

    condition_dict = {
        USER_ACCOUNT: user_account_condition,
        VERIFICATION: user_account_condition,
    }

    def get_form_initial(self, step):
        form_initial = super().get_form_initial(step)
        if step == VERIFICATION:
            data = self.get_cleaned_data_for_step(USER_ACCOUNT)
            if data:
                form_initial['email'] = data['email']
        return form_initial

    def render_next_step(self, form, **kwargs):
        response = super().render_next_step(form, **kwargs)
        if form.prefix == USER_ACCOUNT:
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
        elif form.prefix == VERIFICATION:
            response.cookies.update(form.cleaned_data['cookies'])
        return response


class BusinessTypeRoutingView(
    NotFoundOnDisabledFeature, RedirectAlreadyEnrolledMixin, FormView
):
    form_class = forms.BusinessType
    template_name = 'enrolment/business-type.html'

    url_companies_house_enrolment = reverse_lazy(
        'enrolment-companies-house', kwargs={'step': USER_ACCOUNT}
    )
    url_sole_trader_enrolment = reverse_lazy(
        'enrolment-sole-trader', kwargs={'step': USER_ACCOUNT}
    )

    def dispatch(self, *args, **kwargs):
        flag = settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_SELECT_BUSINESS_ON']
        if not flag:
            return redirect(self.url_companies_house_enrolment)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            step_labels=PROGRESS_STEP_LABELS,
            step_number=1,
            **kwargs
        )

    def form_valid(self, form):
        if form.cleaned_data['choice'] == constants.COMPANIES_HOUSE_COMPANY:
            return redirect(self.url_companies_house_enrolment)
        elif form.cleaned_data['choice'] == constants.SOLE_TRADER:
            return redirect(self.url_sole_trader_enrolment)
        raise NotImplementedError()


class EnrolmentStartView(
    NotFoundOnDisabledFeature, RedirectAlreadyEnrolledMixin, TemplateView
):
    template_name = 'enrolment/start.html'

    def dispatch(self, request, *args, **kwargs):
        if request.sso_user:
            if helpers.user_has_company(request.sso_user.session_id):
                return redirect('find-a-buyer')
        return super().dispatch(request, *args, **kwargs)


class BaseEnrolmentWizardView(
    NotFoundOnDisabledFeature,
    RedirectAlreadyEnrolledMixin,
    RestartOnStepSkipped,
    UserAccountEnrolmentHandlerMixin,
    core.mixins.PreventCaptchaRevalidationMixin,
    ProgressIndicatorMixin,
    NamedUrlSessionWizardView
):
    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.steps.current == PERSONAL_INFO:
            context['company'] = self.get_cleaned_data_for_step(BUSINESS_INFO)
        return context


class CompaniesHouseEnrolmentView(BaseEnrolmentWizardView):
    form_list = (
        (USER_ACCOUNT, forms.UserAccount),
        (VERIFICATION, forms.UserAccountVerification),
        (COMPANY_SEARCH, forms.CompaniesHouseSearch),
        (BUSINESS_INFO, forms.CompaniesHouseBusinessDetails),
        (PERSONAL_INFO, forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        COMPANY_SEARCH: 'enrolment/companies-house-search.html',
        BUSINESS_INFO: 'enrolment/companies-house-business-details.html',
        PERSONAL_INFO: 'enrolment/companies-house-personal-details.html',
        FINISHED: 'enrolment/success-companies-house.html',
    }

    def get_form_kwargs(self, step=None):
        form_kwargs = super().get_form_kwargs(step=step)
        if step == BUSINESS_INFO:
            previous_data = self.get_cleaned_data_for_step(COMPANY_SEARCH)
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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.steps.current == COMPANY_SEARCH:
            context['company_not_found_url'] = urls.build_great_url(
                'contact/triage/great-account/company-not-found/'
            )
        return context

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
        return TemplateResponse(self.request, self.templates[FINISHED])

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


class SoleTraderEnrolmentView(BaseEnrolmentWizardView):

    form_list = (
        (USER_ACCOUNT, forms.UserAccount),
        (VERIFICATION, forms.UserAccountVerification),
        (COMPANY_SEARCH, forms.SoleTraderSearch),
        (BUSINESS_INFO, forms.SoleTraderBusinessDetails),
        (PERSONAL_INFO, forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        COMPANY_SEARCH: 'enrolment/sole-trader-search.html',
        BUSINESS_INFO: 'enrolment/sole-trader-business-details.html',
        PERSONAL_INFO: 'enrolment/sole-trader-personal-details.html',
        FINISHED: 'enrolment/success-sole-trader.html',
    }

    def get_form_initial(self, step):
        form_initial = super().get_form_initial(step)
        if step == BUSINESS_INFO:
            data = self.get_cleaned_data_for_step(COMPANY_SEARCH)
            if data:
                form_initial['address'] = data['address'].replace(', ', '\n')
                form_initial['postal_code'] = data['postal_code']
                form_initial['company_name'] = data['company_name']
        return form_initial

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.steps.current == COMPANY_SEARCH:
            context['address_not_found_url'] = urls.build_great_url(
                'contact/triage/great-account/sole-trader-address-not-found/'
            )

        return context

    def done(self, form_list, **kwargs):
        # TODO: support sole trader enrolment
        return TemplateResponse(self.request, self.templates[FINISHED])
