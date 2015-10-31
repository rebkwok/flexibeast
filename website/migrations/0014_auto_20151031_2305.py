# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import imagekit.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0013_auto_20151031_2125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='picture',
            name='image',
            field=imagekit.models.fields.ProcessedImageField(upload_to='website_pages', blank=True, null=True),
        ),
    ]
