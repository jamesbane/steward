from django.conf.urls import url
import deploy.views

urlpatterns = [
    url(r'^$', deploy.views.IndexRedirectView.as_view(), name='index'),
    url(r'^sites/$', deploy.views.SiteListView.as_view(), name='site-list'),
    url(r'^sites/import$', deploy.views.SiteCreateView.as_view(), name='site-create'),
    url(r'^site/(?P<pk>\d+)/$', deploy.views.SiteDetailView.as_view(), name='site-detail'),
    url(r'^device/(?P<pk>\d+)/$', deploy.views.DeviceDetailView.as_view(), name='device-detail'),
    url(r'^device/(?P<pk>\d+)/update$', deploy.views.DeviceUpdateView.as_view(), name='device-update'),
]
