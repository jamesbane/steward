# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-28 18:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0013_numberhistory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='numberhistory',
            options={'ordering': ('-modified',)},
        ),
    ]
