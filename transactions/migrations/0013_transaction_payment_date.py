# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-29 22:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0012_auto_20170619_0706'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='payment_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]