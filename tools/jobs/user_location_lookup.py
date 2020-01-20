# Python
import io
import os
import requests

# Django
from django.utils import timezone
from django.conf import settings

# Application
from tools.models import Process, ProcessContent

class UserLocationLookup():
    def __init__(self, process):
        self._process = process

    def run(self):
        log = io.StringIO()
        summary = io.StringIO()

        # parameters
        url = self._process.parameters.get('url', None)
        line_port = self._process.parameters.get('line_port', None)
        dn = self._process.parameters.get('dn', None)
        group_id = self._process.parameters.get('group_id', None)

        print(url)
        print(line_port)
        print(dn)
        print(group_id)

        return None


def loc_lookup(process_id):
    process = Process.objects.get(id=process_id)

    # Summary Tab
    summary_content = ProcessContent.objects.create(process=process, tab='Summary', priority=1)
    dir_path = os.path.join(settings.PROJECTED_ROOT, 'process')
    filename_html = '{}_{}'.format(process.id, 'summary.html')
    pathname_html = os.path.join(dir_path, filename_html)
    filename_raw = '{}_{}'.format(process.id, 'summary.csv')
    pathname_raw = os.path.join(dir_path, filename_raw)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    summary_html = open(pathname_html, "w")
    summary_content.html.name = os.path.join('process', filename_html)
    summary_raw = open(pathname_raw, "w")
    summary_content.raw.name = os.path.join('process', filename_raw)
    summary_content.save()

    # Log Tab
    lookup = UserLocationLookup(process)
    data = lookup.run()


