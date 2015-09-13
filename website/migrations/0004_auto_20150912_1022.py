# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_auto_20150912_0813'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AboutInfo',
        ),
        migrations.DeleteModel(
            name='PrivateInfo',
        ),
        migrations.AlterModelOptions(
            name='subsection',
            options={'ordering': ['index']},
        ),
        migrations.AddField(
            model_name='page',
            name='menu_name',
            field=models.CharField(default='', max_length=255, help_text='The heading to include in the top menu bar'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='page',
            name='name',
            field=models.CharField(max_length=255, unique=True, help_text='A unique identifier for this page. Use lowercase, no spaces.'),
        ),
    ]
