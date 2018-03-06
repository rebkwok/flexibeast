# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_auto_20150912_1022'),
    ]

    operations = [
        migrations.CreateModel(
            name='Picture',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('image', models.ImageField(help_text='Upload a .jpg image', blank=True, null=True, upload_to='website_pages')),
            ],
        ),
        migrations.AlterField(
            model_name='page',
            name='menu_name',
            field=models.CharField(help_text='The heading to include in the top menu bar', blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='picture',
            name='page',
            field=models.ForeignKey(to='website.Page', related_name='pictures', on_delete=models.CASCADE),
        ),
    ]
