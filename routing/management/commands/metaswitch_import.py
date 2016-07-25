# Python
import argparse
import csv
import time

# Django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.template import loader
from django.utils import timezone

# Application
from routing.models import Number, NumberHistory, Route

# Third Party
import paramiko
from lib.pyutil.util import Util


class Command(BaseCommand):
    help = 'Upload UDA6 file to MetaSwitch'

    def add_arguments(self, parser):
        parser.add_argument('--truncate', dest='truncate', action='store_true')
        parser.add_argument('uda_file', type=argparse.FileType('r'))

    @transaction.non_atomic_requests
    def handle(self, *args, **options):
        User = get_user_model()
        steward_user,_ = User.objects.get_or_create(username='steward', defaults={first_name:'System', last_name:''})
        trunks = dict()
        for route in Route.objects.all():
            trunks[str(route.trunkgroup)] = route

        if options['truncate']:
            Number.objects.all().delete()
            NumberHistory.objects.all().delete()

        create_count = 0
        update_count = 0
        with open(options['uda_file'].name) as f:
            csv_file = csv.reader(f, delimiter=',')
            for row in csv_file:
                if len(row) >= 2:
                    if row[0].startswith(';') or row[0].startswith(' ') or row[0] == 'DN':
                        continue
                    number = row[0]
                    trunk_number = row[1]
                    if trunk_number in trunks:
                        route = trunks[trunk_number]
                        obj, created = Number.objects.update_or_create(cc=1, number=number, defaults={'route': route})
                        NumberHistory.objects.create(cc=obj.cc, number=obj.number, user=steward_user, action='Imported to {}'.format(obj.route.name))
                        if created:
                            create_count += 1
                            print('Created {} => {}'.format(number, route))
                        else:
                            update_count += 1
                            print('Updated {} => {}'.format(number, route))
        self.stdout.write(self.style.SUCCESS('Successfully imported UDA6 file >> Created: {} Updated: {}'.format(create_count, update_count)))
