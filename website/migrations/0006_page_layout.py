# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_auto_20150912_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='layout',
            field=models.CharField(max_length=15, choices=[('no-img', 'No images'), ('1-img-top', 'One image, centred, top of page'), ('1-img-left', 'One image, left of page text'), ('1-img-right', 'One image, right of page text'), ('img-col-left', 'Multiple small images, left of page text'), ('img-col-right', 'Multiple small images, right of page text')], default='no-img'),
        ),
    ]
