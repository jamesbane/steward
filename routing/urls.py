from django.conf.urls import url

# Application
import routing.views


urlpatterns = [
    url(r'^fraud-bypass$', routing.views.FraudBypassListView.as_view(), name='fraud-bypass-list'),
    url(r'^fraud-bypass-history$', routing.views.FraudBypassHistoryListView.as_view(), name='fraud-bypass-history'),
    url(r'^fraud-bypass/create$', routing.views.FraudBypassCreateView.as_view(), name='fraud-bypass-create'),
    url(r'^fraud-bypass/(?P<pk>\d+)/delete$', routing.views.FraudBypassDeleteView.as_view(), name='fraud-bypass-delete'),
    url(r'^fraud-bypass/(?P<cc>\d+)/(?P<number>\d+)/$', routing.views.FraudBypassHistoryView.as_view(), name='fraud-bypass-history'),

    url(r'^numbers/search$', routing.views.NumberSearchView.as_view(), name='number-search'),
    url(r'^numbers/(?P<cc>\d+)/(?P<number>\d+)/$', routing.views.NumberHistoryView.as_view(), name='number-detail'),
    url(r'^number-history/$', routing.views.NumberHistoryListView.as_view(), name='number-history'),

    url(r'^outbound-routes$', routing.views.OutboundRouteListView.as_view(), name='outbound-route-list'),
    url(r'^outbound-routes-history$', routing.views.OutboundRouteHistoryListView.as_view(), name='outbound-route-history'),
    url(r'^outbound-routes/create$', routing.views.OutboundRouteCreateView.as_view(), name='outbound-route-create'),
    url(r'^outbound-route/(?P<pk>\d+)/edit$', routing.views.OutboundRouteUpdateView.as_view(), name='outbound-route-update'),
    url(r'^outbound-route/(?P<pk>\d+)/delete$', routing.views.OutboundRouteDeleteView.as_view(), name='outbound-route-delete'),

    url(r'^remote-call-forward$', routing.views.RemoteCallForwardSearchView.as_view(), name='remote-call-forward-search'),
    url(r'^remote-call-forward/history$', routing.views.RemoteCallForwardHistoryListView.as_view(), name='remote-call-forward-history'),
    url(r'^remote-call-forward/(?P<called_number>\d+)/$', routing.views.RemoteCallForwardHistoryDetailView.as_view(), name='remote-call-forward-history-detail'),

    url(r'^routes$', routing.views.RouteListView.as_view(), name='route-list'),
    url(r'^routes/add$', routing.views.RouteCreateView.as_view(), name='route-create'),
    url(r'^routes/(?P<pk>\d+)/$', routing.views.RouteDetailView.as_view(), name='route-detail'),
    url(r'^routes/(?P<pk>\d+)/edit$', routing.views.RouteUpdateView.as_view(), name='route-update'),
    url(r'^routes/(?P<pk>\d+)/delete$', routing.views.RouteDeleteView.as_view(), name='route-delete'),

    url(r'^transmissions$', routing.views.TransmissionListView.as_view(), name='transmission-list'),
    url(r'^transmissions/(?P<pk>\d+)/$', routing.views.TransmissionDetailView.as_view(), name='transmission-detail'),
]
