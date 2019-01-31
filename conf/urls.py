import directory_healthcheck.views

from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView

import core.views
import enrolment.views
import profile.api.views
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
        r'^v1/directory/supplier/$',
        profile.api.views.ExternalSupplierAPIView.as_view(),
        name='external-supplier'
    ),
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
        r'^find-a-buyer/$',
        profile.fab.views.FindABuyerView.as_view(),
        name='find-a-buyer'
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
        RedirectView.as_view(
            url=reverse_lazy('enrolment', kwargs={'step': 'business-type'})
        ),
        name='enrol-redirect'
    ),
    url(
        r'^enrol/done/$',
        enrolment.views.EnrolmentSuccess.as_view(),
        name='enrolment-success'
    ),
    url(
        r'^enrol/(?P<step>.+)/$',
        enrolment.views.EnrolmentView.as_view(
            url_name='enrolment',
            done_step_name='finished'
        ),
        name='enrolment'
    ),

]
