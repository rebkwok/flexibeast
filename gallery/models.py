from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'categories'


class Image(models.Model):
    photo = models.ImageField(upload_to='gallery')
    category = models.ForeignKey(Category, related_name='images')
    caption = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "Photo id: " + str(self.id)

    def save(self, *args, **kwargs):
        # delete old image file when replacing by updating the file
        try:
            this = Image.objects.get(id=self.id)
            if this.photo != self.photo:
                this.photo.delete(save=False)
        except: pass # when new photo then we do nothing, normal case
        super(Image, self).save(*args, **kwargs)


@receiver(pre_delete)
def delete_image(sender, instance, **kwargs):
    if sender == Image:
        instance.photo.delete()
