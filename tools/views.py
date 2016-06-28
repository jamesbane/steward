# Python
from collections import OrderedDict
import csv
import requests
import importlib

# Django
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms import formset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

# Application
import tools.forms
from tools.models import Process
from tools.serializers import ProcessSerializer

# Third Party
import django_rq
from lib.pybw.broadworks import BroadWorks, Nil
from lib.pypalladion.palladion import Palladion
from lib.pyutil.django.mixins import ProcessFormMixin
from redis import Redis
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
import rq


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


class ProcessDetailAPIViewSet(ModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer


class RegistrationAPIViewSet(ViewSet):
    lookup_value_regex = '[^/]+'       #Just add this line & change your Regex if needed
    permission_classes = [IsAdminUser]

    def list(self, request, format=None):
        return Response()

    def retrieve(self, request, pk, format=None):
        user_id = pk
        public_device_ids = [12,24,25,31,37,40,41,44]
        requests.packages.urllib3.disable_warnings()
        palladion = Palladion(**settings.PLATFORMS['palladion'])
        pl_devices = { x['id']: x for x in palladion.devices() }
        bw = BroadWorks(**settings.PLATFORMS['broadworks'])
        bw.LoginRequest14sp4()

        if '@' in user_id:
            line_port = user_id
            user_line_id = line_port.split('@')[0]
            regs = sorted([reg for reg in palladion.registrations(user_line_id) if reg['dev_id'] in public_device_ids], key=lambda reg: reg['dev_id'])
            registrations = list()
            for reg in regs:
                registration = dict()
                if 'dev_id' in reg:
                    if reg['dev_id'] in pl_devices:
                        registration['device'] = pl_devices[reg['dev_id']]['name']
                    else:
                        registration['device'] = 'Unknown'
                if 'expires' in reg:
                    registration['expires'] = reg['expires']
                if 'expires_in' in reg:
                    registration['expires_in'] = reg['expires_in']
                if 'first_seen_ts' in reg:
                    registration['first_seen'] = reg['first_seen_ts']
                if 'last_seen_ts' in reg:
                    registration['last_seen'] = reg['last_seen_ts']
                if 'last_refreshed_ts' in reg:
                    registration['last_refreshed'] = reg['last_refreshed_ts']
                if 'srcip' in reg:
                    registration['ip_address'] = reg['srcip']
                if 'usrdev' in reg:
                    registration['user_agent'] = reg['usrdev']
                registrations.append(registration)
            if len(registrations) > 0:
                status = "Registered"
            else:
                status = "Not registered"
            rval = Response({
                "status": status,
                "registrations": registrations,
                "line_port": line_port,
            })
        else:
            user_id = None
            user_detail = None
            # Retrieve User by User Id
            resp1 = bw.UserGetRequest19(pk)
            if resp1['type'] != 'c:ErrorResponse':
                user_detail = resp1['data']
                user_id = pk
            if not user_id:
                # Retrieve User by DN
                resp2 = bw.UserGetListInSystemRequest(searchCriteriaDn=OrderedDict([('mode', 'Contains'), ('value', pk), ('isCaseInsensitive', True)]))
                if resp2['type'] != 'c:ErrorResponse' and 'userTable' in resp2['data'] and len(resp2['data']['userTable']) == 1:
                    user = resp2['data']['userTable'][0]
                    user_id = user['User Id']
            if not user_id:
                # No user could be found :-(
                rval = Response({"status": "User Id not found"})
                bw.LogoutRequest()
                return rval
            else:
                if not user_detail:
                    resp3 = bw.UserGetRequest19(user_id)
                    if resp3['type'] != 'c:ErrorResponse':
                        user_detail = resp3['data']
                    else:
                        rval = Response({"status": "User Id lookup error"})
                        bw.LogoutRequest()
                        return rval
                if 'accessDeviceEndpoint' in user_detail:
                    line_port = user_detail['accessDeviceEndpoint']['linePort']
                    user_line_id = line_port.split('@')[0]
                    regs = sorted([reg for reg in palladion.registrations('polycom_2_VVX600') if reg['dev_id'] in public_device_ids], key=lambda reg: reg['dev_id'])
                    registrations = list()
                    for reg in regs:
                        registration = dict()
                        if 'dev_id' in reg:
                            if reg['dev_id'] in pl_devices:
                                registration['device'] = pl_devices[reg['dev_id']]['name']
                            else:
                                registration['device'] = 'Unknown'
                        if 'expires' in reg:
                            registration['expires'] = reg['expires']
                        if 'expires_in' in reg:
                            registration['expires_in'] = reg['expires_in']
                        if 'first_seen_ts' in reg:
                            registration['first_seen'] = reg['first_seen_ts']
                        if 'last_seen_ts' in reg:
                            registration['last_seen'] = reg['last_seen_ts']
                        if 'last_refreshed_ts' in reg:
                            registration['last_refreshed'] = reg['last_refreshed_ts']
                        if 'srcip' in reg:
                            registration['ip_address'] = reg['srcip']
                        if 'usrdev' in reg:
                            registration['user_agent'] = reg['usrdev']
                        registrations.append(registration)
                    if len(registrations) > 0:
                        status = "Registered"
                    else:
                        status = "Not registered"
                    rval = Response({
                        "broadworks": {
                            "provider_id": user_detail['serviceProviderId'],
                            "group_id": user_detail['groupId'],
                            "user_id": user_id,
                            "first_name": user_detail['firstName'],
                            "last_name": user_detail['lastName']
                        },
                        "status": status,
                        "registrations": registrations,
                        "line_port": line_port,
                    })
                else:
                    rval = Response({"status": "Not found"})
        bw.LogoutRequest()
        return rval


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
    form_class = tools.forms.CallParkPickupForm


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


class TrunkAuditToolView(PermissionRequiredMixin, LoginRequiredMixin, ToolView):
    permission_required = 'tools.process_trunk_user_audit_exec'
    permission_view = 'tools.process_trunk_user_audit_view'
    process_name = 'Trunk User Audit'
    process_function = 'tools.jobs.trunk_user_audit.trunk_user_audit'
    template_name = 'tools/trunk_user_audit.html'
    form_class = tools.forms.TrunkUserAuditForm
