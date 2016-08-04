# Django
from django.conf.urls import url, include

# Third Party
from rest_framework import routers

# Application
from tools.api import views


# Router
router = routers.DefaultRouter()
router.register(r'processes', views.ProcessDetailAPIViewSet, base_name='tools-process')
router.register(r'registrations', views.RegistrationAPIViewSet, base_name='tools-registration')


urlpatterns = [
    url(r'^$', views.ToolsRootView.as_view(), name='tools-root'),
    url(r'^dect-lookup$', views.DeviceDectLookupAPIView.as_view(), name='tools-dect-lookup'),
    url(r'^', include(router.urls)),
]
