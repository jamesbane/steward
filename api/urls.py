from sys import path

from django.conf.urls import url, include

import routing.api.urls
import tools.api.urls
from rest_framework import views

from api.views import RootAPIView, CustomAuthToken

urlpatterns = [
    url(r'^$', RootAPIView.as_view(), name='index'),
    url(r'^routing/', include(routing.api.urls)),
    url(r'^tools/', include(tools.api.urls)),
    url(r'^api-token-auth/', CustomAuthToken.as_view()),
]
