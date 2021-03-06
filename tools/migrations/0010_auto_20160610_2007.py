# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-06-10 20:07
from __future__ import unicode_literals

from django.db import migrations, models
import steward.storage


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0009_auto_20160609_1646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='processcontent',
            name='html',
            field=models.FileField(storage=steward.storage.ProtectedFileStorage(), upload_to='process'),
        ),
        migrations.AlterField(
            model_name='processcontent',
            name='raw',
            field=models.FileField(storage=steward.storage.ProtectedFileStorage(), upload_to='process'),
        ),
    ]
