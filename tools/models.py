from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField, HStoreField

# Create your models here.
class Process(models.Model):
    STATUS_SCHEDULED = 0
    STATUS_COMPLETED = 1
    STATUS_CANCELED = 2
    STATUS_ERROR = 3
    STATUS_RUNNING = 4
    CHOICES_STATUS = (
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELED, 'Cancled'),
        (STATUS_ERROR, 'Error'),
        (STATUS_RUNNING, 'Running'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='processes', verbose_name=('user'), null=False)
    method = models.CharField(max_length=256, null=False)
    parameters = HStoreField()
    start_timestamp = models.DateTimeField(null=False)
    end_timestamp = models.DateTimeField(null=True)
    content = HStoreField(default={})
    status = models.PositiveSmallIntegerField(null=False, default=STATUS_SCHEDULED, choices=CHOICES_STATUS)
    exception = models.TextField()

    class Meta:
        ordering = ['-start_timestamp', '-end_timestamp']
