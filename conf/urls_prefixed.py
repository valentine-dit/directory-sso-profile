from django.conf.urls import url, include

import conf.urls


urlpatterns = [
    url(
        r'^profile/',
        include(conf.urls.urlpatterns)
    )
]
