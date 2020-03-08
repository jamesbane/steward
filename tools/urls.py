from django.conf.urls import url

# Application
import tools.views


urlpatterns = [
    url(r'^$', tools.views.IndexView.as_view(), name='index'),
    # Tools
    url(r'^call-park-pickup-configurator$', tools.views.CallParkPickupConfiguratorToolView.as_view(), name='call-park-pickup-configurator'),
    url(r'^dect-configurator$', tools.views.DectConfiguratorToolView.as_view(), name='dect-configurator'),
    url(r'^device-specific-migration-tool$', tools.views.DeviceSpecificMigrationToolView.as_view(), name='device-specific-migration-tool'),
    url(r'^fraud-compliance-reset-tool$', tools.views.FraudComplianceResetToolView.as_view(), name='fraud-compliance-reset-tool'),
    url(r'^lab-rebuild-tool$', tools.views.LabResetToolView.as_view(), name='lab-rebuild-tool'),
    url(r'^push-to-talk-configurator$', tools.views.PushToTalkConfiguratorToolView.as_view(), name='push-to-talk-configurator'),
    url(r'^tag-removal$', tools.views.TagRemovalToolView.as_view(), name='tag-removal'),
    url(r'^speed-dial-configurator$', tools.views.SpeedDialConfiguratorToolView.as_view(), name='speed-dial-configurator'),
    url(r'^trunk-user-audit$', tools.views.TrunkAuditToolView.as_view(), name='trunk-user-audit'),
    url(r'^blf-fixup$', tools.views.BusyLampFieldFixupToolView.as_view(), name='busy-lamp-field-fixup'),
    url(r'^user-loc-lookup$', tools.views.UserLocationLookupToolView.as_view(), name='user-location-lookup'),
    url(r'^device-creds-modify-tool$', tools.views.DeviceCredentialsModifyToolView.as_view(), name='device-creds-modify-tool'),
    # Reports
    url(r'^firmware-report$', tools.views.FirmwareReportView.as_view(), name='firmware-report'),
    url(r'^registrations-report$', tools.views.RegistrationReportView.as_view(), name='registrations-report'),
    url(r'^registration-by-type-report$', tools.views.RegistrationByTypeReportView.as_view(), name='registration-by-type-report'),
    url(r'^tag-report$', tools.views.TagReportView.as_view(), name='tag-report'),
    # Results
    url(r'^jobs/$', tools.views.ProcessListView.as_view(), name='process-list'),
    url(r'^results/(?P<pk>\d+)/$', tools.views.ProcessDetailView.as_view(), name='process-detail'),
]
