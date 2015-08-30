# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0005_auto_20150830_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='block',
            field=models.ForeignKey(to='flex_bookings.Block', null=True, related_name='bookings'),
        ),
    ]
