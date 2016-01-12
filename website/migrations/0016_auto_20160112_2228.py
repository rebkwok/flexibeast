# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0015_auto_20160112_2203'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'permissions': (('can_view_restricted', 'Can view restricted pages'),)},
        ),
        migrations.AddField(
            model_name='page',
            name='restricted',
            field=models.BooleanField(help_text='Page only visible if user is logged in and has been given permission', default=False),
        ),
    ]
