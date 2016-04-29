from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class EmptyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/empty.html"


class VoipDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/voip.html"
