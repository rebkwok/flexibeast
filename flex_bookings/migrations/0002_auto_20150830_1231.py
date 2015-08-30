# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='individual_booking_date',
            field=models.DateTimeField(verbose_name='Date individual bookings allows', default=django.utils.timezone.now, help_text='Set the date when individual booking will be allowed for classes in this block.  Defaults to the creation date of the block.'),
        ),
        migrations.AddField(
            model_name='event',
            name='block',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, null=True, related_name='events', to='flex_bookings.Block'),
        ),
        migrations.AddField(
            model_name='event',
            name='block_cost',
            field=models.DecimalField(decimal_places=2, default=6, max_digits=8),
        ),
        migrations.AlterField(
            model_name='event',
            name='contact_email',
            field=models.EmailField(default='flexibeast@hotmail.com', max_length=254),
        ),
        migrations.AlterField(
            model_name='event',
            name='contact_person',
            field=models.CharField(default='Alicia Alexandra', max_length=255),
        ),
        migrations.AlterField(
            model_name='event',
            name='cost',
            field=models.DecimalField(decimal_places=2, default=7, max_digits=8),
        ),
    ]
