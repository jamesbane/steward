# Django
from django.conf.urls import url, include

# Third Party
from rest_framework import routers

# Application
from routing.api import views


# Router
router = routers.DefaultRouter()
# router.register(r'numbers', views.NumberViewSet, base_name='routing-number')
router.register(r'records', views.RecordViewSet, base_name='routing-record')
router.register(r'routes', views.RouteViewSet, base_name='routing-route')

urlpatterns = [
    url(r'^$', views.RouteRootView.as_view(), name='routing-root'),
    url(r'^numbers/$', views.NumberListView.as_view(), name='routing-number-list'),
    url(r'^numbers/(?P<cc>\d+)/(?P<number>\d+)/$', views.NumberDetailView.as_view(), name='routing-number-detail'),
    url(r'^', include(router.urls)),
]
