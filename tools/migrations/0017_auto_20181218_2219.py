# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-12-18 22:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0016_auto_20160803_1844'),
    ]

    operations = [
        migrations.AddField(
            model_name='process',
            name='platform_id',
            field=models.IntegerField(default=-1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='process',
            name='platform_type',
            field=models.SmallIntegerField(default=-1),
            preserve_default=False,
        ),
    ]