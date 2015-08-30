# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0003_auto_20150830_1237'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='block_cost',
        ),
        migrations.AddField(
            model_name='block',
            name='item_cost',
            field=models.DecimalField(decimal_places=2, default=6, max_digits=8),
        ),
    ]
