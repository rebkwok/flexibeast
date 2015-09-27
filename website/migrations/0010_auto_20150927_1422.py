# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0009_auto_20150926_2225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subsection',
            name='index',
            field=models.PositiveIntegerField(null=True, help_text='This controls the order subsections are displayed on the page'),
        ),
    ]
