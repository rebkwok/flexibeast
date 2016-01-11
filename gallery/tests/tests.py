import os

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
        self.assertQuerysetEqual(
            response.context['images'],
            ['<Image: Photo id: {}>'.format(testimg.id)]
        )

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


@override_settings(MEDIA_ROOT=os.path.join(TEST_ROOT, 'gallery/testdata/'))
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
