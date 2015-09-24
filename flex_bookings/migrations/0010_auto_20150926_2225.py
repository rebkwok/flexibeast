# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0009_auto_20150917_1904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='max_participants',
            field=models.PositiveIntegerField(default=9, null=True, help_text='Leave blank if no max number of participants', blank=True),
        ),
    ]
