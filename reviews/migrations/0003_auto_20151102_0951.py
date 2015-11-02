# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0002_auto_20151102_0907'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='previous_rating',
            field=models.IntegerField(null=True),
        ),
    ]
