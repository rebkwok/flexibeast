# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0011_auto_20150927_1433'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='menu_location',
            field=models.CharField(default='dropdown', max_length=8, choices=[('main', 'Separate link in main menu'), ('dropdown', 'Displayed under "More" dropdown menu')], help_text='Choose where to display the menu link.  Note that all options appear under the "More" dropdown at small screen sizes. Note that too many main menu links will cause the menu bar to become double normal height.'),
        ),
    ]
