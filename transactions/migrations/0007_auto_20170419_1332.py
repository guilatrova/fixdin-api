# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-19 16:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0006_auto_20170417_0813'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Balance',
            new_name='PeriodBalance',
        ),
    ]
