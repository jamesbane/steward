# Django
from django.conf.urls import url, include

# Third Party
from rest_framework import routers

# Application
from routing.api import views


# Router
router = routers.DefaultRouter()
router.register(r'records', views.RecordViewSet, base_name='routing-record')
router.register(r'routes', views.RouteViewSet, base_name='routing-route')

urlpatterns = [
    url(r'^$', views.RouteRootView.as_view(), name='routing-root'),
    url(r'^numbers/$', views.NumberListView.as_view(), name='routing-number-list'),
    url(r'^numbers/(?P<cc>\d+)/(?P<number>\d+)/$', views.NumberDetailView.as_view(), name='routing-number-detail'),
    url(r'^fraud-bypass/$', views.FraudBypassListView.as_view(), name='routing-fraud-bypass-list'),
    url(r'^fraud-bypass/(?P<cc>\d+)/(?P<number>\d+)/$', views.FraudBypassDetailView.as_view(), name='routing-fraud-bypass-detail'),
    url(r'^outbound-route/$', views.OutboundRouteListView.as_view(), name='routing-outbound-route-list'),
    url(r'^outbound-route/(?P<number>\d+)/$', views.OutboundRouteDetailView.as_view(), name='routing-outbound-route-detail'),
    url(r'^', include(router.urls)),
]
