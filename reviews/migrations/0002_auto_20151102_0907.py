# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='user',
            field=models.ForeignKey(verbose_name='author', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='review',
            name='user_display_name',
            field=models.CharField(verbose_name='display name', max_length=255),
        ),
    ]
