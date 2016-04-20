"""tools URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
import tools.views

urlpatterns = [
    url(r'^$', tools.views.IndexView.as_view(), name='index'),
    # Tools
    url(r'^tools/device-specific-migration-tool$', tools.views.DeviceSpecificMigrationToolView.as_view(), name='device-specific-migration-tool'),
    url(r'^tools/fraud-compliance-reset-tool$', tools.views.FraudComplianceResetToolView.as_view(), name='fraud-compliance-reset-tool'),
    url(r'^tools/lab-rebuild-tool$', tools.views.LabResetToolView.as_view(), name='lab-rebuild-tool'),
    url(r'^tools/push-to-talk-configurator$', tools.views.PushToTalkConfiguratorToolView.as_view(), name='push-to-talk-configurator'),
    # Reports
    url(r'^reports/firmware-report$', tools.views.FirmwareReportView.as_view(), name='firmware-report'),
    url(r'^reports/registrations$', tools.views.RegistrationReportView.as_view(), name='registrations-report'),
    url(r'^reports/registration-by-type$', tools.views.RegistrationByTypeReportView.as_view(), name='registration-by-type-report'),
    url(r'^reports/tag-report$', tools.views.TagReportView.as_view(), name='tag-report'),
    # Results
    url(r'^jobs/$', tools.views.ProcessListView.as_view(), name='process-list'),
    url(r'^results/(?P<pk>\d+)/$', tools.views.ProcessDetailView.as_view(), name='process-detail'),
]
