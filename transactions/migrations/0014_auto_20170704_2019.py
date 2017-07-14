# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-04 23:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('transactions', '0013_transaction_payment_date'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='category',
            unique_together=set([('user', 'name', 'kind')]),
        ),
    ]