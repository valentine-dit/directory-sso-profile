import abc

from directory_constants import company_types, urls
from formtools.wizard.views import NamedUrlSessionWizardView
from requests.exceptions import HTTPError

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView
from django.template.response import TemplateResponse

import core.forms
import core.helpers
import core.mixins
from enrolment import constants, forms, helpers


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


class RedirectLoggedInMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('about')
        return super().dispatch(request, *args, **kwargs)


class RedirectAlreadyEnrolledMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if helpers.user_has_company(request.user.session_id):
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
        return self.request.user.is_anonymous

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
                bool(self.request.user.is_anonymous)
            )
        return super().get(*args, **kwargs)

    def render_done(self, *args, **kwargs):
        self.request.session.pop(SESSION_KEY_INGRESS_ANON, None)
        return super().render_done(*args, **kwargs)

    def should_show_anon_progress_indicator(self):
        if self.request.session.get(SESSION_KEY_INGRESS_ANON):
            return True
        return self.request.user.is_anonymous

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
        is_logged_in = self.request.user.is_authenticated
        # user has gone straight to verification code entry step, skipping the
        # step where they enter their email. This can happen if:
        # - user submitted the first step then closed the browser and followed
        # the email from another browser session
        # - user submitted the first step then followed the email from another
        # device
        skipped_first_step = (
            self.kwargs['step'] == VERIFICATION and
            USER_ACCOUNT not in self.storage.data['step_data']
        )
        if skipped_first_step:
            return False

        return self.request.sso_user is None

    def verification_condition(self):
        return self.request.user.is_anonymous

    condition_dict = {
        USER_ACCOUNT: user_account_condition,
        VERIFICATION: verification_condition,
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
            if error.response.status_code in [400, 404]:
                self.storage.set_step_data(
                    VERIFICATION,
                    {
                        form.add_prefix('email'): [form.cleaned_data['email']],
                        form.add_prefix('code'): [None]
                    }
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
            'company_type',
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
            'sso_id': self.request.user.id,
            'company_email': self.request.user.email,
            'contact_email_address': self.request.user.email,
            **data,
        })


class BusinessTypeRoutingView(
    RedirectAlreadyEnrolledMixin, StepsListMixin, FormView
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
    RedirectAlreadyEnrolledMixin, StepsListMixin, TemplateView
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
        if request.user.is_authenticated:
            if helpers.user_has_company(request.user.session_id):
                return redirect('find-a-buyer')
        return super().dispatch(request, *args, **kwargs)


class BaseEnrolmentWizardView(
    RedirectAlreadyEnrolledMixin,
    RestartOnStepSkipped,
    UserAccountEnrolmentHandlerMixin,
    core.mixins.PreventCaptchaRevalidationMixin,
    ProgressIndicatorMixin,
    StepsListMixin,
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
    core.mixins.CreateUserProfileMixin, CreateCompanyProfileMixin,
    BaseEnrolmentWizardView
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
        (PERSONAL_INFO, core.forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        COMPANY_SEARCH: 'enrolment/companies-house-search.html',
        BUSINESS_INFO: 'enrolment/companies-house-business-details.html',
        PERSONAL_INFO: 'enrolment/companies-house-personal-details.html',
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
            **super().serialize_form_list(form_list),
            'company_type': 'COMPANIES_HOUSE',
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
                email=self.request.user.email,
                name=f"{data['given_name']} {data['family_name']}",
                form_url=self.request.path,
            )
        else:
            self.create_company_profile(data)
        messages.success(self.request, 'Business profile created')
        return redirect('find-a-buyer')


class SoleTraderEnrolmentView(
    core.mixins.CreateUserProfileMixin, CreateCompanyProfileMixin,
    BaseEnrolmentWizardView
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
            PERSONAL_INFO: 3,
        },
        step_counter_anon={
            USER_ACCOUNT: 2,
            VERIFICATION: 3,
            COMPANY_SEARCH: 4,
            PERSONAL_INFO: 5,
        },
        first_step=USER_ACCOUNT,
    )

    form_list = (
        (USER_ACCOUNT, forms.UserAccount),
        (VERIFICATION, forms.UserAccountVerification),
        (COMPANY_SEARCH, forms.SoleTraderSearch),
        (PERSONAL_INFO, core.forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        COMPANY_SEARCH: 'enrolment/sole-trader-business-details.html',
        PERSONAL_INFO: 'enrolment/sole-trader-personal-details.html',
    }

    def get_form_initial(self, step):
        form_initial = super().get_form_initial(step=step)
        if step == COMPANY_SEARCH:
            form_initial.setdefault('company_type', company_types.SOLE_TRADER)
        return form_initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.steps.current == PERSONAL_INFO:
            context['company'] = self.get_cleaned_data_for_step(COMPANY_SEARCH)
        return context

    def done(self, form_list, form_dict, **kwargs):
        self.create_user_profile(form_dict[PERSONAL_INFO])
        data = self.serialize_form_list(form_list)
        self.create_company_profile(data)
        messages.success(self.request, 'Business profile created')
        return redirect('find-a-buyer')


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
        (PERSONAL_INFO, core.forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        PERSONAL_INFO: 'enrolment/preverified-personal-details.html',
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
            return TemplateResponse(self.request, self.templates[FAILURE])
        else:
            messages.success(self.request, 'Business profile created')
            return redirect('find-a-buyer')

    def claim_company(self, data):
        helpers.claim_company(
            enrolment_key=self.request.session[SESSION_KEY_ENROL_KEY],
            personal_name=f'{data["given_name"]} {data["family_name"]}',
            sso_session_id=self.request.user.session_id,
        )

    def serialize_form_list(self, form_list):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)
        return data


class ResendVerificationCodeView(
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
