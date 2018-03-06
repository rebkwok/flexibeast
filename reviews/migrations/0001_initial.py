# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('user_display_name', models.CharField(max_length=255)),
                ('submission_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('title', models.CharField(max_length=255, blank=True, null=True)),
                ('review', models.TextField()),
                ('rating', models.IntegerField(default=5)),
                ('published', models.BooleanField(default=False)),
                ('previous_review', models.TextField(blank=True, null=True)),
                ('previous_rating', models.IntegerField(default=5)),
                ('previous_title', models.CharField(max_length=255, blank=True, null=True)),
                ('edited', models.BooleanField(default=False)),
                ('update_published', models.BooleanField(default=False)),
                ('edited_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-submission_date',),
            },
        ),
    ]
