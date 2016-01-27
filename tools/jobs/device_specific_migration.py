# Python

# Django
from django.utils import timezone

# Application
from tools.models import Process

# Third Party


def device_specific_migration(process_id):
    print(process_id)
    process = Process.objects.get(id=process_id)
    print(process.method)
    print(process.parameters)
