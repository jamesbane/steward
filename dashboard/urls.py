from django.conf.urls import url
import dashboard.views

urlpatterns = [
    url(r'^$', dashboard.views.EmptyDashboardView.as_view(), name='empty'),
    url(r'^voip$', dashboard.views.VoipDashboardView.as_view(), name='voip'),
]
