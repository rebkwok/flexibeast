# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0008_auto_20151104_1221'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='user_display_name',
            field=models.CharField(max_length=255, verbose_name='username that will be displayed on the site', blank=True),
        ),
    ]
