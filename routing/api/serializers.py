from routing import models

from rest_framework import serializers
from rest_framework.reverse import reverse, reverse_lazy


class RecordSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:routing-record-detail')
    class Meta:
        model = models.Record
        fields = ('url', 'id', 'route', 'order', 'preference', 'flags', 'service', 'regex', 'replacement')



class RouteSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:routing-route-detail')
    records = RecordSerializer(many=True, read_only=True)
    class Meta:
        model = models.Route
        fields = ('url', 'id', 'name', 'trunkgroup', 'records')


class NumberSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Number
        fields = ('cc', 'number', 'destination', 'route', 'modified', 'active')
