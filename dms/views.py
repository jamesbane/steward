# Django
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView

# Application
from deploy.models import Device


class PolycomDefaultView(TemplateView):
    content_type = 'application/xml'
    template_name = 'dms/polycom/000000000000.cfg'


class PolycomResyncView(TemplateView):
    content_type = 'application/xml'
    template_name = 'dms/polycom/resync.cfg'


class PolycomView(DetailView):
    content_type = 'application/xml'
    template_name = 'dms/polycom/%mac%-phone.cfg'
    model = Device
    slug_field = 'serial__iexact'
