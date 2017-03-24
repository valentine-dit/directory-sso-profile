from django.conf.urls import url

from profile.eig_apps import views as eig_apps_views


urlpatterns = [
    url(
        r'^$',
        eig_apps_views.LandingPageView.as_view(),
        name='index'
    ),
]
