# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-03-29 08:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0019_auto_20160129_1153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='layout',
            field=models.CharField(choices=[('no-img', 'No images'), ('1-img-top', 'One image, centred, top of page'), ('1-img-left', 'One image, left of text'), ('1-img-right', 'One image, right of text')], default='no-img', help_text="It is recommended to use landscape-oriented pictures for a single, top of page image.  If no image is checked as 'main', the first uploaded image will be used.", max_length=15),
        ),
        migrations.AlterField(
            model_name='page',
            name='menu_location',
            field=models.CharField(choices=[('main', 'Separate link in main menu'), ('dropdown', 'Displayed under "More" dropdown menu')], default='dropdown', help_text='NOTE: ONLY PAGES IN THE "MORE" DROPDOWN WILL BE DISPLAYED ON THE SITE.', max_length=8),
        ),
    ]
