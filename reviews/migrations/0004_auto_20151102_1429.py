# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0003_auto_20151102_0951'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(max_length=40, editable=False, blank=True, populate_from='title'),
        ),
        migrations.AlterField(
            model_name='review',
            name='previous_rating',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
