# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0004_auto_20151102_1429'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(max_length=40, blank=True, unique=True, populate_from='title', editable=False),
        ),
    ]
