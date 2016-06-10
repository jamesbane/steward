# Python
import csv
import importlib

# Django
from django.utils import timezone
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# Application
import tools.forms
from tools.models import Process

# Third Party
import rq
import django_rq
from redis import Redis
from lib.pyutil.django.mixins import ProcessFormMixin


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'tools/index.html'


class ProcessListView(LoginRequiredMixin, ListView):
    model = Process

    def get_queryset(self):
        queryset = super(ProcessListView, self).get_queryset()
        # filter based upon permissions
        permissions = []
        for permission in ['tools.{}'.format(x) for x,y in Process._meta.permissions]:
            if self.request.user.has_perm(permission):
                permissions.append(permission)
        queryset = queryset.filter(view_permission__in=permissions)
        # defer content
        queryset = queryset.defer("content")
        return queryset


class ProcessDetailView(LoginRequiredMixin, DetailView):
    model = Process

    def get_context_data(self, **kwargs):
        context = super(ProcessDetailView, self).get_context_data(**kwargs)
        if not self.request.user.has_perm(context['object'].view_permission):
            raise PermissionDenied
        return context

class ToolView(ProcessFormMixin, TemplateView):

    def form_valid(self, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        self.object = Process.objects.create(user=self.request.user,
                                             method=self.process_name,
                                             parameters=form.cleaned_data,
                                             start_timestamp=timezone.now(),
                                             end_timestamp=None,
                                             view_permission=self.permission_view)
        module = '.'.join(self.process_function.split('.')[:-1])
        method = self.process_function.split('.')[-1]
        importlib.import_module(module)
        process_function = eval(self.process_function)
        q = rq.Queue('tool', connection=Redis(), default_timeout=10800)
        q.enqueue_call(process_function, args=(self.object.pk,))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.success_url:
            # Forcing possible reverse_lazy evaluation
            url = force_text(self.success_url)
        else:
            url = reverse('tools:process-detail', args=(self.object.pk,))
        return url


class CallParkPickupConfiguratorToolView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_call_park_pickup_configurator_exec'
    permission_view = 'tools.process_call_park_pickup_configurator_view'
    process_name = 'Call Park/Pickup Configurator'
    process_function = 'tools.jobs.call_park_pickup_configurator.call_park_pickup_configurator'
    template_name = 'tools/call_park_pickup_configurator.html'
    form_class = tools.forms.TypedProviderGroupForm


class DeviceSpecificMigrationToolView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_device_specific_migration_exec'
    permission_view = 'tools.process_device_specific_migration_view'
    process_name = 'Device Specific Migration'
    process_function = 'tools.jobs.device_specific_migration.device_specific_migration'
    template_name = 'tools/device_specific_migration_tool.html'
    form_class = tools.forms.TypedProviderGroupForm


class FirmwareReportView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_firmware_report_exec'
    permission_view = 'tools.process_firmware_report_view'
    process_name = 'Firmware Report'
    process_function = 'tools.jobs.firmware_report.firmware_report'
    template_name = 'tools/firmware_report.html'
    form_class = tools.forms.ProviderGroupForm


class FraudComplianceResetToolView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_fraud_compliance_reset_exec'
    permission_view = 'tools.process_fraud_compliance_reset_view'
    process_name = 'Fraud Compliance Reset'
    process_function = 'tools.jobs.fraud_compliance_reset.fraud_compliance_reset'
    template_name = 'tools/fraud_compliance_reset_tool.html'
    form_class = tools.forms.TypedProviderGroupForm


class LabResetToolView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_lab_rebuild_exec'
    permission_view = 'tools.process_lab_rebuild_view'
    process_name = 'Lab Rebuild'
    process_function = 'tools.jobs.lab_rebuild.lab_rebuild'
    template_name = 'tools/lab_rebuild.html'
    form_class = tools.forms.EmptyForm


class PushToTalkConfiguratorToolView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_ptt_configurator_exec'
    permission_view = 'tools.process_ptt_configurator_view'
    process_name = 'Push To Talk Configurator'
    process_function = 'tools.jobs.ptt_configurator.ptt_configurator'
    template_name = 'tools/ptt_configurator.html'
    form_class = tools.forms.TypedProviderGroupForm


class RegistrationByTypeReportView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_registration_by_type_exec'
    permission_view = 'tools.process_registration_by_type_view'
    process_name = 'Registration By Type Report'
    process_function = 'tools.jobs.registration_by_type.registration_by_type'
    template_name = 'tools/registration_by_type.html'
    form_class = tools.forms.EmptyForm


class RegistrationReportView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_registration_report_exec'
    permission_view = 'tools.process_registration_report_view'
    process_name = 'Registration Report'
    process_function = 'tools.jobs.registration_report.registration_report'
    template_name = 'tools/registration_report.html'
    form_class = tools.forms.ProviderGroupForm


class TagReportView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_tag_report_exec'
    permission_view = 'tools.process_tag_report_view'
    process_name = 'Tag Report'
    process_function = 'tools.jobs.tag_report.tag_report'
    template_name = 'tools/tag_report.html'
    form_class = tools.forms.TagReportForm


class TagRemovalToolView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_tag_removal_exec'
    permission_view = 'tools.process_tag_removal_view'
    process_name = 'Tag Removal'
    process_function = 'tools.jobs.tag_removal.tag_removal'
    template_name = 'tools/tag_removal_tool.html'
    form_class = tools.forms.TagRemovalForm
