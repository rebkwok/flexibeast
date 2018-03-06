# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0002_auto_20150831_2056'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255)),
                ('heading', models.CharField(null=True, blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SubSection',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('subheading', models.CharField(null=True, blank=True, max_length=255)),
                ('content', models.TextField(verbose_name='Content (note line breaks do not display on the summary page)')),
                ('index', models.PositiveIntegerField()),
                ('page', models.ForeignKey(to='website.Page', related_name='subsections', on_delete=models.CASCADE)),
            ],
        ),
        migrations.RemoveField(
            model_name='aboutinfo',
            name='content',
        ),
        migrations.RemoveField(
            model_name='aboutinfo',
            name='subheading',
        ),
    ]
