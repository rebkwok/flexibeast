# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0007_auto_20150913_1238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='layout',
            field=models.CharField(default='no-img', choices=[('no-img', 'No images'), ('1-img-top', 'One image, centred, top of page'), ('1-img-left', 'One image, left of text'), ('1-img-right', 'One image, right of text'), ('img-col-left', 'Multiple small images in column, left of text'), ('img-col-right', 'Multiple small images in column, right of text')], help_text='It is recommended to use landscape-oriented pictures for a single, top of page image; portrait-oriented pictures without too much detail for column layout.  One-image options will use the first uploaded image.', max_length=15),
        ),
        migrations.AlterField(
            model_name='subsection',
            name='content',
            field=models.TextField(verbose_name='Content', help_text='Leave a blank line between paragraphs.'),
        ),
        migrations.AlterField(
            model_name='subsection',
            name='subheading',
            field=models.CharField(null=True, help_text='Leave blank if no subheading required for this section', max_length=255, blank=True),
        ),
    ]
