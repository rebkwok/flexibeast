# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0005_auto_20151102_1432'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='reviewed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='review',
            name='user_display_name',
            field=models.CharField(verbose_name='username that will be displayed on the site', max_length=255),
        ),
    ]
