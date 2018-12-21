# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2018-12-20 21:32
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('routing', '0023_auto_20160819_1526'),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteCallForward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('called_number', models.CharField(max_length=128)),
                ('forward_number', models.CharField(max_length=128)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('called_number',),
            },
        ),
        migrations.CreateModel(
            name='RemoteCallForwardHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('called_number', models.CharField(max_length=128)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(max_length=256)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-modified',),
            },
        ),
        migrations.AlterField(
            model_name='transmission',
            name='type',
            field=models.SmallIntegerField(choices=[(0, 'Route'), (1, 'Fraud Bypass'), (2, 'Outbound Route'), (3, 'Remote Call Forward')]),
        ),
    ]
