from django.conf.urls import url

from profile.eig_apps import views as eig_apps_views
from profile.fab import views as fab_views
from profile.soo import views as soo_views
from profile.exops import views as exops_views


urlpatterns = [
    url(
        r'^$',
        eig_apps_views.LandingPageView.as_view(),
        name='index'
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
        r'^export-opportunities/$',
        exops_views.ExportOpportunitiesView.as_view(),
        name='export-opportunities'
    ),
]
