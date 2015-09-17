# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0008_auto_20150912_0813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='individual_booking_date',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='Set the date when individual booking will be allowed for classes in this block.  Defaults to the date the block is created.', verbose_name='Date individual bookings allowed'),
        ),
        migrations.AlterField(
            model_name='block',
            name='item_cost',
            field=models.DecimalField(decimal_places=2, default=6, help_text='The (discounted) cost of each individual class when booked as part of the block', max_digits=8),
        ),
    ]
