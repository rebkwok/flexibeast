# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('paid', models.BooleanField(help_text='Payment has been made by user', default=False)),
                ('date_booked', models.DateTimeField(default=django.utils.timezone.now)),
                ('payment_confirmed', models.BooleanField(help_text='Payment confirmed by admin/organiser', default=False)),
                ('date_payment_confirmed', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('CANCELLED', 'Cancelled')], default='OPEN', max_length=255)),
                ('attended', models.BooleanField(help_text='Student has attended this event', default=False)),
                ('reminder_sent', models.BooleanField(default=False)),
                ('warning_sent', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='')),
                ('date', models.DateTimeField()),
                ('location', models.CharField(default='Watermelon Studio', max_length=255)),
                ('max_participants', models.PositiveIntegerField(help_text='Leave blank if no max number of participants', blank=True, null=True)),
                ('contact_person', models.CharField(default='Gwen Burns', max_length=255)),
                ('contact_email', models.EmailField(default='thewatermelonstudio@hotmail.com', max_length=254)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=8, default=0)),
                ('advance_payment_required', models.BooleanField(default=True)),
                ('booking_open', models.BooleanField(default=True)),
                ('payment_open', models.BooleanField(default=True)),
                ('payment_info', models.TextField(blank=True)),
                ('payment_due_date', models.DateTimeField(help_text='If this date is set, make sure that it is earlier than the cancellation period.  Booking that are not paid will be automatically cancelled (a warning email will be sent to users first).', blank=True, null=True)),
                ('cancellation_period', models.PositiveIntegerField(default=24)),
                ('email_studio_when_booked', models.BooleanField(default=False)),
                ('slug', django_extensions.db.fields.AutoSlugField(editable=False, populate_from='name', blank=True, unique=True, max_length=40)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='EventType',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('event_type', models.CharField(help_text="This determines whether events of this type are listed on the 'Classes' or 'Events' page", choices=[('CL', 'Class'), ('EV', 'Event')], max_length=2)),
                ('subtype', models.CharField(help_text='Type of class/event. Use this to categorise events/classes.  If an event can be block booked, this should match the event type used in the Block Type.', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='WaitingListUser',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('event', models.ForeignKey(related_name='waitinglistusers', to='flex_bookings.Event')),
                ('user', models.ForeignKey(related_name='waitinglists', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='eventtype',
            unique_together=set([('event_type', 'subtype')]),
        ),
        migrations.AddField(
            model_name='event',
            name='event_type',
            field=models.ForeignKey(to='flex_bookings.EventType'),
        ),
        migrations.AddField(
            model_name='booking',
            name='event',
            field=models.ForeignKey(related_name='bookings', to='flex_bookings.Event'),
        ),
        migrations.AddField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(related_name='bookings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='booking',
            unique_together=set([('user', 'event')]),
        ),
    ]
