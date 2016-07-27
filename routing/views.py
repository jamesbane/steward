# Django
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView,
)

# Application
from routing.models import Number, NumberHistory, Record, Route, Transmission

class NVFileView(LoginRequiredMixin, TemplateView):
    template_name = 'routing/NVFILE.txt'

    def get_context_data(self, **kwargs):
        context = super(UDA6View, self).get_context_data(**kwargs)
        context['routes'] = Route.objects.all()
        context['numbers'] = Number.objects.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super(UDA6View, self).render_to_response( context, **response_kwargs)
        response['Content-Type'] = 'text/text'
        return response


class TransmissionListView(LoginRequiredMixin, ListView):
    model = Transmission
    paginate_by = 100


class TransmissionDetailView(LoginRequiredMixin, DetailView):
    model = Transmission


class NumberCreateView(LoginRequiredMixin, CreateView):
    model = Number


class NumberDeleteView(LoginRequiredMixin, DeleteView):
    model = Number


class NumberDetailView(LoginRequiredMixin, DetailView):
    model = Number


class NumberUpdateView(LoginRequiredMixin, UpdateView):
    model = Number


class NumberSearchView(LoginRequiredMixin, TemplateView):
    template_name = 'routing/number_search.html'

    def get_context_data(self, **kwargs):
        context = super(NumberSearchView, self).get_context_data(**kwargs)
        context['number_count'] = Number.objects.filter(active=True).count()
        return context


class NumberDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'routing/number_detail.html'

    def get_object(self):
        try:
            return Number.objects.get(cc=self.kwargs.get('cc'), number=self.kwargs.get('number'))
        except Number.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super(NumberDetailView, self).get_context_data(**kwargs)
        context['object'] = self.get_object()
        context['cc'] = self.kwargs.get('cc')
        context['number'] = self.kwargs.get('number')
        context['history_list'] = NumberHistory.objects.filter(cc=self.kwargs.get('cc'), number=self.kwargs.get('number'))
        return context


class NumberHistoryListView(LoginRequiredMixin, ListView):
    model = NumberHistory
    paginate_by = 100


class RecordCreateView(LoginRequiredMixin, CreateView):
    model = Record


class RecordDeleteView(LoginRequiredMixin, DeleteView):
    model = Record


class RecordDetailView(LoginRequiredMixin, DetailView):
    model = Record


class RecordListView(LoginRequiredMixin, ListView):
    model = Record


class RecordUpdateView(LoginRequiredMixin, UpdateView):
    model = Record


class RouteCreateView(LoginRequiredMixin, CreateView):
    model = Route
    fields = ('name', 'trunkgroup',)

    def get_success_url(self):
        return reverse('routing:route-detail', args=(self.object.id,))


class RouteDeleteView(LoginRequiredMixin, DeleteView):
    model = Route
    success_url = reverse_lazy('routing:route-list')


class RouteDetailView(LoginRequiredMixin, DetailView):
    model = Route


class RouteListView(LoginRequiredMixin, ListView):
    model = Route


class RouteUpdateView(LoginRequiredMixin, UpdateView):
    model = Route
    fields = ('name',)

    def get_success_url(self):
        return reverse('routing:route-detail', args=(self.object.id,))
