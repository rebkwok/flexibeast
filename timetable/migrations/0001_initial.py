# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('day', models.CharField(choices=[('01MON', 'Monday'), ('02TUE', 'Tuesday'), ('03WED', 'Wednesday'), ('04THU', 'Thursday'), ('05FRI', 'Friday'), ('06SAT', 'Saturday'), ('07SUN', 'Sunday')], max_length=5)),
                ('time', models.TimeField()),
                ('description', models.TextField(blank=True, default='')),
                ('location', models.CharField(default='Watermelon Studio', max_length=255)),
                ('max_participants', models.PositiveIntegerField(help_text='Leave blank if no max number of participants', blank=True, default=10, null=True)),
                ('contact_person', models.CharField(default='Gwen Burns', max_length=255)),
                ('contact_email', models.EmailField(default='thewatermelonstudio@hotmail.com', max_length=254)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=8, default=7.0)),
                ('booking_open', models.BooleanField(default=True)),
                ('payment_open', models.BooleanField(default=True)),
                ('advance_payment_required', models.BooleanField(default=True)),
                ('payment_info', models.TextField(blank=True)),
                ('cancellation_period', models.PositiveIntegerField(default=24)),
                ('external_instructor', models.BooleanField(default=False)),
                ('email_studio_when_booked', models.BooleanField(default=False)),
                ('event_type', models.ForeignKey(to='flex_bookings.EventType', null=True)),
            ],
        ),
    ]
