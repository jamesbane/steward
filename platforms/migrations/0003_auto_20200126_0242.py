# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2020-01-26 02:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platforms', '0002_auto_20181218_2219'),
    ]

    operations = [
        migrations.AddField(
            model_name='broadworksplatform',
            name='hostname',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AddField(
            model_name='broadworksplatform',
            name='ip',
            field=models.CharField(default='', max_length=15),
        ),
    ]
