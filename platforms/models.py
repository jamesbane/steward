from django.db import models


class BroadworksPlatform(models.Model):
    name = models.CharField(max_length=32, unique=True)
    uri = models.CharField(max_length=1024)
    username = models.CharField(max_length=256)
    password = models.CharField(max_length=256)
    ip = models.CharField(max_length=15, default='', blank=True)
    hostname = models.CharField(max_length=256, default='', blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
