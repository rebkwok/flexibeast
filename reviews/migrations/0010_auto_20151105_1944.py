# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0009_auto_20151105_0002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='edited_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='review',
            name='review',
            field=models.TextField(verbose_name='testimonial'),
        ),
        migrations.AlterField(
            model_name='review',
            name='user_display_name',
            field=models.CharField(max_length=255, help_text='If not provided, your first name will be used', verbose_name='username that will be displayed on the site', blank=True),
        ),
    ]
