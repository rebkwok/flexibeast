# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flex_bookings', '0007_auto_20150831_1057'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['date']},
        ),
        migrations.AlterField(
            model_name='booking',
            name='block',
            field=models.ForeignKey(related_name='bookings', to='flex_bookings.Block', blank=True, null=True),
        ),
    ]
