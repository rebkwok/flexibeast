from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile

from imagekit.models import ProcessedImageField


PAGE_LAYOUT_CHOICES = (
    ('no-img', 'No images'),
    ('1-img-top', 'One image, centred, top of page'),
    ('1-img-left', 'One image, left of text'),
    ('1-img-right', 'One image, right of text'),
)

MENU_CHOICES = (
    ('main', 'Separate link in main menu'),
    ('dropdown', 'Displayed under "More" dropdown menu')
)


class Page(models.Model):

    name = models.CharField(
        max_length=255, unique=True,
        help_text="A unique identifier for this page. Use lowercase, no "
                  "spaces.  Forward slash (/) and hyphens (-) are allowed."
    )
    menu_name = models.CharField(
        max_length=255,
        help_text="The heading to include in the top menu bar; if left "
                  "blank, will not be shown as a menu option.",
        null=True, blank=True
    )
    menu_location = models.CharField(
        max_length=8,
        choices=MENU_CHOICES,
        default='dropdown',
        help_text='NOTE: ONLY PAGES IN THE "MORE" DROPDOWN WILL BE DISPLAYED '
                  'ON THE SITE.'
    )
    heading = models.CharField(max_length=255, null=True, blank=True)
    layout = models.CharField(
        max_length=15, choices=PAGE_LAYOUT_CHOICES, default='no-img',
        help_text="It is recommended to use landscape-oriented pictures for "
                  "a single, top of page image.  If no image is checked as "
                  "'main', the first uploaded image will be used."
    )
    content = models.TextField('Content')
    restricted = models.BooleanField(
        default=False,
        help_text='Page only visible if user is logged in and has been given '
                  'permission'
    )
    active = models.BooleanField(
        default=False,
        help_text="Unselect if you don't want this page to be visible on "
                  "the site (irrespective of user permissions)"
    )

    class Meta:
        permissions = (
            ("can_view_restricted", "Can view restricted pages"),
        )

    def __str__(self):
        return "{} page content".format(self.name.title())

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        if ' ' in self.name:
            self.name = self.name.replace(' ', '-')
        super(Page, self).save()


class Picture(models.Model):

    image = ProcessedImageField(
        upload_to='website_pages',
        format='JPEG',
        options={'quality': 70},
        null=True, blank=True,
    )
    page = models.ForeignKey(
        Page, related_name='pictures', on_delete=models.CASCADE
    )
    main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # delete old image file when replacing by updating the file
        try:
            this = Picture.objects.get(id=self.id)
            if this.image != self.image:
                this.image.delete(save=False)
        except:
            pass # when new photo then we do nothing, normal case
        super(Picture, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # delete the image from storage when deleting Picture object
        self.image.delete()
        super(Picture, self).delete(*args, **kwargs)


class RestrictedAccessTracker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=timezone.now)
