# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0002_auto_20150830_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='name',
            field=models.CharField(max_length=255, default='name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='block',
            name='individual_booking_date',
            field=models.DateTimeField(verbose_name='Date individual bookings allowed', help_text='Set the date when individual booking will be allowed for classes in this block.  Defaults to the creation date of the block.', default=django.utils.timezone.now),
        ),
    ]
