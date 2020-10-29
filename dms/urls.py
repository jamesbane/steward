from django.conf.urls import url
import dms.views

urlpatterns = [
    url(r'^000000000000\.cfg$', dms.views.PolycomDefaultView.as_view(), name='polycom-default'),
    url(r'^polycom-resync\.cfg$', dms.views.PolycomResyncView.as_view(), name='polycom-resync'),
    url(r'^(?P<slug>[0-9a-fA-F]{12})-phone\.cfg$', dms.views.PolycomView.as_view(), name='polycom'),
]
