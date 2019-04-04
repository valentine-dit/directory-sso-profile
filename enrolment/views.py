import abc

from formtools.wizard.views import NamedUrlSessionWizardView
from requests.exceptions import HTTPError

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView
from django.template.response import TemplateResponse

import core.mixins
from enrolment import constants, forms, helpers
from directory_constants.constants import urls


SESSION_KEY_ENROL_KEY = 'ENROL_KEY'

SESSION_KEY_ENROL_KEY_COMPANY_DATA = 'ENROL_KEY_COMPANY_DATA'
SESSION_KEY_INGRESS_ANON = 'ANON_INGRESS'
SESSION_KEY_COMPANY_CHOICE = 'COMPANY_CHOICE'
SESSION_KEY_COMPANY_DATA = 'ENROL_KEY_COMPANY_DATA'
SESSION_KEY_REFERRER = 'REFERRER_URL'

PROGRESS_STEP_LABEL_USER_ACCOUNT = (
    'Enter your business email address and set a password'
)
PROGRESS_STEP_LABEL_VERIFICATION = 'Enter your confirmation code'
PROGRESS_STEP_LABEL_PERSONAL_INFO = 'Enter your details'
PROGRESS_STEP_LABEL_BUSINESS_TYPE = 'Select your business type'
PROGRESS_STEP_LABEL_BUSINESS_DETAILS = 'Enter your business details'

RESEND_VERIFICATION = 'resend'
USER_ACCOUNT = 'user-account'
VERIFICATION = 'verification'
COMPANY_SEARCH = 'search'
BUSINESS_INFO = 'business-details'
PERSONAL_INFO = 'personal-details'
FINISHED = 'finished'
FAILURE = 'failure'

URL_SOLE_TRADER_ENROLMENT = reverse_lazy(
    'enrolment-sole-trader', kwargs={'step': USER_ACCOUNT}
)
URL_COMPANIES_HOUSE_ENROLMENT = reverse_lazy(
    'enrolment-companies-house', kwargs={'step': USER_ACCOUNT}
)


class NotFoundOnDisabledFeature:
    def dispatch(self, *args, **kwargs):
        if not settings.FEATURE_FLAGS['NEW_ACCOUNT_JOURNEY_ON']:
            raise Http404()
        return super().dispatch(*args, **kwargs)


class RedirectLoggedInMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.sso_user:
            return redirect('about')
        return super().dispatch(request, *args, **kwargs)


class RedirectAlreadyEnrolledMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.sso_user:
            if helpers.user_has_company(request.sso_user.session_id):
                return redirect('about')
        return super().dispatch(request, *args, **kwargs)


class StepsListMixin(abc.ABC):
    """
    Anonymous users see different steps on the progress indicator. Feature flag
    can also affect the steps shown.

    """

    @property
    @abc.abstractmethod
    def steps_list_conf(self):
        pass  # pragma: no cover

    def should_show_anon_progress_indicator(self):
        return self.request.sso_user is None

    @property
    def step_labels(self):
        if self.should_show_anon_progress_indicator():
            labels = self.steps_list_conf.form_labels_anon[:]
        else:
            labels = self.steps_list_conf.form_labels_user[:]
        if not settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON']:
            if PROGRESS_STEP_LABEL_BUSINESS_TYPE in labels:
                labels.remove(PROGRESS_STEP_LABEL_BUSINESS_TYPE)
        return labels

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            step_labels=self.step_labels,
            step_number=1,
            *args,
            **kwargs,
        )


class ProgressIndicatorMixin:
    """
    Anonymous users see different numbers next to the steps on the progress
    indicator. Feature flag can also affect this numbering.

    """

    @property
    @abc.abstractmethod
    def progress_conf(self):
        pass  # pragma: no cover

    def get(self, *args, **kwargs):
        if self.steps.current == self.progress_conf.first_step:
            self.request.session[SESSION_KEY_INGRESS_ANON] = (
                self.request.sso_user is None
            )
        return super().get(*args, **kwargs)

    def render_done(self, *args, **kwargs):
        self.request.session.pop(SESSION_KEY_INGRESS_ANON, None)
        return super().render_done(*args, **kwargs)

    def should_show_anon_progress_indicator(self):
        if self.request.session.get(SESSION_KEY_INGRESS_ANON):
            return True
        return self.request.sso_user is None

    @property
    def step_counter(self):
        if self.should_show_anon_progress_indicator():
            counter = self.progress_conf.step_counter_anon
        else:
            counter = self.progress_conf.step_counter_user
        # accounts for the first step being removed in StepsListMixin
        if not settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON']:
            counter = {key: value-1 for key, value in counter.items()}
        return counter

    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            'step_number': self.step_counter[self.steps.current],
        }


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
            # Check if we have a user, else the user is already registered
            if form.cleaned_data['user_details']:
                user_details = form.cleaned_data['user_details']
                helpers.send_verification_code_email(
                    email=user_details['email'],
                    verification_code=user_details['verification_code'],
                    form_url=self.request.path,
                )
            else:
                helpers.notify_already_registered(
                    email=form.cleaned_data['email'],
                    form_url=self.request.path
                )
        elif form.prefix == VERIFICATION:
            response = self.validate_code(form=form, response=response)
        return response

    def validate_code(self, form, response):
        try:
            upstream_response = helpers.confirm_verification_code(
                email=form.cleaned_data['email'],
                verification_code=form.cleaned_data['code'],
            )
        except HTTPError as error:
            if error.response.status_code == 400:
                self.storage.set_step_data(
                    VERIFICATION,
                    {form.add_prefix('code'): [None]}
                )
                return self.render_revalidation_failure(
                    failed_step=VERIFICATION,
                    form=form
                )
            else:
                raise
        else:
            cookies = helpers.parse_set_cookie_header(
                upstream_response.headers['set-cookie']
            )
            response.cookies.update(cookies)
            return response


class CreateCompanyProfileMixin:
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
            'sectors',
            'job_title',
            'phone_number',
            'postal_code',
            'sic',
            'website',
        ]
        return {
            key: value for key, value in data.items()
            if value and key in whitelist
        }

    def create_company_profile(self, data):
        helpers.create_company_profile({
            'sso_id': self.request.sso_user.id,
            'company_email': self.request.sso_user.email,
            'contact_email_address': self.request.sso_user.email,
            **data,
        })


class CreateUserProfileMixin:

    def serialize_user_profile(self, form):
        return {
            'first_name': form.cleaned_data['given_name'],
            'last_name': form.cleaned_data['family_name'],
            'job_title': form.cleaned_data['job_title'],
            'mobile_phone_number': form.cleaned_data.get('phone_number'),
        }

    def create_user_profile(self, form):
        helpers.create_user_profile(
            sso_session_id=self.request.sso_user.session_id,
            data=self.serialize_user_profile(form),
        )


class ServicesRefererDetectorMixin:
    def get_referrer_context(self):
        context = {}
        referrer_url = self.request.session.get(SESSION_KEY_REFERRER)
        if referrer_url and referrer_url.startswith(urls.SERVICES_FAB):
            context = {'fab_referrer': True}
        self.request.session.pop(SESSION_KEY_REFERRER, None)
        return context

    def dispatch(self, request, *args, **kwargs):
        referrer_entry_points = [urls.SERVICES_FAB]
        referrer_url = request.META.get('HTTP_REFERER')
        if referrer_url:
            for url in referrer_entry_points:
                if referrer_url.startswith(url):
                    self.request.session[SESSION_KEY_REFERRER] = referrer_url
        return super().dispatch(request, *args, **kwargs)


class BusinessTypeRoutingView(
    NotFoundOnDisabledFeature, RedirectAlreadyEnrolledMixin,
    StepsListMixin, FormView
):
    form_class = forms.BusinessType
    template_name = 'enrolment/business-type.html'
    steps_list_conf = helpers.StepsListConf(
        form_labels_user=[
            PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
        form_labels_anon=[
            PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            PROGRESS_STEP_LABEL_USER_ACCOUNT,
            PROGRESS_STEP_LABEL_VERIFICATION,
            PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
    )

    def dispatch(self, *args, **kwargs):
        if not settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON']:
            return redirect(URL_COMPANIES_HOUSE_ENROLMENT)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        choice = form.cleaned_data['choice']
        if choice == constants.COMPANIES_HOUSE_COMPANY:
            url = URL_COMPANIES_HOUSE_ENROLMENT
        elif choice == constants.SOLE_TRADER:
            url = URL_SOLE_TRADER_ENROLMENT
        else:
            raise NotImplementedError()
        self.request.session[SESSION_KEY_COMPANY_CHOICE] = choice
        return redirect(url)


class EnrolmentStartView(
    NotFoundOnDisabledFeature, RedirectAlreadyEnrolledMixin,
    StepsListMixin, ServicesRefererDetectorMixin, TemplateView
):
    template_name = 'enrolment/start.html'

    steps_list_conf = helpers.StepsListConf(
        form_labels_user=[
            PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
        form_labels_anon=[
            PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            PROGRESS_STEP_LABEL_USER_ACCOUNT,
            PROGRESS_STEP_LABEL_VERIFICATION,
            PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
    )

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
    StepsListMixin,
    ServicesRefererDetectorMixin,
    NamedUrlSessionWizardView
):

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.steps.current == PERSONAL_INFO:
            context['company'] = self.get_cleaned_data_for_step(BUSINESS_INFO)
        elif self.steps.current == VERIFICATION:
            context['verification_missing_url'] = urls.build_great_url(
                'contact/triage/great-account/verification-missing/'
            )
        return context


class CompaniesHouseEnrolmentView(
    CreateUserProfileMixin, CreateCompanyProfileMixin, BaseEnrolmentWizardView
):
    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_user={
            COMPANY_SEARCH: 2,
            BUSINESS_INFO: 2,
            PERSONAL_INFO: 3,
        },
        step_counter_anon={
            USER_ACCOUNT: 2,
            VERIFICATION: 3,
            COMPANY_SEARCH: 4,
            BUSINESS_INFO: 4,
            PERSONAL_INFO: 5,
        },
        first_step=USER_ACCOUNT,
    )
    steps_list_conf = helpers.StepsListConf(
        form_labels_user=[
            PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
        form_labels_anon=[
            PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            PROGRESS_STEP_LABEL_USER_ACCOUNT,
            PROGRESS_STEP_LABEL_VERIFICATION,
            PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
    )

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
        elif step == COMPANY_SEARCH:
            form_kwargs['session'] = self.request.session
        return form_kwargs

    def serialize_form_list(self, form_list):
        return {
            'company_type': 'COMPANIES_HOUSE',
            **super().serialize_form_list(form_list)
        }

    def done(self, form_list, form_dict, **kwargs):
        self.create_user_profile(form_dict[PERSONAL_INFO])
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
            self.create_company_profile(data)
        return TemplateResponse(
            self.request,
            self.templates[FINISHED],
            context=self.get_referrer_context()
        )


class SoleTraderEnrolmentView(
    CreateUserProfileMixin, CreateCompanyProfileMixin, BaseEnrolmentWizardView
):
    steps_list_conf = helpers.StepsListConf(
        form_labels_user=[
            PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
        form_labels_anon=[
            PROGRESS_STEP_LABEL_BUSINESS_TYPE,
            PROGRESS_STEP_LABEL_USER_ACCOUNT,
            PROGRESS_STEP_LABEL_VERIFICATION,
            PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
    )
    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_user={
            COMPANY_SEARCH: 2,
            BUSINESS_INFO: 3,
            PERSONAL_INFO: 4,
        },
        step_counter_anon={
            USER_ACCOUNT: 2,
            VERIFICATION: 3,
            COMPANY_SEARCH: 4,
            BUSINESS_INFO: 4,
            PERSONAL_INFO: 5,
        },
        first_step=USER_ACCOUNT,
    )

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

    def done(self, form_list, form_dict, **kwargs):
        self.create_user_profile(form_dict[PERSONAL_INFO])
        data = self.serialize_form_list(form_list)
        self.create_company_profile(data)
        return TemplateResponse(
            self.request,
            self.templates[FINISHED],
            context=self.get_referrer_context()
        )

    def serialize_form_list(self, form_list):
        return {
            'company_type': 'SOLE_TRADER',
            **super().serialize_form_list(form_list)
        }


class PreVerifiedEnrolmentView(BaseEnrolmentWizardView):
    steps_list_conf = helpers.StepsListConf(
        form_labels_user=[PROGRESS_STEP_LABEL_PERSONAL_INFO],
        form_labels_anon=[
            PROGRESS_STEP_LABEL_USER_ACCOUNT,
            PROGRESS_STEP_LABEL_VERIFICATION,
            PROGRESS_STEP_LABEL_PERSONAL_INFO,
        ],
    )
    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_user={PERSONAL_INFO: 1},
        step_counter_anon={
            USER_ACCOUNT: 1,
            VERIFICATION: 2,
            PERSONAL_INFO: 3,
        },
        first_step=USER_ACCOUNT,
    )

    form_list = (
        (USER_ACCOUNT, forms.UserAccount),
        (VERIFICATION, forms.UserAccountVerification),
        (PERSONAL_INFO, forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        PERSONAL_INFO: 'enrolment/preverified-personal-details.html',
        FINISHED: 'enrolment/success-pre-verified.html',
        FAILURE: 'enrolment/failure-pre-verified.html',
    }

    def get(self, *args, **kwargs):
        key = self.request.GET.get('key')
        if key:
            data = helpers.retrieve_preverified_company(key)
            if data:
                self.request.session[SESSION_KEY_COMPANY_DATA] = data
                self.request.session[SESSION_KEY_ENROL_KEY] = key
                self.request.session.save()
            else:
                return redirect(reverse('enrolment-start'))
        if self.steps.current == PERSONAL_INFO:
            if not self.request.session.get(SESSION_KEY_COMPANY_DATA):
                return redirect(reverse('enrolment-start'))
        return super().get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.steps.current == PERSONAL_INFO:
            context['company'] = (
                self.request.session[SESSION_KEY_COMPANY_DATA]
            )
        return context

    def done(self, form_list, **kwargs):
        try:
            self.claim_company(self.serialize_form_list(form_list))
        except HTTPError:
            template_name = self.templates[FAILURE]
        else:
            template_name = self.templates[FINISHED]
        return TemplateResponse(self.request, template_name)

    def claim_company(self, data):
        helpers.claim_company(
            enrolment_key=self.request.session[SESSION_KEY_ENROL_KEY],
            personal_name=f'{data["given_name"]} {data["family_name"]}',
            sso_session_id=self.request.sso_user.session_id,
        )

    def serialize_form_list(self, form_list):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)
        return data


class ResendVerificationCodeView(
    NotFoundOnDisabledFeature,
    RedirectLoggedInMixin,
    RestartOnStepSkipped,
    ProgressIndicatorMixin,
    StepsListMixin,
    UserAccountEnrolmentHandlerMixin,
    NamedUrlSessionWizardView
):

    form_list = (
        (RESEND_VERIFICATION, forms.ResendVerificationCode),
        (VERIFICATION, forms.UserAccountVerification),
    )

    templates = {
        RESEND_VERIFICATION: 'enrolment/user-account-resend-verification.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        FINISHED: 'enrolment/start.html',
    }

    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_anon={RESEND_VERIFICATION: 1, VERIFICATION: 2},
        first_step=RESEND_VERIFICATION,
        # logged in users should not get here
        step_counter_user={},
    )
    steps_list_conf = helpers.StepsListConf(
        form_labels_anon=[
            'Resend verification',
            PROGRESS_STEP_LABEL_VERIFICATION,
        ],
        # logged in users should not get here
        form_labels_user=[],
    )

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def render_done(self, form, **kwargs):
        choice = self.request.session.get(SESSION_KEY_COMPANY_CHOICE)
        if choice == constants.COMPANIES_HOUSE_COMPANY:
            url = URL_COMPANIES_HOUSE_ENROLMENT
        elif choice == constants.SOLE_TRADER:
            url = URL_SOLE_TRADER_ENROLMENT
        else:
            url = reverse('enrolment-business-type')
        response = self.validate_code(
            form=form,
            response=redirect(url)
        )
        return response

    def render_next_step(self, form, **kwargs):
        response = super().render_next_step(form, **kwargs)
        if form.prefix == RESEND_VERIFICATION:
            email = form.cleaned_data['email']
            verification_code = helpers.regenerate_verification_code(email)
            if verification_code:
                helpers.send_verification_code_email(
                    email=email,
                    verification_code=verification_code,
                    form_url=self.request.path,
                )
        return response

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            verification_missing_url=urls.build_great_url(
                'contact/triage/great-account/verification-missing/'
            ),
            contact_url=urls.build_great_url('contact/domestic/'),
            *args,
            **kwargs
        )

    def get_form_initial(self, step):
        form_initial = super().get_form_initial(step)
        if step == VERIFICATION:
            data = self.get_cleaned_data_for_step(RESEND_VERIFICATION)
            if data:
                form_initial['email'] = data['email']
        return form_initial
