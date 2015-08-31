# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AboutInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('heading', models.CharField(null=True, max_length=255, blank=True)),
                ('subheading', models.CharField(null=True, max_length=255, blank=True)),
                ('content', models.TextField(verbose_name='Content (note line breaks do not display on the summary page)')),
            ],
            options={
                'verbose_name_plural': 'About page information',
            },
        ),
    ]
