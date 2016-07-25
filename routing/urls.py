from django.conf.urls import url

# Application
import routing.views


urlpatterns = [
    url(r'^numbers/search$', routing.views.NumberSearchView.as_view(), name='number-search'),
    url(r'^numbers/(?P<cc>\d+)/(?P<number>\d+)/$', routing.views.NumberDetailView.as_view(), name='number-detail'),
    url(r'^routes$', routing.views.RouteListView.as_view(), name='route-list'),
    url(r'^routes/add$', routing.views.RouteCreateView.as_view(), name='route-create'),
    url(r'^routes/(?P<pk>\d+)/$', routing.views.RouteDetailView.as_view(), name='route-detail'),
    url(r'^routes/(?P<pk>\d+)/edit$', routing.views.RouteUpdateView.as_view(), name='route-update'),
    url(r'^routes/(?P<pk>\d+)/delete$', routing.views.RouteDeleteView.as_view(), name='route-delete'),
    url(r'^transmissions$', routing.views.TransmissionListView.as_view(), name='transmission-list'),
    url(r'^transmissions/(?P<pk>\d+)/$', routing.views.TransmissionDetailView.as_view(), name='transmission-detail'),
    url(r'^UDA6.txt$', routing.views.UDA6View.as_view(), name='UDA6.txt'),
]
