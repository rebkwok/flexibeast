from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse

from gallery.models import Category, Image
from gallery.tests.helpers import set_up_fb


import os
import sys
from django.conf import settings


def create_image(photo, category):
    category, _ = Category.objects.get_or_create(name=category)
    return Image.objects.create(
        category=category, photo=photo, caption='This is an image'
    )

TEST_ROOT = os.path.abspath(os.path.dirname(__file__))

@override_settings(MEDIA_ROOT=os.path.join(TEST_ROOT, 'gallery/testdata/'))
class GalleryModelTests(TestCase):

    def setUp(self):
        set_up_fb()

    def test_image_str(self):
        '''
        test that image is created with correct str output
        '''
        testimg = create_image('hoop.jpg', 'category1')
        self.assertEqual(str(testimg), 'Photo id: {}'.format(testimg.id))

    def test_deleting_category_deletes_images(self):
        img = create_image('hoop.jpg', 'categorytest')
        img1 = create_image('pole.jpg', 'categorytest')

        cat = Category.objects.get(name='categorytest')
        self.assertEqual(
            sorted([im.id for im in cat.images.all()]),
            sorted([img.id, img1.id])
        )
        self.assertEqual(Image.objects.count(), 2)
        cat.delete()
        self.assertEqual(Image.objects.count(), 0)


@override_settings(MEDIA_ROOT=os.path.join(TEST_ROOT, 'gallery/testdata/'))
class GalleryViewsTests(TestCase):

    def setUp(self):
        set_up_fb()

    def test_gallery_view(self):
        '''
        test that context is being generated correctly
        '''
        create_image('hoop.jpg', 'category1')
        response = self.client.get(reverse('gallery:gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('images' in response.context)
        self.assertTrue('categories' in response.context)

    def test_gallery_view_with_no_images(self):
        """
        If no images exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse('gallery:gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Coming soon")
        self.assertQuerysetEqual(response.context['images'], [])

    def test_gallery_view_with_image(self):
        """
        If image exists, it should be displayed.
        """
        testimg = create_image('hoop.jpg', 'category1')
        response = self.client.get(reverse('gallery:gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['images'], ['<Image: Photo id: {}>'.format(testimg.id)])
