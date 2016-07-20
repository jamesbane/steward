from django.conf.urls import url, include

from api import views
import routing.api.urls
import tools.api.urls

urlpatterns = [
    url(r'^$', views.RootAPIView.as_view(), name='index'),
    url(r'^routing/', include(routing.api.urls)),
    url(r'^tools/', include(tools.api.urls)),
]
