# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-16 19:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0024_account_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='avatar',
            field=models.ImageField(blank=True, upload_to='avatars-accounts'),
        ),
    ]
