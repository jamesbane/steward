# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-28 18:45
from __future__ import unicode_literals

from django.db import migrations


def data_migrate_parameters(apps, schema_editor):
    Process = apps.get_model("tools", "Process")
    for process in Process.objects.all():
        process.parameters2 = process.parameters
        process.save()

class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0013_add_parameters2'),
    ]

    operations = [
        migrations.RunPython(data_migrate_parameters),
    ]
