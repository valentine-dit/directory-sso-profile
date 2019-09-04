import abc

from directory_constants import urls
from formtools.wizard.views import NamedUrlSessionWizardView
from requests.exceptions import HTTPError
from urllib.parse import unquote

from django.conf import settings
from django.contrib import messages
from django.http import QueryDict
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
SESSION_KEY_BUSINESS_PROFILE_INTENT = 'BUSINESS_PROFILE_INTENT'
SESSION_KEY_BACKFILL_DETAILS_INTENT = 'BACKFILL_DETAILS_INTENT'


PROGRESS_STEP_LABEL_USER_ACCOUNT = (
    'Enter your business email address and set a password'
)
PROGRESS_STEP_LABEL_INDIVIDUAL_USER_ACCOUNT = (
    'Enter your email address and set a password'
)
PROGRESS_STEP_LABEL_VERIFICATION = 'Enter your confirmation code'
PROGRESS_STEP_LABEL_RESEND_VERIFICATION = 'Resend verification'
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

URL_NON_COMPANIES_HOUSE_ENROLMENT = reverse_lazy(
    'enrolment-sole-trader', kwargs={'step': USER_ACCOUNT}
)
URL_COMPANIES_HOUSE_ENROLMENT = reverse_lazy(
    'enrolment-companies-house', kwargs={'step': USER_ACCOUNT}
)
URL_INDIVIDUAL_ENROLMENT = reverse_lazy(
    'enrolment-individual', kwargs={'step': USER_ACCOUNT}
)
URL_OVERSEAS_BUSINESS_ENROLMNET = reverse_lazy(
    'enrolment-overseas-business'
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
    def steps_list_labels(self):
        pass  # pragma: no cover

    def should_show_anon_progress_indicator(self):
        return self.request.user.is_anonymous

    @property
    def step_labels(self):
        labels = self.steps_list_labels[:]
        if not self.should_show_anon_progress_indicator():
            self.remove_label(labels=labels, label=PROGRESS_STEP_LABEL_USER_ACCOUNT)
            self.remove_label(labels=labels, label=PROGRESS_STEP_LABEL_VERIFICATION)
            if self.request.user.has_user_profile:
                self.remove_label(labels=labels, label=PROGRESS_STEP_LABEL_PERSONAL_INFO)

        if not settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON']:
            self.remove_label(labels=labels, label=PROGRESS_STEP_LABEL_BUSINESS_TYPE)

        return labels

    def remove_label(self, labels, label):
        if label in labels:
            labels.remove(label)

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
        if (
            SESSION_KEY_INGRESS_ANON not in self.storage.extra_data and
            self.kwargs['step'] == self.steps.first
        ):
            self.storage.extra_data[SESSION_KEY_INGRESS_ANON] = bool(
                self.request.user.is_anonymous
            )
        return super().get(*args, **kwargs)

    def should_show_anon_progress_indicator(self):
        if self.storage.extra_data.get(SESSION_KEY_INGRESS_ANON):
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


class CreateUserAccountMixin:

    def user_account_condition(self):
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

        return self.request.user.is_anonymous

    def verification_condition(self):
        return self.request.user.is_anonymous

    def personal_info_condition(self):
        if self.request.user.is_anonymous:
            return True
        return not self.request.user.has_user_profile

    condition_dict = {
        USER_ACCOUNT: user_account_condition,
        VERIFICATION: verification_condition,
        PERSONAL_INFO: personal_info_condition
    }

    def get_form_initial(self, step):
        form_initial = super().get_form_initial(step)
        if step == VERIFICATION:
            data = self.get_cleaned_data_for_step(USER_ACCOUNT)
            if data:
                form_initial['email'] = data['email']
        return form_initial

    def process_step(self, form):
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
        return super().process_step(form)

    def render_next_step(self, form, **kwargs):
        response = super().render_next_step(form=form, **kwargs)
        if form.prefix == VERIFICATION:
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


class CreateBusinessProfileMixin:

    def __new__(cls, *args, **kwargs):
        assert FINISHED in cls.templates
        return super().__new__(cls)

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
            'sectors',
            'job_title',
            'phone_number',
            'postal_code',
            'sic',
            'website',
            'given_name',
            'family_name',
        ]
        return {
            key: value for key, value in data.items()
            if value and key in whitelist
        }

    def create_company_profile(self, data):
        user = self.request.user
        helpers.create_company_profile({
            'sso_id': user.id,
            'company_email': user.email,
            'contact_email_address': user.email,
            **data,
        })

    # For user that started their journey from sso-profile, take them directly
    # to their business profile, otherwise show them the success page.
    # The motivation is users that started from sso-profle created the business
    # profile as their end goal. Those that started elsewhere created a
    # business profile as a mean to some other end - so show them a success
    # page with a list of places they can go next.

    def done(self, form_list, *args, **kwargs):
        data = self.serialize_form_list(form_list)
        self.create_company_profile(data)
        if self.request.session.get(SESSION_KEY_BUSINESS_PROFILE_INTENT):
            messages.success(self.request, 'Account created')
            del self.request.session[SESSION_KEY_BUSINESS_PROFILE_INTENT]
            return redirect('find-a-buyer')
        else:
            return TemplateResponse(self.request, self.templates[FINISHED])


class ReadUserIntentMixin:
    """Expose whether the user's intent is to create a business profile"""
    LABEL_BUSINESS = 'create a business profile'
    LABEL_ACCOUNT = 'create an great.gov.uk account'
    LABEL_BACKFILL_DETAILS = 'Update your details'

    def has_business_profile_intent_in_session(self):
        return self.request.session.get(SESSION_KEY_BUSINESS_PROFILE_INTENT)

    def has_backfill_details_intent_in_session(self):
        return self.request.session.get(SESSION_KEY_BACKFILL_DETAILS_INTENT)

    def get_user_journey_verb(self):
        if self.has_backfill_details_intent_in_session():
            return self.LABEL_BACKFILL_DETAILS
        if (
            self.has_business_profile_intent_in_session() or
            self.request.user.is_authenticated
        ):
            return self.LABEL_BUSINESS
        return self.LABEL_ACCOUNT

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            user_journey_verb=self.get_user_journey_verb(),
            **kwargs
        )


class WriteUserIntentMixin:
    """Save weather the user's intent is to create a business profile"""

    def has_intent_in_querystring(self, intent_name):
        params = self.request.GET
        # catch the case where anonymous user clicked "start now" from FAB
        # landing page then were sent to SSO login and then clicked "sign up"
        # resulting in 'business-profile-intent' in the `next` param
        if params.get('next'):
            try:
                url, querystring, *rest = unquote(params['next']).split('?')
            except ValueError:
                # querystring may be malformed
                pass
            else:
                params = QueryDict(querystring)
        return params.get(intent_name)

    def dispatch(self, *args, **kwargs):
        if self.has_intent_in_querystring('backfill-details-intent'):
            # user was prompted to backfill their company or business
            # details after logging in
            self.request.session[SESSION_KEY_BACKFILL_DETAILS_INTENT] = True
        elif self.has_intent_in_querystring('business-profile-intent'):
            # user has clicked a button to specifically create a business
            # profile. They are signing up because their end goal is to have
            # a business profile. The counter to this scenario is the user
            # started their journey from outside of sso-profile and their
            # intent is to gain access use other services, and creating a
            # business profile is a step towards that goal. The business
            # profile is a means to and end, not the desired end.
            self.request.session[SESSION_KEY_BUSINESS_PROFILE_INTENT] = True
        return super().dispatch(*args, **kwargs)


class BusinessTypeRoutingView(
    RedirectAlreadyEnrolledMixin, StepsListMixin, WriteUserIntentMixin,
    ReadUserIntentMixin, FormView
):
    form_class = forms.BusinessType
    template_name = 'enrolment/business-type.html'
    steps_list_labels = [
        PROGRESS_STEP_LABEL_BUSINESS_TYPE,
        PROGRESS_STEP_LABEL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
        PROGRESS_STEP_LABEL_PERSONAL_INFO,
    ]

    def dispatch(self, *args, **kwargs):
        if not settings.FEATURE_FLAGS['ENROLMENT_SELECT_BUSINESS_ON']:
            return redirect(URL_COMPANIES_HOUSE_ENROLMENT)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        choice = form.cleaned_data['choice']
        if choice == constants.COMPANIES_HOUSE_COMPANY:
            url = URL_COMPANIES_HOUSE_ENROLMENT
        elif choice == constants.NON_COMPANIES_HOUSE_COMPANY:
            url = URL_NON_COMPANIES_HOUSE_ENROLMENT
        elif choice == constants.NOT_COMPANY:
            if self.has_business_profile_intent_in_session():
                url = reverse('enrolment-individual-interstitial')
            else:
                url = URL_INDIVIDUAL_ENROLMENT
        elif choice == constants.OVERSEAS_COMPANY:
            url = URL_OVERSEAS_BUSINESS_ENROLMNET
        else:
            raise NotImplementedError()
        self.request.session[SESSION_KEY_COMPANY_CHOICE] = choice
        return redirect(url)


class EnrolmentStartView(
    RedirectAlreadyEnrolledMixin, StepsListMixin, WriteUserIntentMixin,
    ReadUserIntentMixin, TemplateView
):
    template_name = 'enrolment/start.html'

    steps_list_labels = [
        PROGRESS_STEP_LABEL_BUSINESS_TYPE,
        PROGRESS_STEP_LABEL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
        PROGRESS_STEP_LABEL_PERSONAL_INFO,
    ]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if helpers.user_has_company(request.user.session_id):
                return redirect('find-a-buyer')
        return super().dispatch(request, *args, **kwargs)


class BaseEnrolmentWizardView(
    RedirectAlreadyEnrolledMixin,
    RestartOnStepSkipped,
    core.mixins.PreventCaptchaRevalidationMixin,
    core.mixins.CreateUserProfileMixin,
    ProgressIndicatorMixin,
    StepsListMixin,
    ReadUserIntentMixin,
    CreateUserAccountMixin,
    NamedUrlSessionWizardView
):

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.steps.current == PERSONAL_INFO:
            context['company'] = self.get_cleaned_data_for_step(BUSINESS_INFO)
        elif self.steps.current == VERIFICATION:
            context['verification_missing_url'] = urls.build_great_url(
                'contact/triage/great-account/verification-missing/'
            )
        return context

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def process_step(self, form):
        if form.prefix == PERSONAL_INFO:
            self.create_user_profile(form)
        return super().process_step(form)


class CompaniesHouseEnrolmentView(CreateBusinessProfileMixin, BaseEnrolmentWizardView):
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
    )
    steps_list_labels = [
        PROGRESS_STEP_LABEL_BUSINESS_TYPE,
        PROGRESS_STEP_LABEL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
        PROGRESS_STEP_LABEL_PERSONAL_INFO,
    ]

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
        FINISHED: 'enrolment/companies-house-success.html',
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
        data = self.serialize_form_list(form_list)
        is_enrolled = helpers.get_is_enrolled(
            company_number=data['company_number'],
            session=self.request.session,
        )

        if self.request.user.full_name:
            name = self.request.user.full_name
        else:
            name = f'{data["given_name"]} {data["family_name"]}'

        if is_enrolled:
            helpers.create_company_member(data={
                'company': data['company_number'],
                'sso_id': self.request.user.id,
                'company_email': self.request.user.email,
                'name': name,
                'mobile_number': data.get('phone_number', ''),
            })

            helpers.notify_company_admins_member_joined(email_data={
                'sso_session_id': self.request.user.session_id,
                'company_name': data['company_name'],
                'name': name,
                'email': self.request.user.email,
                'form_url': self.request.path,
                'profile_remove_member_url': self.request.build_absolute_uri(
                    reverse('find-a-buyer-admin-tools')
                ),
                'report_abuse_url': urls.FEEDBACK
            }, form_url=None)

            return TemplateResponse(self.request, self.templates[FINISHED])
        else:
            return super().done(form_list, form_dict=form_dict, **kwargs)


class NonCompaniesHouseEnrolmentView(CreateBusinessProfileMixin, BaseEnrolmentWizardView):
    steps_list_labels = [
        PROGRESS_STEP_LABEL_BUSINESS_TYPE,
        PROGRESS_STEP_LABEL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
        PROGRESS_STEP_LABEL_PERSONAL_INFO,
    ]

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
    )

    form_list = (
        (USER_ACCOUNT, forms.UserAccount),
        (VERIFICATION, forms.UserAccountVerification),
        (COMPANY_SEARCH, forms.NonCompaniesHouseSearch),
        (PERSONAL_INFO, core.forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        COMPANY_SEARCH: 'enrolment/non-companies-house-business-details.html',
        PERSONAL_INFO: 'enrolment/non-companies-house-personal-details.html',
        FINISHED: 'enrolment/non-companies-house-success.html',
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.steps.current == PERSONAL_INFO:
            context['company'] = self.get_cleaned_data_for_step(COMPANY_SEARCH)
        return context


class IndividualUserEnrolmentInterstitial(ReadUserIntentMixin, TemplateView):
    template_name = 'enrolment/individual-interstitial.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.has_business_profile_intent_in_session():
            url = reverse(
                'enrolment-individual', kwargs={'step': PERSONAL_INFO}
            )
            return redirect(url)
        return super().dispatch(request, *args, **kwargs)


class IndividualUserEnrolmentView(BaseEnrolmentWizardView):
    steps_list_labels = [
        PROGRESS_STEP_LABEL_BUSINESS_TYPE,
        PROGRESS_STEP_LABEL_INDIVIDUAL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_PERSONAL_INFO
    ]

    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_user={
            PERSONAL_INFO: 3
        },
        step_counter_anon={
            USER_ACCOUNT: 2,
            VERIFICATION: 3,
            PERSONAL_INFO: 4
        },
    )

    form_list = (
        (USER_ACCOUNT, forms.UserAccount),
        (VERIFICATION, forms.UserAccountVerification),
        (PERSONAL_INFO, forms.IndividualPersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/individual-user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        PERSONAL_INFO: 'enrolment/individual-personal-details.html',
        FINISHED: 'enrolment/individual-success.html',
    }

    def get(self, *args, **kwargs):
        # at this point all the steps will be hidden as the user is logged
        # in and has a user profile, so the normal `get` method fails with
        # IndexError, meaning `done` will not be hit. Working around this:
        if self.kwargs['step'] == FINISHED:
            return self.done()
        return super().get(*args, **kwargs)

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, *args, **kwargs):
        return TemplateResponse(self.request, self.templates[FINISHED])


class PreVerifiedEnrolmentView(BaseEnrolmentWizardView):
    steps_list_labels = [
        PROGRESS_STEP_LABEL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_PERSONAL_INFO,
    ]

    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_user={PERSONAL_INFO: 1},
        step_counter_anon={
            USER_ACCOUNT: 1,
            VERIFICATION: 2,
            PERSONAL_INFO: 3,
        },
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
    CreateUserAccountMixin,
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
        # logged in users should not get here
        step_counter_user={},
    )
    steps_list_labels = [
        PROGRESS_STEP_LABEL_RESEND_VERIFICATION,
        PROGRESS_STEP_LABEL_VERIFICATION,
    ]

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def render_done(self, form, **kwargs):
        choice = self.request.session.get(SESSION_KEY_COMPANY_CHOICE)
        if choice == constants.COMPANIES_HOUSE_COMPANY:
            url = URL_COMPANIES_HOUSE_ENROLMENT
        elif choice == constants.NON_COMPANIES_HOUSE_COMPANY:
            url = URL_NON_COMPANIES_HOUSE_ENROLMENT
        elif choice == constants.NOT_COMPANY:
            url = URL_INDIVIDUAL_ENROLMENT
        else:
            url = reverse('enrolment-business-type')
        response = self.validate_code(
            form=form,
            response=redirect(url)
        )
        return response

    def process_step(self, form):
        if form.prefix == RESEND_VERIFICATION:
            email = form.cleaned_data['email']
            verification_code = helpers.regenerate_verification_code(email)
            if verification_code:
                helpers.send_verification_code_email(
                    email=email,
                    verification_code=verification_code,
                    form_url=self.request.path,
                )
        return super().process_step(form)

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


class EnrolmentOverseasBusinessView(ReadUserIntentMixin, TemplateView):
    template_name = 'enrolment/overseas-business.html'
