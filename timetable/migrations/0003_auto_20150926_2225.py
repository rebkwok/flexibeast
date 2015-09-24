# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0002_auto_20150915_0909'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='contact_email',
            field=models.EmailField(default='flexibeast@hotmail.com', max_length=254),
        ),
        migrations.AlterField(
            model_name='session',
            name='contact_person',
            field=models.CharField(default='Alicia Alexandra', max_length=255),
        ),
    ]
