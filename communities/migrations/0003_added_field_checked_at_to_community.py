# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-01 14:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0002_auto_20180322_0206'),
    ]

    operations = [
        migrations.AddField(
            model_name='community',
            name='checked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
