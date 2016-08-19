# Python
import argparse
import os
import tempfile
import time

# Django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.template import loader
from django.utils import timezone

# Application
from routing.models import FraudBypass, Number, OutboundRoute, Route, Transmission

# Third Party
import paramiko
from lib.pyutil.util import Util


class Command(BaseCommand):
    help = 'Export MetaSwitch to UDA file'

    def add_arguments(self, parser):
        parser.add_argument('--type', dest='type', choices=['fraud-bypass', 'route', 'outbound-route'], required=True)
        parser.add_argument('output_file', type=argparse.FileType('w'))

    def handle(self, *args, **options):
        output_file = options['output_file']
        if options['type'] == 'fraud-bypass':
            self.export_fraud_bypass(output_file)
        elif options['type'] == 'route':
            self.export_route(output_file)
        elif options['type'] == 'outbound-route':
            self.export_outbound_route(output_file)

    @transaction.non_atomic_requests
    def export_fraud_bypass(self, output_file):
        f = output_file
        # generate file
        context = dict()
        context['object_list'] = FraudBypass.objects.all()
        f.write(str(loader.render_to_string('routing/NVFILE_fraud_bypass.txt', context)))
        f.close()
        self.stdout.write(self.style.SUCCESS('Successfully exported Fraud Bypass file to {}'.format(f.name)))

    @transaction.non_atomic_requests
    def export_route(self, output_file):
        f = output_file
        # generate file
        context = dict()
        context['routes'] = Route.objects.filter(type=Route.TYPE_CHOICE_INTERNAL)
        context['numbers'] = Number.objects.all().select_related('route')
        f.write(str(loader.render_to_string('routing/NVFILE_route.txt', context)))
        f.close()
        self.stdout.write(self.style.SUCCESS('Successfully exported Route file to {}'.format(f.name)))

    @transaction.non_atomic_requests
    def export_outbound_route(self, output_file):
        f = output_file
        # generate file
        context = dict()
        context['routes'] = Route.objects.filter(type=Route.TYPE_CHOICE_OUTBOUND)
        context['object_list'] = OutboundRoute.objects.all().select_related('end_office_route', 'long_distance_route')
        f.write(str(loader.render_to_string('routing/NVFILE_outbound_route.txt', context)))
        f.close()
        self.stdout.write(self.style.SUCCESS('Successfully exported Route file to {}'.format(f.name)))
