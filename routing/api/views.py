# Python
from collections import OrderedDict
import requests

# Django
from django.conf import settings

# Third Party
import django_filters
from rest_framework.filters import FilterSet
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

# Application
from routing import models
from routing.api import serializers


class RouteRootView(APIView):

    def get(self, request, format=None):
        context = dict()
        context['numbers'] = reverse('api:routing-number-list', request=request, format=format)
        context['records'] = reverse('api:routing-record-list', request=request, format=format)
        context['routes'] = reverse('api:routing-route-list', request=request, format=format)
        return Response(context)


class RouteViewSet(ModelViewSet):
    queryset = models.Route.objects.all()
    serializer_class = serializers.RouteSerializer


class RecordViewSet(ModelViewSet):
    queryset = models.Record.objects.all()
    serializer_class = serializers.RecordSerializer


class NumberFilter(FilterSet):
    modified_gt = django_filters.IsoDateTimeFilter(name='modified', lookup_type='gt')
    modified_lte = django_filters.IsoDateTimeFilter(name='modified', lookup_type='lte')
    class Meta:
        model = models.Number
        fields = ['cc', 'number', 'route', 'active', 'modified_gt', 'modified_lte']


class NumberListView(ListModelMixin, CreateModelMixin, GenericAPIView):
    queryset = models.Number.objects.all()
    serializer_class = serializers.NumberSerializer
    filter_class = NumberFilter

    def get_queryset(self):
        queryset = super(NumberListView, self).get_queryset()
        q = self.request.query_params.get('q', None)
        if q is not None:
            if q.startswith('^'):
                queryset = queryset.filter(number__startswith=q[1:])
            elif q.endswith('$'):
                queryset = queryset.filter(number__endswith=q[:-1])
            else:
                queryset = queryset.filter(number__contains=q)
        return queryset

    def get(self, request, *args, **kwargs):
        print('get')
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        for item in data:
            item['url'] = '{}://{}{}'.format(request.scheme, request.META.get('HTTP_HOST'), reverse('api:routing-number-detail', args=(item.get('cc'), item.get('number'))))
        return Response(data)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class NumberDetailView(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView):
    serializer_class = serializers.NumberSerializer

    def get_object(self):
        return models.Number.objects.get(cc=self.kwargs['cc'], number=self.kwargs['number'])

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['url'] = '{}://{}{}'.format(request.scheme, request.META.get('HTTP_HOST'), reverse('api:routing-number-detail', args=(instance.cc, instance.number)))
        return Response(data)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
