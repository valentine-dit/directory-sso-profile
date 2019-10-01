from directory_constants import urls
from formtools.wizard.views import NamedUrlSessionWizardView
from requests.exceptions import HTTPError
from directory_forms_api_client.helpers import FormSessionMixin

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import FormView, TemplateView

import core.forms
import core.helpers
import core.mixins
from enrolment import constants, forms, helpers, mixins


SESSION_KEY_ENROL_KEY = 'ENROL_KEY'
SESSION_KEY_ENROL_KEY_COMPANY_DATA = 'ENROL_KEY_COMPANY_DATA'
SESSION_KEY_INGRESS_ANON = 'ANON_INGRESS'
SESSION_KEY_COMPANY_CHOICE = 'COMPANY_CHOICE'
SESSION_KEY_COMPANY_DATA = 'ENROL_KEY_COMPANY_DATA'
SESSION_KEY_REFERRER = 'REFERRER_URL'
SESSION_KEY_BUSINESS_PROFILE_INTENT = 'BUSINESS_PROFILE_INTENT'
SESSION_KEY_BACKFILL_DETAILS_INTENT = 'BACKFILL_DETAILS_INTENT'
SESSION_KEY_INVITE_KEY = 'INVITE_KEY'

PROGRESS_STEP_LABEL_USER_ACCOUNT = (
    'Enter your business email address and set a password'
)
PROGRESS_STEP_LABEL_INDIVIDUAL_USER_ACCOUNT = (
    'Enter your email address and set a password'
)
PROGRESS_STEP_LABEL_VERIFICATION = 'Enter your confirmation code'
PROGRESS_STEP_LABEL_RESEND_VERIFICATION = 'Resend verification'
PROGRESS_STEP_LABEL_PERSONAL_INFO = 'Enter your personal details'
PROGRESS_STEP_LABEL_BUSINESS_TYPE = 'Select your business type'
PROGRESS_STEP_LABEL_BUSINESS_DETAILS = 'Enter your business details'

RESEND_VERIFICATION = 'resend'
USER_ACCOUNT = 'user-account'
VERIFICATION = 'verification'
COMPANY_SEARCH = 'company-search'
ADDRESS_SEARCH = 'address-search'
BUSINESS_INFO = 'business-details'
PERSONAL_INFO = 'personal-details'
FINISHED = 'finished'
FAILURE = 'failure'
INVITE_EXPIRED = 'invite-expired'

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


class EnrolmentStartView(
    mixins.RedirectAlreadyEnrolledMixin,
    FormSessionMixin,
    mixins.StepsListMixin,
    mixins.WriteUserIntentMixin,
    mixins.ReadUserIntentMixin,
    mixins.GA360Mixin,
    TemplateView
):
    google_analytics_page_id = 'EnrolmentStartPage'
    template_name = 'enrolment/start.html'
    steps_list_labels = [
        PROGRESS_STEP_LABEL_BUSINESS_TYPE,
        PROGRESS_STEP_LABEL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
        PROGRESS_STEP_LABEL_PERSONAL_INFO,
    ]

    def get(self, *args, **kwargs):
        if 'next' in self.request.GET:
            self.form_session.ingress_url = self.request.GET['next']

        return super().get(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if helpers.user_has_company(request.user.session_id):
                return redirect('business-profile')
        return super().dispatch(request, *args, **kwargs)


class BusinessTypeRoutingView(
    mixins.RedirectAlreadyEnrolledMixin,
    mixins.StepsListMixin,
    mixins.WriteUserIntentMixin,
    mixins.ReadUserIntentMixin,
    mixins.GA360Mixin, FormView
):
    google_analytics_page_id = 'EnrolmentBusinessTypeChooser'
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


class BaseEnrolmentWizardView(
    mixins.RedirectAlreadyEnrolledMixin,
    FormSessionMixin,
    mixins.RestartOnStepSkipped,
    core.mixins.PreventCaptchaRevalidationMixin,
    core.mixins.CreateUpdateUserProfileMixin,
    mixins.ProgressIndicatorMixin,
    mixins.StepsListMixin,
    mixins.ReadUserIntentMixin,
    mixins.CreateUserAccountMixin,
    mixins.GA360Mixin,
    NamedUrlSessionWizardView
):

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.steps.current == COMPANY_SEARCH:
            context['contact_us_url'] = (urls.domestic.CONTACT_US / 'domestic')
        elif self.steps.current == BUSINESS_INFO:
            previous_data = self.get_cleaned_data_for_step(COMPANY_SEARCH)
            if previous_data:
                context['is_enrolled'] = helpers.get_is_enrolled(previous_data['company_number'])
                context['contact_us_url'] = (urls.domestic.CONTACT_US / 'domestic')
        if self.steps.current == PERSONAL_INFO:
            context['company'] = self.get_cleaned_data_for_step(BUSINESS_INFO)
        elif self.steps.current == VERIFICATION:
            context['verification_missing_url'] = (
                urls.domestic.CONTACT_US / 'triage/great-account/verification-missing/'
            )
        return context

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def process_step(self, form):
        if form.prefix == PERSONAL_INFO:
            self.create_update_user_profile(form)
        return super().process_step(form)

    def redirect_to_ingress_or_finish(self):
        if self.form_session.ingress_url:
            ingress_url = self.form_session.ingress_url
            # self.form_session.clear()
            return redirect(ingress_url)
        else:
            return TemplateResponse(self.request, self.templates[FINISHED])


class CompaniesHouseEnrolmentView(
    mixins.CreateBusinessProfileMixin,
    BaseEnrolmentWizardView
):
    google_analytics_page_id = 'CompaniesHouseEnrolment'
    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_user={
            COMPANY_SEARCH: 2,
            ADDRESS_SEARCH: 2,
            BUSINESS_INFO: 2,
            PERSONAL_INFO: 3,
        },
        step_counter_anon={
            USER_ACCOUNT: 2,
            VERIFICATION: 3,
            COMPANY_SEARCH: 4,
            ADDRESS_SEARCH: 4,
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
        (COMPANY_SEARCH, forms.CompaniesHouseCompanySearch),
        (ADDRESS_SEARCH, forms.CompaniesHouseAddressSearch),
        (BUSINESS_INFO, forms.CompaniesHouseBusinessDetails),
        (PERSONAL_INFO, core.forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        COMPANY_SEARCH: 'enrolment/companies-house-company-search.html',
        ADDRESS_SEARCH: 'enrolment/address-search.html',
        BUSINESS_INFO: 'enrolment/companies-house-business-details.html',
        PERSONAL_INFO: 'enrolment/companies-house-personal-details.html',
        FINISHED: 'enrolment/companies-house-success.html',
    }

    def address_search_condition(self):
        company = self.get_cleaned_data_for_step(COMPANY_SEARCH)
        if not company:
            return True
        return helpers.is_companies_house_details_incomplete(company['company_number'])

    condition_dict = {
        ADDRESS_SEARCH: address_search_condition,
        **mixins.CreateUserAccountMixin.condition_dict
    }

    def get_form_kwargs(self, step=None):
        form_kwargs = super().get_form_kwargs(step=step)
        if step == BUSINESS_INFO:
            previous_data = self.get_cleaned_data_for_step(COMPANY_SEARCH)
            if previous_data:
                form_kwargs['is_enrolled'] = helpers.get_is_enrolled(previous_data['company_number'])
        return form_kwargs

    def get_form_initial(self, step):
        form_initial = super().get_form_initial(step)
        if step == ADDRESS_SEARCH:
            company = self.get_cleaned_data_for_step(COMPANY_SEARCH)
            form_initial['company_name'] = company['company_name']
        elif step == BUSINESS_INFO:
            company_search_step_data = self.get_cleaned_data_for_step(COMPANY_SEARCH)
            company_data = helpers.get_companies_house_profile(company_search_step_data['company_number'])
            company = helpers.CompanyParser(company_data)
            form_initial['company_name'] = company.name
            form_initial['company_number'] = company.number
            form_initial['sic'] = company.nature_of_business
            form_initial['date_of_creation'] = company.date_of_creation
            if self.address_search_condition():
                address_step_data = self.get_cleaned_data_for_step(ADDRESS_SEARCH)
                form_initial['address'] = address_step_data['address']
                form_initial['postal_code'] = address_step_data['postal_code']
            else:
                form_initial['address'] = company.address
                form_initial['postal_code'] = company.postcode
        return form_initial

    def serialize_form_list(self, form_list):
        return {
            **super().serialize_form_list(form_list),
            'company_type': 'COMPANIES_HOUSE',
        }

    def done(self, form_list, form_dict, **kwargs):
        data = self.serialize_form_list(form_list)
        is_enrolled = helpers.get_is_enrolled(data['company_number'])
        if is_enrolled:
            helpers.create_company_member(
                sso_session_id=self.request.user.session_id,
                data={
                    'company': data['company_number'],
                    'sso_id': self.request.user.id,
                    'company_email': self.request.user.email,
                    'name': self.request.user.full_name,
                    'mobile_number': data.get('phone_number', ''),
                }
            )

            helpers.notify_company_admins_member_joined(
                sso_session_id=self.request.user.session_id,
                email_data={
                    'company_name': data['company_name'],
                    'name': self.request.user.full_name,
                    'email': self.request.user.email,
                    'profile_remove_member_url': self.request.build_absolute_uri(
                        reverse('business-profile-admin-tools')
                    ),
                    'report_abuse_url': urls.domestic.FEEDBACK
                }, form_url=self.request.path)

            return self.redirect_to_ingress_or_finish()
        else:
            return super().done(form_list, form_dict=form_dict, **kwargs)


class NonCompaniesHouseEnrolmentView(
    mixins.CreateBusinessProfileMixin,
    BaseEnrolmentWizardView
):
    google_analytics_page_id = 'NonCompaniesHouseEnrolment'
    steps_list_labels = [
        PROGRESS_STEP_LABEL_BUSINESS_TYPE,
        PROGRESS_STEP_LABEL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_BUSINESS_DETAILS,
        PROGRESS_STEP_LABEL_PERSONAL_INFO,
    ]

    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_user={
            ADDRESS_SEARCH: 2,
            PERSONAL_INFO: 3,
        },
        step_counter_anon={
            USER_ACCOUNT: 2,
            VERIFICATION: 3,
            ADDRESS_SEARCH: 4,
            PERSONAL_INFO: 5,
        },
    )

    form_list = (
        (USER_ACCOUNT, forms.UserAccount),
        (VERIFICATION, forms.UserAccountVerification),
        (ADDRESS_SEARCH, forms.NonCompaniesHouseSearch),
        (PERSONAL_INFO, core.forms.PersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        ADDRESS_SEARCH: 'enrolment/address-search.html',
        PERSONAL_INFO: 'enrolment/non-companies-house-personal-details.html',
        FINISHED: 'enrolment/non-companies-house-success.html',
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.steps.current == PERSONAL_INFO:
            context['company'] = self.get_cleaned_data_for_step(ADDRESS_SEARCH)
        return context


class IndividualUserEnrolmentInterstitialView(
    mixins.ReadUserIntentMixin,
    mixins.GA360Mixin,
    TemplateView
):
    google_analytics_page_id = 'IndividualEnrolmentInterstitial'
    template_name = 'enrolment/individual-interstitial.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.has_business_profile_intent_in_session():
            url = reverse(
                'enrolment-individual', kwargs={'step': PERSONAL_INFO}
            )
            return redirect(url)
        return super().dispatch(request, *args, **kwargs)


class IndividualUserEnrolmentView(BaseEnrolmentWizardView):
    google_analytics_page_id = 'IndividualEnrolment'
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
        return self.redirect_to_ingress_or_finish()


class CollaboratorEnrolmentView(BaseEnrolmentWizardView):
    google_analytics_page_id = 'CollaboratorEnrolment'
    steps_list_labels = [
        PROGRESS_STEP_LABEL_INDIVIDUAL_USER_ACCOUNT,
        PROGRESS_STEP_LABEL_VERIFICATION,
        PROGRESS_STEP_LABEL_PERSONAL_INFO
    ]

    progress_conf = helpers.ProgressIndicatorConf(
        step_counter_user={
            PERSONAL_INFO: 2
        },
        step_counter_anon={
            USER_ACCOUNT: 1,
            VERIFICATION: 2,
            PERSONAL_INFO: 3
        },
    )

    form_list = (
        (USER_ACCOUNT, forms.UserAccountCollaboration),
        (VERIFICATION, forms.UserAccountVerification),
        (PERSONAL_INFO, forms.IndividualPersonalDetails),
    )

    templates = {
        USER_ACCOUNT: 'enrolment/individual-user-account.html',
        VERIFICATION: 'enrolment/user-account-verification.html',
        PERSONAL_INFO: 'enrolment/individual-personal-details.html',
        FINISHED: 'enrolment/individual-success.html',
        INVITE_EXPIRED: 'enrolment/individual-collaborator-invite-expired.html'
    }

    def get(self, *args, **kwargs):
        if 'invite_key' in self.request.GET:
            self.request.session[SESSION_KEY_INVITE_KEY] = self.request.GET['invite_key']
            if not self.collaborator_invition:
                contact_url = urls.domestic.CONTACT_US / 'domestic/enquiries/'
                context = {
                    'contact_url': contact_url,
                    'description': (
                        'This invitation has expired, please contact your business profile administrator to request a '
                        f'new invitation or <a href="{contact_url}"">contact us.</a>'
                    )
                }
                return TemplateResponse(
                    request=self.request,
                    template=self.templates[INVITE_EXPIRED],
                    context=context,
                )
        # at this point all the steps will be hidden as the user is logged
        # in and has a user profile, so the normal `get` method fails with
        # IndexError, meaning `done` will not be hit. Working around this:
        if self.steps.count == 0:
            return self.render_done(form=None, step=FINISHED)
        return super().get(*args, **kwargs)

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def create_company_profile(self):
        helpers.collaborator_invite_accept(
            sso_session_id=self.request.user.session_id,
            invite_key=self.request.session[SESSION_KEY_INVITE_KEY],
        )

    @cached_property
    def collaborator_invition(self):
        return helpers.collaborator_invite_retrieve(self.request.session[SESSION_KEY_INVITE_KEY])

    def get_context_data(self, **kwargs):
        return super().get_context_data(collaborator_invition=self.collaborator_invition, **kwargs,)

    def get_form_initial(self, step):
        form_initial = super().get_form_initial(step)
        if step == USER_ACCOUNT:
            form_initial['email'] = self.collaborator_invition['collaborator_email']
        return form_initial

    def done(self, *args, **kwargs):
        self.create_company_profile()
        messages.success(self.request, 'Account created')
        return redirect('business-profile')


class PreVerifiedEnrolmentView(BaseEnrolmentWizardView):
    google_analytics_page_id = 'PreVerifiedEnrolment'
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
            context['company'] = self.request.session[SESSION_KEY_COMPANY_DATA]
        return context

    def done(self, form_list, **kwargs):
        try:
            self.claim_company(self.serialize_form_list(form_list))
        except HTTPError:
            return TemplateResponse(self.request, self.templates[FAILURE])
        else:
            messages.success(self.request, 'Business profile created')
            return redirect('business-profile')

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
    mixins.RedirectLoggedInMixin,
    mixins.RestartOnStepSkipped,
    mixins.ProgressIndicatorMixin,
    mixins.StepsListMixin,
    mixins.CreateUserAccountMixin,
    mixins.GA360Mixin,
    NamedUrlSessionWizardView
):
    google_analytics_page_id = 'ResendVerificationCode'
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
            verification_missing_url=urls.domestic.CONTACT_US / 'triage/great-account/verification-missing/',
            contact_url=urls.domestic.CONTACT_US / 'domestic/',
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


class EnrolmentOverseasBusinessView(
    mixins.ReadUserIntentMixin,
    mixins.GA360Mixin, TemplateView
):
    google_analytics_page_id = 'OverseasBusinessEnrolment'
    template_name = 'enrolment/overseas-business.html'
