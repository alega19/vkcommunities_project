# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-03-21 16:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VkAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=16, null=True, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ('password', models.TextField()),
                ('api_token', models.CharField(blank=True, max_length=85, null=True, unique=True)),
                ('enabled', models.BooleanField(default=True)),
                ('note', models.TextField(blank=True)),
            ],
        ),
    ]
