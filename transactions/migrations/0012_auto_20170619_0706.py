# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-19 10:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0011_auto_20170529_1959'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=70),
        ),
    ]
