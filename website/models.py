from django.db import models


PAGE_LAYOUT_CHOICES = (
    ('no-img', 'No images'),
    ('1-img-top', 'One image, centred, top of page'),
    ('1-img-left', 'One image, left of text'),
    ('1-img-right', 'One image, right of text'),
    ('img-col-left', 'Multiple small images in column, left of text'),
    ('img-col-right', 'Multiple small images in column, right of text'),
)


class Page(models.Model):

    name = models.CharField(
        max_length=255, unique=True,
        help_text="A unique identifier for this page. Use lowercase, no spaces."
    )
    menu_name = models.CharField(
        max_length=255,
        help_text="The heading to include in the top menu bar; if left "
                  "blank, will not be shown as a menu option.",
        null=True, blank=True
    )
    menu_location = models.CharField(
        max_length=8,
        choices=(
            ('main', 'Separate link in main menu'),
            ('dropdown', 'Displayed under "More" dropdown menu')
        ),
        default='dropdown',
        help_text='Choose where to display the menu link.  Note that all '
                  'options appear under the "More" dropdown at small screen '
                  'sizes'
    )
    heading = models.CharField(max_length=255, null=True, blank=True)
    layout = models.CharField(
        max_length=15, choices=PAGE_LAYOUT_CHOICES, default='no-img',
        help_text="It is recommended to use landscape-oriented pictures for "
                  "a single, top of page image; portrait-oriented pictures "
                  "without too much detail for column layout.  One-image "
                  "options will use the first uploaded image."
    )

    def __str__(self):
        return "{} page content".format(self.name.title())

    def save(self):
        self.name = self.name.lower()
        if ' ' in self.name:
            self.name = self.name.replace(' ', '-')
        super(Page, self).save()


class SubSection(models.Model):
    subheading = models.CharField(
        max_length=255, null=True, blank=True,
        help_text="Leave blank if no subheading required for this section"
    )
    content = models.TextField(
        'Content',
        help_text='Leave a blank line between paragraphs.'
    )
    index = models.PositiveIntegerField()
    page = models.ForeignKey(Page, related_name='subsections')

    class Meta:
        ordering = ['index']

    def __str__(self):
        return "{} page - subsection {} {}".format(
            self.page.name.title(), self.index,
            "- {}".format(self.subheading) if self.subheading else ''
        )

class Picture(models.Model):
    image = models.ImageField(
        upload_to='website_pages', null=True, blank=True,
        help_text="Upload a .jpg image")
    page = models.ForeignKey(Page, related_name='pictures')

    def save(self, *args, **kwargs):
        # delete old image file when replacing by updating the file
        try:
            this = Picture.objects.get(id=self.id)
            if this.image != self.image:
                this.image.delete(save=False)
        except:
            pass # when new photo then we do nothing, normal case
        super(Picture, self).save(*args, **kwargs)