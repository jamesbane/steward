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
from routing.models import Number, Route, Transmission

# Third Party
import paramiko
from lib.pyutil.util import Util


class Command(BaseCommand):
    help = 'Upload UDA6 file to MetaSwitch'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=argparse.FileType('w'))

    @transaction.non_atomic_requests
    def handle(self, *args, **options):
        f = options['output_file']
        # generate file
        context = dict()
        context['routes'] = Route.objects.all()
        context['numbers'] = Number.objects.all().select_related('route')
        f.write(str(loader.render_to_string('routing/NVFILE.txt', context)))
        f.close()
        self.stdout.write(self.style.SUCCESS('Successfully exported UDA6 file to {}'.format(f.name)))
