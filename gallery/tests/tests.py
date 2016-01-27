import os

from tempfile import NamedTemporaryFile

from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.messages.storage.fallback import FallbackStorage

from model_mommy import mommy

from gallery.models import Category, Image
from gallery.tests.helpers import set_up_fb
from gallery.views import CategoryListView, CategoryUpdateView, view_gallery


def create_image(photo, category):
    category, _ = Category.objects.get_or_create(name=category)
    return Image.objects.create(
        category=category, photo=photo, caption='This is an image'
    )


@override_settings(MEDIA_ROOT='/tmp/')
class GalleryModelTests(TestCase):

    def setUp(self):
        set_up_fb()

    def test_image_str(self):
        '''
        test that image is created with correct str output
        '''
        file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        testimg = create_image(file.name, 'category1')
        self.assertEqual(str(testimg), 'Photo id: {}'.format(testimg.id))
        os.unlink(file.name)

    def test_deleting_category_deletes_images(self):
        file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        file1 = NamedTemporaryFile(suffix='.jpg', dir='/tmp')

        img = create_image(file.name, 'categorytest')
        img1 = create_image(file1.name, 'categorytest')

        cat = Category.objects.get(name='categorytest')
        self.assertEqual(
            sorted([im.id for im in cat.images.all()]),
            sorted([img.id, img1.id])
        )
        self.assertEqual(Image.objects.count(), 2)
        cat.delete()
        self.assertEqual(Image.objects.count(), 0)

        with self.assertRaises(FileNotFoundError):
            os.unlink(file.name)

        with self.assertRaises(FileNotFoundError):
            os.unlink(file1.name)

    def test_deleting_image_from_category_deletes_file(self):
        file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        file1 = NamedTemporaryFile(suffix='.jpg', dir='/tmp')

        create_image(file.name, 'categorytest')
        create_image(file1.name, 'categorytest')
        self.assertEqual(Image.objects.count(), 2)

        self.assertTrue(os.path.exists(file.name))
        self.assertTrue(os.path.exists(file1.name))

        cat = Category.objects.get(name='categorytest')
        self.assertEqual(cat.images.first().photo, file.name)
        cat.images.first().delete()
        self.assertEqual(Image.objects.count(), 1)

        self.assertFalse(os.path.exists(file.name))
        self.assertTrue(os.path.exists(file1.name))

        os.unlink(file1.name)
        # check and clean up deleted temp file if it wasn't properly deleted
        with self.assertRaises(FileNotFoundError):
            os.unlink(file.name)


@override_settings(MEDIA_ROOT='/tmp/')
class GalleryViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make(User)
        self.staff_user = mommy.make(User)
        self.staff_user.is_staff = True
        self.staff_user.save()

    def _get_response(self, user):
        url = reverse('gallery:gallery')
        request = self.factory.get(url)
        request.user = user
        return view_gallery(request)

    def test_login_not_required(self):
        """
        test that page is accessible if there is no user logged in
        """
        url = reverse('gallery:gallery')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_gallery_view(self):
        '''
        test that context is being generated correctly
        '''
        file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        create_image(file.name, 'category1')
        response = self.client.get(reverse('gallery:gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('images' in response.context)
        self.assertTrue('categories' in response.context)

        os.unlink(file.name)

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
        file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        testimg = create_image(file.name, 'category1')
        response = self.client.get(reverse('gallery:gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['images'],
            ['<Image: Photo id: {}>'.format(testimg.id)]
        )

        os.unlink(file.name)

    def test_gallery_view_with_logged_in_user(self):
        """
        With logged in (not staff) user, the edit gallery links are still
        not shown
        """
        response = self._get_response(self.user)
        self.assertNotIn('View and edit Gallery', str(response.content))

    def test_gallery_view_with_logged_in_staff_user(self):
        """
        With staff user, the edit gallery links are shown
        """
        response = self._get_response(self.staff_user)
        self.assertIn('View and edit Gallery', str(response.content))


class CategoryListViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make(User)
        self.staff_user = mommy.make(User)
        self.staff_user.is_staff = True
        self.staff_user.save()

    def _get_response(self, user):
        url = reverse('gallery:categories')
        request = self.factory.get(url)
        request.user = user
        view = CategoryListView.as_view()
        return view(request)

    def _post_response(self, user, data):
        url = reverse('gallery:categories')
        request = self.factory.post(url, data)
        request.user = user
        view = CategoryListView.as_view()
        return view(request)

    def test_staff_user_required(self):
        # no logged in user
        response = self.client.get(reverse('gallery:categories'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.PERMISSION_DENIED_URL), response.url)

        # logged in non-staff user
        response = self._get_response(self.user)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.PERMISSION_DENIED_URL), response.url)

        # logged in staff user
        response = self._get_response(self.staff_user)
        self.assertEqual(response.status_code, 200)
