from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
import django.views.static


import steward.views


urlpatterns = [
    url(r'^$', steward.views.IndexRedirectView.as_view(), name='index'),

    url(r'^accounts/', include('django.contrib.auth.urls', namespace='auth')),
    url(r'^admin/', admin.site.urls),
    url(r'^dashboards/', include('dashboard.urls', namespace='dashboard')),
    url(r'^deploy/', include('deploy.urls', namespace='deploy')),
    url(r'^dms/', include('dms.urls', namespace='dms')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^tools/', include('tools.urls', namespace='tools')),
    url(r'^protected/(?P<path>.*)$', steward.views.ProtectedFileView.as_view()),
]

# Allow serving media content if in debug mode
if settings.DEBUG == True:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', django.views.static.serve, {'document_root': settings.MEDIA_ROOT,}),
    ]
