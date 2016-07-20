# Python
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

    @transaction.non_atomic_requests
    def handle(self, *args, **options):
        try:
            last_transmission = Transmission.objects.filter(result_state=Transmission.RESULT_CHOICE_SUCCESS).latest('last_modified')
        except Transmission.DoesNotExist:
            last_transmission = None
        try:
            last_modified = Number.objects.latest('modified').modified
        except Number.DoesNotExist:
            last_modified = None
        if last_transmission and last_modified and last_transmission.last_modified >= last_modified:
            self.stdout.write(self.style.SUCCESS('No modifications since last transmission'))
            return
        transmission = Transmission.objects.create(result_state=Transmission.RESULT_CHOICE_PENDING)
        meta_settings = settings.PLATFORMS['metaswitch']

        # generate file
        context = dict()
        context['routes'] = Route.objects.all()
        context['numbers'] = Number.objects.all().select_related('route')
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(loader.render_to_string('routing/NVFILE.txt', context).encode())
        f.close()
        file_hash = Util.md5(f.name)

        # transfer file
        try:
            transmission.result_state = Transmission.RESULT_CHOICE_TRANSFERING
            transmission.checksum = file_hash
            transmission.last_modified = last_modified
            transmission.save(update_fields=['result_state', 'checksum', 'last_modified'])
            transport = paramiko.Transport((meta_settings['host'], meta_settings['port']))
            transport.connect(username=meta_settings['username'], password=meta_settings['password'])
            sftp = paramiko.sftp_client.SFTPClient.from_transport(transport)
            sftp.chdir(path=meta_settings['pathname'])
            sftp.put(f.name, meta_settings['filename'])
            os.remove(f.name)
            del(f)

            file_list = sftp.listdir()
            while meta_settings['filename'] in file_list:
                time.sleep(5)
                file_list = sftp.listdir()

            ok_filename = '{}@ok'.format(meta_settings['filename'])
            error_filename = '{}@error'.format(meta_settings['filename'])
            while ok_filename not in file_list and error_filename not in file_list:
                time.sleep(5)
                file_list = sftp.listdir()

            if ok_filename in file_list:
                # retreive ok file
                transmission.result_state = Transmission.RESULT_CHOICE_SUCCESS
                transmission.result_timestamp = timezone.now()
                f = tempfile.NamedTemporaryFile(delete=False)
                f.close()
                sftp.get(ok_filename, f.name)
                with open(f.name) as r:
                    content = r.read()
                    transmission.result_data = content
                transmission.save()
                os.remove(f.name)
                del(f)
                self.stdout.write(self.style.SUCCESS('Successfully transfered UDA6 file'))
            elif error_filename in file_list:
                # retrieve error file
                transmission.result_state = Transmission.RESULT_CHOICE_FAILURE
                transmission.result_timestamp = timezone.now()
                f = tempfile.NamedTemporaryFile(delete=False)
                f.close()
                sftp.get(ok_filename, f.name)
                with open(f.name) as r:
                    content = r.read()
                    transmission.result_data = content
                transmission.save()
                os.remove(f.name)
                del(f)
                self.stdout.write(self.style.ERROR('Failed to transfer UDA6 file'))
        except Exception as e:
            transmission.result_state = Transmission.RESULT_CHOICE_FAILURE
            transmission.result_timestamp = timezone.now()
            transmission.result_data = str(e)
            transmission.save()
