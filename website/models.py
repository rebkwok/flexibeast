from django.db import models


class AboutInfo(models.Model):
    heading = models.CharField(max_length=255, null=True, blank=True)
    subheading = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField('Content (note line breaks do not display on the summary page)')

    class Meta:
        verbose_name_plural = 'About page content'

    def __str__(self):
        return "About page section " + str(self.id)

    def get_id(self):
        return self.id
    get_id.short_description = 'Section number'


class PrivateInfo(models.Model):
    heading = models.CharField(max_length=255, null=True, blank=True)
    subheading = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField('Content (note line breaks do not display on the summary page)')

    class Meta:
        verbose_name_plural = 'Private instruction page content'

    def __str__(self):
        return "About page section " + str(self.id)

    def get_id(self):
        return self.id
    get_id.short_description = 'Section number'