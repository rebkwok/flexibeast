# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0006_booking_block'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='payment_open',
        ),
        migrations.AddField(
            model_name='block',
            name='booking_open',
            field=models.BooleanField(help_text='If this box is checked, all classes in the block will be available for booking.  Single class booking will only be available from the date you have selected.  Note that unchecking the box does NOT close booking for individual classes.', default=False),
        ),
        migrations.AlterField(
            model_name='event',
            name='booking_open',
            field=models.BooleanField(help_text='Determines whether this class/workshop is visible on the site and available to book', default=False),
        ),
    ]
