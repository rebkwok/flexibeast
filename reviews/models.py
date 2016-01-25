from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from django_extensions.db.fields import AutoSlugField


class Review(models.Model):

    user = models.ForeignKey(User, verbose_name='author')
    user_display_name = models.CharField(
        max_length=255, blank=True,
        verbose_name='username that will be displayed on the site',
        help_text='If not provided, your first name will be used'
    )
    submission_date = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=255, null=True, blank=True)
    review = models.TextField(verbose_name='testimonial')
    rating = models.IntegerField(default=5)
    published = models.BooleanField(default=False)

    previous_user_display_name = models.CharField(
        max_length=255, null=True, blank=True
    )
    previous_review = models.TextField(null=True, blank=True)
    previous_rating = models.IntegerField(null=True, blank=True)
    previous_title = models.CharField(max_length=255, null=True, blank=True)
    edited = models.BooleanField(default=False)
    update_published = models.BooleanField(default=False)
    edited_date = models.DateTimeField(null=True, blank=True)

    reviewed = models.BooleanField(default=False)  # flag for notifications to admin users

    slug = AutoSlugField(populate_from='title', max_length=40, unique=True)


    class Meta:
        ordering = ('-submission_date',)

    def approve(self):
        if not self.published:
            self.published = True
        elif not self.update_published:
            self.update_published = True
        self.reviewed = True
        self.save()

    def reject(self):
        self.reviewed = True
        if self.published and not self.edited:
            self.published = False
        elif self.update_published:
            self.update_published = False
        self.save()

    def save(self, *args, **kwargs):
        # if no user_display_name on save, make it the user's first name
        if not self.user_display_name:
            self.user_display_name = self.user.first_name

        already_exists = False
        if self.pk is not None:
            already_exists = True
            orig = Review.objects.get(pk=self.pk)

        # on save, check if user_display_name review, rating or title have
        # changed; if so, we
        # set edited to True, and copy the current values to previous
        # In templates, show the previous values if published is True but
        # update_published is False (i.e. not approved by staff yet)
        if already_exists:
            if self.review != orig.review or \
                            self.rating != orig.rating or \
                            self.title != orig.title or \
                            self.user_display_name != orig.user_display_name:
                self.edited = True
                self.edited_date = timezone.now()
                self.update_published = False
                self.previous_user_display_name = orig.user_display_name
                self.previous_review = orig.review
                self.previous_rating = orig.rating
                self.previous_title = orig.title
                self.reviewed = False

        # call super to save new object
        super(Review, self).save(*args, **kwargs)

    def __str__(self):
        return "{} - {}".format(
            self.user_display_name, self.submission_date.strftime('%d-%b-%y')
        )
