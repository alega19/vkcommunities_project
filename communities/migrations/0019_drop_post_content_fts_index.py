# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-24 06:57
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0018_post_content_fts_index_v2'),
    ]

    operations = [
        migrations.RunSQL('''DROP INDEX "communities_post_content_fts_index";''')
    ]
