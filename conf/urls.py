import directory_healthcheck.views

from django.conf.urls import include, url

from profile.api import views as api_views
from profile.eig_apps import views as eig_apps_views
from profile.fab import views as fab_views
from profile.soo import views as soo_views
from profile.exops import views as exops_views
import healthcheck.views


healthcheck_urls = [
    url(
        r'^single-sign-on/$',
        healthcheck.views.SingleSignOnAPIView.as_view(),
        name='single-sign-on'
    ),
    url(
        r'^ping/$',
        directory_healthcheck.views.PingView.as_view(),
        name='ping'
    ),
    url(
        r'^sentry/$',
        directory_healthcheck.views.SentryHealthcheckView.as_view(),
        name='sentry'
    ),
]

api_urls = [
    url(
        r'^v1/directory/supplier/$',
        api_views.ExternalSupplierAPIView.as_view(),
        name='external-supplier'
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
        eig_apps_views.LandingPageView.as_view(),
        name='index'
    ),
    url(
        r'^about/$',
        eig_apps_views.AboutView.as_view(),
        name='about'
    ),
    url(
        r'^find-a-buyer/$',
        fab_views.FindABuyerView.as_view(),
        name='find-a-buyer'
    ),
    url(
        r'^selling-online-overseas/$',
        soo_views.SellingOnlineOverseasView.as_view(),
        name='selling-online-overseas'
    ),
    url(
        r'^export-opportunities/applications/$',
        exops_views.ExportOpportunitiesApplicationsView.as_view(),
        name='export-opportunities-applications'
    ),
    url(
        r'^export-opportunities/email-alerts/$',
        exops_views.ExportOpportunitiesEmailAlertsView.as_view(),
        name='export-opportunities-email-alerts'
    ),
]
