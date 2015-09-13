# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0006_page_layout'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='menu_location',
            field=models.CharField(choices=[('main', 'Separate link in main menu'), ('dropdown', 'Displayed under "More" dropdown menu')], max_length=8, help_text='Choose where to display the menu link.  Note that all options appear under the "More" dropdown at small screen sizes', default='dropdown'),
        ),
        migrations.AlterField(
            model_name='page',
            name='layout',
            field=models.CharField(choices=[('no-img', 'No images'), ('1-img-top', 'One image, centred, top of page'), ('1-img-left', 'One image, left of text'), ('1-img-right', 'One image, right of text'), ('img-col-left', 'Multiple small images in column, left of text'), ('img-col-right', 'Multiple small images in column, right of text')], max_length=15, help_text='It is recommended to use landscape-oriented pictures for a single, top of page image; portrait-oriented pictures without too much detail for column layout', default='no-img'),
        ),
        migrations.AlterField(
            model_name='page',
            name='menu_name',
            field=models.CharField(max_length=255, null=True, blank=True, help_text='The heading to include in the top menu bar; if left blank, will not be shown as a menu option.'),
        ),
    ]
