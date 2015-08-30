# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0004_auto_20150830_1356'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='block',
        ),
        migrations.AddField(
            model_name='block',
            name='events',
            field=models.ManyToManyField(to='flex_bookings.Event', related_name='blocks'),
        ),
        migrations.AddField(
            model_name='booking',
            name='cost',
            field=models.DecimalField(default=7, max_digits=8, decimal_places=2),
        ),
    ]
