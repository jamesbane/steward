# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-18 14:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0007_auto_20160715_1911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transmission',
            name='result_state',
            field=models.SmallIntegerField(choices=[(0, 'Pending'), (1, 'Transfering'), (2, 'Success'), (3, 'Failure')]),
        ),
    ]
