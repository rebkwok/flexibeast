# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivateInfo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('heading', models.CharField(blank=True, null=True, max_length=255)),
                ('subheading', models.CharField(blank=True, null=True, max_length=255)),
                ('content', models.TextField(verbose_name='Content (note line breaks do not display on the summary page)')),
            ],
            options={
                'verbose_name_plural': 'Private instruction page content',
            },
        ),
        migrations.AlterModelOptions(
            name='aboutinfo',
            options={'verbose_name_plural': 'About page content'},
        ),
    ]
