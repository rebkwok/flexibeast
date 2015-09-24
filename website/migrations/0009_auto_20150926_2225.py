# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0008_auto_20150915_0909'),
    ]

    operations = [
        migrations.AddField(
            model_name='picture',
            name='main',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='picture',
            name='image',
            field=models.ImageField(upload_to='website_pages', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subsection',
            name='index',
            field=models.PositiveIntegerField(help_text='This controls the order subsections are displayed on the page'),
        ),
    ]
