# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0006_auto_20151103_2043'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='previous_user_display_name',
            field=models.CharField(blank=True, null=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='review',
            name='title',
            field=models.CharField(blank=True, null=True, max_length=255, verbose_name=''),
        ),
    ]
