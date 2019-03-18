import directory_healthcheck.views

from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.views.generic import RedirectView

import core.views
import enrolment.views
import profile.eig_apps.views
import profile.exops.views
import profile.fab.views
import profile.soo.views


healthcheck_urls = [
    url(
        r'^$',
        directory_healthcheck.views.HealthcheckView.as_view(),
        name='healthcheck'
    ),
    url(
        r'^ping/$',
        directory_healthcheck.views.PingView.as_view(),
        name='ping'
    ),
]

api_urls = [
    url(
        r'^v1/companies-house-search/$',
        core.views.CompaniesHouseSearchAPIView.as_view(),
        name='companies-house-search'
    ),
    url(
        r'^v1/postcode-search/$',
        core.views.AddressSearchAPIView.as_view(),
        name='postcode-search'
    ),

]


urlpatterns = [
    url(
        r'^api/',
        include(api_urls, namespace='api', app_name='api')
    ),
    url(
        r'^healthcheck/',
        include(
            healthcheck_urls, namespace='healthcheck', app_name='healthcheck'
        )
    ),
    url(
        r'^$',
        profile.eig_apps.views.LandingPageView.as_view(),
        name='index'
    ),
    url(
        r'^about/$',
        profile.eig_apps.views.AboutView.as_view(),
        name='about'
    ),
    url(
        r'^selling-online-overseas/$',
        profile.soo.views.SellingOnlineOverseasView.as_view(),
        name='selling-online-overseas'
    ),
    url(
        r'^export-opportunities/applications/$',
        profile.exops.views.ExportOpportunitiesApplicationsView.as_view(),
        name='export-opportunities-applications'
    ),
    url(
        r'^export-opportunities/email-alerts/$',
        profile.exops.views.ExportOpportunitiesEmailAlertsView.as_view(),
        name='export-opportunities-email-alerts'
    ),
    url(
        r'^enrol/$',
        enrolment.views.EnrolmentStartView.as_view(),
        name='enrolment-start'
    ),
    url(
        r'^enrol/business-type/$',
        enrolment.views.BusinessTypeRoutingView.as_view(),
        name='enrolment-business-type'
    ),
    url(
        r'^enrol/business-type/companies-house/(?P<step>.+)/$',
        enrolment.views.CompaniesHouseEnrolmentView.as_view(
            url_name='enrolment-companies-house',
            done_step_name='finished'
        ),
        name='enrolment-companies-house'
    ),
    url(
        r'^enrol/business-type/sole-trader/(?P<step>.+)/$',
        enrolment.views.SoleTraderEnrolmentView.as_view(
            url_name='enrolment-sole-trader',
            done_step_name='finished'
        ),
        name='enrolment-sole-trader'
    ),
    url(
        r'^enrol/pre-verified/(?P<step>.+)/$',
        enrolment.views.PreVerifiedEnrolmentView.as_view(
            url_name='enrolment-pre-verified',
            done_step_name='finished'
        ),
        name='enrolment-pre-verified'
    ),
    url(
        r'^enrol/pre-verified/$',
        RedirectView.as_view(
            url=reverse_lazy(
                'enrolment-pre-verified', kwargs={'step': 'user-account'}
            ),
            query_string=True,
        )
    ),
    url(
        r'^enrol/resend-verification/(?P<step>.+)/$',
        enrolment.views.ResendVerificationCodeView.as_view(
            url_name='resend-verification',
            done_step_name='finished'
        ),
        name='resend-verification'
    ),
    url(
        r'^find-a-buyer/$',
        profile.fab.views.FindABuyerView.as_view(),
        name='find-a-buyer'
    ),
    url(
        r'^find-a-buyer/social-links/$',
        profile.fab.views.SocialLinksFormView.as_view(),
        name='find-a-buyer-social'
    ),
    url(
        r'^find-a-buyer/email/$',
        profile.fab.views.EmailAddressFormView.as_view(),
        name='find-a-buyer-email'
    ),
    url(
        r'^find-a-buyer/description/$',
        profile.fab.views.DescriptionFormView.as_view(),
        name='find-a-buyer-description'
    ),
    url(
        r'^find-a-buyer/logo/$',
        profile.fab.views.LogoFormView.as_view(),
        name='find-a-buyer-logo'
    ),
    url(
        r'^find-a-buyer/products-and-services/$',
        profile.fab.views.ProductsServicesFormView.as_view(),
        name='find-a-buyer-products-and-services'
    ),
    url(
        r'^find-a-buyer/publish/$',
        profile.fab.views.PublishFormView.as_view(),
        name='find-a-buyer-publish'
    ),
    url(
        r'^find-a-buyer/business-details/$',
        profile.fab.views.BusinessDetailsFormView.as_view(),
        name='find-a-buyer-business-details'
    ),
    url(
        r'^find-a-buyer/case-study/(?P<id>[0-9]+)/(?P<step>.+)/$',
        profile.fab.views.CaseStudyWizardEditView.as_view(
            url_name='find-a-buyer-case-study-edit'
        ),
        name='find-a-buyer-case-study-edit'
    ),
    url(
        r'^find-a-buyer/case-study/(?P<step>.+)/$',
        profile.fab.views.CaseStudyWizardCreateView.as_view(
            url_name='find-a-buyer-case-study'
        ),
        name='find-a-buyer-case-study'
    ),
    url(
        r'^find-a-buyer/admin/$',
        profile.fab.views.AdminToolsView.as_view(),
        name='find-a-buyer-admin-tools'
    ),
]
