# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-18 21:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0019_outboundroute'),
    ]

    operations = [
        migrations.RenameField(
            model_name='outboundroute',
            old_name='local_route',
            new_name='end_office_route',
        ),
        migrations.AlterField(
            model_name='route',
            name='type',
            field=models.SmallIntegerField(choices=[(0, 'Internal'), (1, 'Outbound')]),
        ),
    ]
