from django.conf.urls import url

from profile import views as profile_views


urlpatterns = [
    url(
        r'^$',
        profile_views.LandingPageView.as_view(),
        name='index'
    ),
]
