# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0012_auto_20151003_1705'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subsection',
            options={'ordering': ['index', 'id']},
        ),
        migrations.AlterUniqueTogether(
            name='subsection',
            unique_together=set([]),
        ),
    ]
