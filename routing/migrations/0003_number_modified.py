# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-30 19:45
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0002_auto_20160630_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='number',
            name='modified',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2016, 6, 30, 19, 45, 5, 958692)),
            preserve_default=False,
        ),
    ]
