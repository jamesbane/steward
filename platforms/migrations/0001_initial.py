# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-12-18 19:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BroadworksPlatform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True)),
                ('uri', models.CharField(max_length=1024)),
                ('username', models.CharField(max_length=256)),
                ('password', models.CharField(max_length=256)),
            ],
            options={
                'ordering': ('name', 'uri'),
            },
        ),
    ]
