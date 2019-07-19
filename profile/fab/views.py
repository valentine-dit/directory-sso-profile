from directory_api_client.client import api_client
from formtools.wizard.views import NamedUrlSessionWizardView
from raven.contrib.django.raven_compat.models import client as sentry_client
from requests.exceptions import RequestException

from django.conf import settings
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import DefaultStorage
from django.shortcuts import redirect, Http404
from django.views.generic import TemplateView, FormView

import core.mixins
from profile.fab import forms, helpers

BASIC = 'details'
MEDIA = 'images'


class FindABuyerView(TemplateView):
    template_name_fab_user = 'fab/profile.html'
    template_name_not_fab_user = 'fab/is-not-fab-user.html'

    SUCCESS_MESSAGES = {
        'owner-transferred': (
            'We’ve sent a confirmation email to the new profile owner.'
        ),
        'user-added': (
            'We’ve emailed the person you want to add to this account.'
        ),
        'user-removed': 'User successfully removed from your profile.',
    }

    def get(self, *args, **kwargs):
        for key, message in self.SUCCESS_MESSAGES.items():
            if key in self.request.GET:
                messages.add_message(self.request, messages.SUCCESS, message)
        return super().get(*args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        if self.request.user.company:
            template_name = self.template_name_fab_user
        else:
            template_name = self.template_name_not_fab_user
        return [template_name]

    def is_company_profile_owner(self):
        if not self.request.user.company:
            return False
        response = api_client.supplier.retrieve_profile(
            sso_session_id=self.request.user.session_id,
        )
        response.raise_for_status()
        parsed = response.json()
        return parsed['is_company_owner']

    def get_context_data(self):
        if self.request.user.is_authenticated and self.request.user.company:
            company = self.request.user.company.serialize_for_template()
        else:
            company = None

        return {
            'fab_tab_classes': 'active',
            'is_profile_owner': self.is_company_profile_owner(),
            'company': company,
            'FAB_EDIT_COMPANY_LOGO_URL': settings.FAB_EDIT_COMPANY_LOGO_URL,
            'FAB_EDIT_PROFILE_URL': settings.FAB_EDIT_PROFILE_URL,
            'FAB_ADD_CASE_STUDY_URL': settings.FAB_ADD_CASE_STUDY_URL,
            'FAB_REGISTER_URL': settings.FAB_REGISTER_URL,
            'FAB_ADD_USER_URL': settings.FAB_ADD_USER_URL,
            'FAB_REMOVE_USER_URL': settings.FAB_REMOVE_USER_URL,
            'FAB_TRANSFER_ACCOUNT_URL': settings.FAB_TRANSFER_ACCOUNT_URL,
        }


class BaseFormView(FormView):

    success_url = reverse_lazy('find-a-buyer')

    def get_initial(self):
        return self.request.user.company.serialize_for_form()

    def form_valid(self, form):
        try:
            response = api_client.company.update_profile(
                sso_session_id=self.request.user.session_id,
                data=self.serialize_form(form)
            )
            response.raise_for_status()
        except RequestException:
            self.send_update_error_to_sentry(
                user=self.request.user,
                api_response=response
            )
            raise
        else:
            if self.success_message:
                messages.success(self.request, self.success_message)
            return redirect(self.success_url)

    def serialize_form(self, form):
        return form.cleaned_data

    @staticmethod
    def send_update_error_to_sentry(user, api_response):
        # This is needed to not include POST data (e.g. binary image), which
        # was causing sentry to fail at sending
        sentry_client.context.clear()
        sentry_client.user_context(
            {'hashed_uuid': user.hashed_uuid, 'user_email': user.email}
        )
        sentry_client.captureMessage(
            message='Updating company profile failed',
            data={},
            extra={'api_response': str(api_response.content)}
        )


class SocialLinksFormView(BaseFormView):
    template_name = 'fab/social-links-form.html'
    form_class = forms.SocialLinksForm
    success_message = 'Social links updated'


class EmailAddressFormView(BaseFormView):
    template_name = 'fab/email-address-form.html'
    form_class = forms.EmailAddressForm
    success_message = 'Email address updated'


class DescriptionFormView(BaseFormView):
    form_class = forms.DescriptionForm
    template_name = 'fab/description-form.html'
    success_message = 'Description updated'


class WebsiteFormView(BaseFormView):
    form_class = forms.WebsiteForm
    template_name = 'fab/website-form.html'
    success_message = 'Website updated'


class LogoFormView(BaseFormView):
    def get_initial(self):
        return {}
    form_class = forms.LogoForm
    template_name = 'fab/logo-form.html'
    success_message = 'Logo updated'


class ExpertiseRoutingFormView(FormView):

    form_class = forms.ExpertiseRoutingForm
    template_name = 'fab/expertise-routing-form.html'

    def form_valid(self, form):
        if form.cleaned_data['choice'] == form.REGION:
            url = reverse('find-a-buyer-expertise-regional')
        elif form.cleaned_data['choice'] == form.COUNTRY:
            url = reverse('find-a-buyer-expertise-countries')
        elif form.cleaned_data['choice'] == form.INDUSTRY:
            url = reverse('find-a-buyer-expertise-industries')
        elif form.cleaned_data['choice'] == form.LANGUAGE:
            url = reverse('find-a-buyer-expertise-languages')
        else:
            raise NotImplementedError
        return redirect(url)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            company=self.request.user.company.serialize_for_template(),
            **kwargs,
        )


class RegionalExpertiseFormView(BaseFormView):
    form_class = forms.RegionalExpertiseForm
    template_name = 'fab/expertise-regions-form.html'
    success_message = None
    success_url = reverse_lazy('find-a-buyer-expertise-routing')


class CountryExpertiseFormView(BaseFormView):
    form_class = forms.CountryExpertiseForm
    template_name = 'fab/expertise-countries-form.html'
    success_message = None
    success_url = reverse_lazy('find-a-buyer-expertise-routing')


class IndustryExpertiseFormView(BaseFormView):
    form_class = forms.IndustryExpertiseForm
    template_name = 'fab/expertise-industry-form.html'
    success_message = None
    success_url = reverse_lazy('find-a-buyer-expertise-routing')


class LanguageExpertiseFormView(BaseFormView):
    form_class = forms.LanguageExpertiseForm
    template_name = 'fab/expertise-language-form.html'
    success_message = None
    success_url = reverse_lazy('find-a-buyer-expertise-routing')


class BusinessDetailsFormView(BaseFormView):
    template_name = 'fab/business-details-form.html'

    def get_form_class(self):
        if self.request.user.company.is_sole_trader:
            return forms.SoleTraderBusinessDetailsForm
        return forms.CompaniesHouseBusinessDetailsForm

    success_message = 'Business details updated'


class PublishFormView(BaseFormView):
    form_class = forms.PublishForm
    template_name = 'fab/find-a-buyer-publsh.html'
    success_url = reverse_lazy('find-a-buyer')
    success_message = 'Published status successfully changed'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.company.is_publishable:
            return redirect('find-a-buyer')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'company': self.request.user.company.serialize_for_form()
        }

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            company=self.request.user.company.serialize_for_template()
        )


class BaseCaseStudyWizardView(NamedUrlSessionWizardView):

    done_step_name = 'finished'

    file_storage = DefaultStorage()

    form_list = (
        (BASIC, forms.CaseStudyBasicInfoForm),
        (MEDIA, forms.CaseStudyRichMediaForm),
    )
    templates = {
        BASIC: 'fab/case-study-basic-form.html',
        MEDIA: 'fab/case-study-media-form.html',
    }

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def serialize_form_list(self, form_list):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)
        # the case studies edit view pre-populates the image fields with the
        # url of the existing value (rather than the real file). Things would
        # get confused if we send a string instead of a file here.
        for field in ['image_one', 'image_two', 'image_three']:
            value = data.get(field)
            if not value or isinstance(value, str):
                del data[field]
        return data


class CaseStudyWizardEditView(BaseCaseStudyWizardView):

    def get_form_initial(self, step):
        response = api_client.company.retrieve_private_case_study(
            sso_session_id=self.request.user.session_id,
            case_study_id=self.kwargs['id'],
        )
        if response.status_code == 404:
            raise Http404()
        response.raise_for_status()
        return response.json()

    def done(self, form_list, *args, **kwags):
        response = api_client.company.update_case_study(
            data=self.serialize_form_list(form_list),
            case_study_id=self.kwargs['id'],
            sso_session_id=self.request.user.session_id,
        )
        response.raise_for_status()
        return redirect('find-a-buyer')

    def get_step_url(self, step):
        return reverse(
            self.url_name, kwargs={'step': step, 'id': self.kwargs['id']}
        )


class CaseStudyWizardCreateView(BaseCaseStudyWizardView):
    def done(self, form_list, *args, **kwags):
        response = api_client.company.create_case_study(
            sso_session_id=self.request.user.session_id,
            data=self.serialize_form_list(form_list),
        )
        response.raise_for_status()
        return redirect('find-a-buyer')


class AdminToolsView(TemplateView):

    template_name = 'fab/admin-tools.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            FAB_ADD_USER_URL=settings.FAB_ADD_USER_URL,
            FAB_REMOVE_USER_URL=settings.FAB_REMOVE_USER_URL,
            FAB_TRANSFER_ACCOUNT_URL=settings.FAB_TRANSFER_ACCOUNT_URL,
            company=self.request.user.company.serialize_for_template(),
            has_collaborators=helpers.has_collaborators(
                self.request.user.session_id
            ),
            **kwargs,
        )


class ProductsServicesRoutingFormView(FormView):

    form_class = forms.ExpertiseProductsServicesRoutingForm
    template_name = 'fab/products-services-routing-form.html'

    def form_valid(self, form):
        url = reverse(
            'find-a-buyer-expertise-products-services',
            kwargs={'category': form.cleaned_data['choice']}
        )
        return redirect(url)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            company=self.request.user.company.serialize_for_template(),
            **kwargs,
        )


class ProductsServicesFormView(BaseFormView):
    success_message = None
    success_url = reverse_lazy(
        'find-a-buyer-expertise-products-services-routing'
    )
    field_name = 'expertise_products_services'

    def dispatch(self, *args, **kwargs):
        form = forms.ExpertiseProductsServicesRoutingForm(
            data={'choice': self.kwargs['category']}
        )
        if not form.is_valid():
            return redirect(self.success_url)
        return super().dispatch(*args, **kwargs)

    form_class = forms.ExpertiseProductsServicesForm
    template_name = 'fab/products-services-form.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            category=self.kwargs['category'].replace('-', ' '),
            **kwargs
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['category'] = self.kwargs['category']
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        value = initial[self.field_name].get(self.kwargs['category'], [])
        return {self.field_name: '|'.join(value)}

    def serialize_form(self, form):
        return {
            self.field_name: {
                **self.request.user.company.data[self.field_name],
                self.kwargs['category']: form.cleaned_data[self.field_name],
            }
        }


class ProductsServicesOtherFormView(BaseFormView):
    success_message = None
    success_url = reverse_lazy(
        'find-a-buyer-expertise-products-services-routing'
    )
    field_name = 'expertise_products_services'
    form_class = forms.ExpertiseProductsServicesOtherForm
    template_name = 'fab/products-services-other-form.html'

    def get_initial(self):
        initial = super().get_initial()
        value = initial[self.field_name].get('other', [])
        return {self.field_name: ', '.join(value)}

    def serialize_form(self, form):
        return {
            self.field_name: {
                **self.request.user.company.data[self.field_name],
                'other': form.cleaned_data[self.field_name],
            }
        }


class PersonalDetailsFormView(
    core.mixins.CreateUserProfileMixin, SuccessMessageMixin, FormView
):
    template_name = 'fab/personal-details-form.html'
    form_class = core.forms.PersonalDetails
    success_url = reverse_lazy('find-a-buyer')
    success_message = 'Details updated'

    def form_valid(self, form):
        self.create_user_profile(form)
        return super().form_valid(form)
