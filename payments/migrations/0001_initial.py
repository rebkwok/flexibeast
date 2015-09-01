# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0007_auto_20150831_1057'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaypalBlockTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('invoice_id', models.CharField(null=True, blank=True, unique=True, max_length=255)),
                ('transaction_id', models.CharField(null=True, blank=True, unique=True, max_length=255)),
                ('block', models.ForeignKey(null=True, to='flex_bookings.Block')),
            ],
        ),
        migrations.CreateModel(
            name='PaypalBookingTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('invoice_id', models.CharField(null=True, blank=True, unique=True, max_length=255)),
                ('transaction_id', models.CharField(null=True, blank=True, unique=True, max_length=255)),
                ('booking', models.ForeignKey(null=True, to='flex_bookings.Booking')),
            ],
        ),
    ]
