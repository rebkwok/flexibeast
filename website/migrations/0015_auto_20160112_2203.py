# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0014_auto_20151031_2305'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subsection',
            name='page',
        ),
        migrations.AddField(
            model_name='page',
            name='content',
            field=models.TextField(default='content', verbose_name='Content'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='SubSection',
        ),
    ]
