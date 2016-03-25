# Python
import csv
import importlib

# Django
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse

# Application
import tools.forms
from tools.models import Process

# Third Party
import rq
from redis import Redis
import django_rq

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"


class ProcessListView(LoginRequiredMixin, ListView):
    model = Process


class ProcessDetailView(LoginRequiredMixin, DetailView):
    model = Process

    def get_context_data(self, **kwargs):
        context = super(ProcessDetailView, self).get_context_data(**kwargs)
        context['files'] = dict()
        for key,value in context['object'].content.items():
            extension = key.split('.')[-1]
            if extension == 'csv':
                content = csv.reader(value.splitlines())
                print(content)
            else:
                content = value
            context['files'][key] = {
                'filename': key,
                'content': content,
                'extension': extension,
            }
        return context

class ToolView(TemplateView):
    form_class = None
    initial = {}
    prefix = None
    success_url = None

    def get_form(self, form_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_form_class(self):
        """
        Returns the form class to use in this view
        """
        return self.form_class

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        return self.initial.copy()

    def get_prefix(self):
        """
        Returns the prefix to use for forms on this view
        """
        return self.prefix

    def get_context_data(self, **kwargs):
        """
        Insert the form into the context dict.
        """
        kwargs.setdefault('form', self.get_form())
        return super(ToolView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        self.object = Process.objects.create(user=self.request.user,
                                             method=self.process_name,
                                             parameters=form.cleaned_data,
                                             start_timestamp=timezone.now(),
                                             end_timestamp=None)
        module = '.'.join(self.process_function.split('.')[:-1])
        method = self.process_function.split('.')[-1]
        importlib.import_module(module)
        process_function = eval(self.process_function)
        # django_rq.enqueue(process_function, process_id=self.object.pk, timeout=0)
        q = rq.Queue('default', connection=Redis(), default_timeout=10800)
        q.enqueue_call(process_function, args=(self.object.pk,))
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        """
        Returns the supplied success URL.
        """
        if self.success_url:
            # Forcing possible reverse_lazy evaluation
            url = force_text(self.success_url)
        else:
            url = reverse('process-detail', args=(self.object.pk,))
        return url


class ReportView(TemplateView):
    pass


class DeviceSpecificMigrationToolView(LoginRequiredMixin, ToolView):
    process_name = 'Device Specific Migration'
    process_function = 'tools.jobs.device_specific_migration.device_specific_migration'
    template_name = 'tools/device_specific_migration_tool.html'
    form_class = tools.forms.TypedProviderGroupForm


class FraudComplianceResetToolView(LoginRequiredMixin, ToolView):
    process_name = 'Fraud Compliance Reset'
    process_function = 'tools.jobs.fraud_compliance_reset.fraud_compliance_reset'
    template_name = 'tools/fraud_compliance_reset_tool.html'
    form_class = tools.forms.TypedProviderGroupForm


class LabResetToolView(LoginRequiredMixin, ToolView):
    process_name = 'Lab Rebuild'
    process_function = 'tools.jobs.lab_rebuild.lab_rebuild'
    template_name = 'tools/lab_rebuild.html'
    form_class = tools.forms.LabRebuildForm


class FirmwareReportView(LoginRequiredMixin, ToolView):
    process_name = 'Firmware Report'
    process_function = 'tools.jobs.firmware_report.firmware_report'
    template_name = 'tools/firmware_report.html'
    form_class = tools.forms.ProviderGroupForm

class RegistrationByTypeReportView(LoginRequiredMixin, ToolView):
    process_name = 'Registration By Type Report'
    process_function = 'tools.jobs.registration_by_type.registration_by_type'
    template_name = 'tools/registration_by_type.html'
    form_class = tools.forms.EmptyForm
