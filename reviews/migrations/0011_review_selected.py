# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-03-27 22:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0010_auto_20151105_1944'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='selected',
            field=models.BooleanField(default=False, help_text='Selected for display on home page'),
        ),
    ]
