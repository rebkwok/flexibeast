import os

from tempfile import NamedTemporaryFile

from django.conf import settings
from django.test import Client, RequestFactory, TestCase, override_settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages.storage.fallback import FallbackStorage

from model_mommy import mommy

from gallery.models import Category, Image
from gallery.tests.helpers import set_up_fb, _create_session
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

    def _get_response(self, user, data={}):
        url = reverse('gallery:gallery')
        request = self.factory.get(url, data)
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

    def test_gallery_view_filter(self):
        """
        Test gallery shows only images in selected category
        """
        file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        testimg = create_image(file.name, 'category')
        file1 = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        testimg1 = create_image(file1.name, 'category1')
        file2 = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        testimg2 = create_image(file2.name, 'category2')

        response = self.client.get(
            reverse('gallery:gallery'), {'category': [testimg.category.id]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['images'],
            ['<Image: Photo id: {}>'.format(testimg.id)]
        )

        response = self.client.get(
            reverse('gallery:gallery'), {'category': [testimg1.category.id]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['images'],
            ['<Image: Photo id: {}>'.format(testimg1.id)]
        )

        os.unlink(file.name)
        os.unlink(file1.name)
        os.unlink(file2.name)


@override_settings(MEDIA_ROOT='/tmp/')
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
        store = _create_session()
        request.session = store
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
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

    def test_cannot_post_if_not_staff_user(self):
        formset_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-name': 'test',
            'form-0-description': 'description'
        }

        # no logged in user
        response = self.client.post(
            reverse('gallery:categories'), formset_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.PERMISSION_DENIED_URL), response.url)
        self.assertFalse(Category.objects.exists())

        # logged in non-staff user
        response = self._post_response(self.user, formset_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.PERMISSION_DENIED_URL), response.url)
        self.assertFalse(Category.objects.exists())

        # logged in staff user
        response = self._post_response(self.staff_user, formset_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('gallery:categories'), response.url)
        self.assertTrue(Category.objects.exists())

    def test_add_category(self):
        formset_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-name': 'test',
            'form-0-description': 'description'
        }
        self.assertFalse(Category.objects.exists())
        self._post_response(self.staff_user, formset_data)

        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.first().name, 'test')
        self.assertEqual(Category.objects.first().description, 'description')

    def test_add_category_description_not_required(self):
        formset_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-name': 'test',
        }
        self.assertFalse(Category.objects.exists())
        self._post_response(self.staff_user, formset_data)

        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.first().name, 'test')

    def test_update_category(self):
        category = mommy.make(Category)
        formset_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': category.id,
            'form-0-name': 'test',
            'form-0-description': 'description'
        }

        self.assertNotEqual(category.name, 'test')
        self.assertNotEqual(category.description, 'description')
        self._post_response(self.staff_user, formset_data)

        category.refresh_from_db()
        self.assertEqual(category.name, 'test')
        self.assertEqual(category.description, 'description')

    def test_add_additional_category(self):
        category = mommy.make(Category)
        formset_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 1,
            'form-0-id': category.id,
            'form-0-name': category.name,
            'form-0-description': category.description,
            'form-1-name': 'new test',
            'form-1-description': 'new description'
        }

        self.assertEquals(Category.objects.count(), 1)
        self._post_response(self.staff_user, formset_data)

        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(Category.objects.last().name, 'new test')
        self.assertEqual(Category.objects.last().description, 'new description')

    def test_delete_category(self):
        category = mommy.make(Category)
        formset_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': category.id,
            'form-0-name': category.name,
            'form-0-description': category.description,
            'form-0-DELETE': True,
        }
        self.assertEquals(Category.objects.count(), 1)
        self._post_response(self.staff_user, formset_data)
        self.assertFalse(Category.objects.exists())

    def test_get_category_with_images(self):
        category = mommy.make(Category, name='category')
        file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        testimg = create_image(file.name, 'category')

        resp = self._get_response(self.staff_user)
        self.assertEqual(
            [cat.id for cat in resp.context_data['categories']],
            [category.id]
        )
        form = resp.context_data['categories_formset'].forms[0]
        self.assertEqual(
            [img.id for img in form.instance.images.all()],
            [img.id for img in Image.objects.all()]
        )

        self.assertIn(
            'id="cat_{}_imagecount">{}<'.format(category.id, category.images.count()),
            resp.rendered_content
        )
        os.unlink(file.name)

    def test_delete_category_with_images(self):
        category = mommy.make(Category, name='category')
        file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        testimg = create_image(file.name, 'category')

        formset_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': category.id,
            'form-0-name': category.name,
            'form-0-description': category.description,
            'form-0-DELETE': True,
        }
        self.assertEquals(Category.objects.count(), 1)
        self.assertEquals(Image.objects.count(), 1)
        self._post_response(self.staff_user, formset_data)
        self.assertFalse(Category.objects.exists())
        # deleting the category also deleted the associated image
        self.assertFalse(Image.objects.exists())

        # and the image file has been deleted from the filesystem
        with self.assertRaises(FileNotFoundError):
            os.unlink(file.name)

    def test_add_multiple_categories(self):
        formset_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-name': 'test1',
            'form-0-description': 'description1',
            'form-1-name': 'test2',
            'form-1-description': 'description2'
        }
        self.assertEquals(Category.objects.count(), 0)
        self._post_response(self.staff_user, formset_data)
        self.assertEqual(Category.objects.count(), 2)

    def test_update_multiple_categories(self):
        category1 = mommy.make(Category, name='category1')
        category2 = mommy.make(Category, name='category2')

        formset_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-id': category1.id,
            'form-0-name': 'test1',
            'form-0-description': 'description1',
            'form-1-id': category2.id,
            'form-1-name': 'test2',
            'form-1-description': 'description2'
        }
        self.assertEquals(Category.objects.count(), 2)
        self.assertNotEqual(category1.name, 'test1')
        self.assertNotEqual(category1.description, 'description1')
        self.assertNotEqual(category2.name, 'test2')
        self.assertNotEqual(category2.description, 'description2')

        self._post_response(self.staff_user, formset_data)
        category1.refresh_from_db()
        category2.refresh_from_db()
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(category1.name, 'test1')
        self.assertEqual(category1.description, 'description1')
        self.assertEqual(category2.name, 'test2')
        self.assertEqual(category2.description, 'description2')

    def test_delete_multiple_categories(self):
        category1 = mommy.make(Category, name='category1')
        category2 = mommy.make(Category, name='category2')

        formset_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-id': category1.id,
            'form-0-name': category1.name,
            'form-0-description': category1.description,
            'form-0-DELETE': True,
            'form-1-id': category2.id,
            'form-1-name': category2.name,
            'form-1-description': category2.description,
            'form-1-DELETE': True,
        }
        self.assertEquals(Category.objects.count(), 2)

        self._post_response(self.staff_user, formset_data)
        self.assertEqual(Category.objects.count(), 0)


@override_settings(MEDIA_ROOT='/tmp/')
class CategoryUpdateViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make(User)
        self.staff_user = mommy.make(User)
        self.staff_user.is_staff = True
        self.staff_user.save()
        self.category = mommy.make(Category, name='category')

    def _get_response(self, user, category_id):
        url = reverse('gallery:edit_category', args=[category_id])
        request = self.factory.get(url)
        request.user = user
        view = CategoryUpdateView.as_view()
        return view(request, pk=category_id)

    def _post_response(self, user, category_id, data):
        url = reverse('gallery:edit_category', args=[category_id])
        request = self.factory.post(url, data, follow=True)
        store = _create_session()
        request.session = store
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = CategoryUpdateView.as_view()
        return view(request, pk=category_id)

    def test_staff_user_required(self):
        # no logged in user
        response = self.client.get(
            reverse('gallery:edit_category', args=[self.category.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.PERMISSION_DENIED_URL), response.url)

        # logged in non-staff user
        response = self._get_response(self.user, self.category.id)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.PERMISSION_DENIED_URL), response.url)

        # logged in staff user
        response = self._get_response(self.staff_user, self.category.id)
        self.assertEqual(response.status_code, 200)

    def test_cannot_post_if_not_staff_user(self):
        formset_data = {
            'images-TOTAL_FORMS': 0,
            'images-INITIAL_FORMS': 0,
        }

        # no logged in user
        response = self.client.post(
            reverse('gallery:edit_category', args=[self.category.id]),
            formset_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.PERMISSION_DENIED_URL), response.url)

        # logged in non-staff user
        response = self._post_response(self.user, self.category.id, formset_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.PERMISSION_DENIED_URL), response.url)

        # logged in staff user
        response = self._post_response(
            self.staff_user, self.category.id, formset_data
        )
        self.assertEqual(response.status_code, 200)

    def test_add_image(self):
        testfile_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'testjpg.jpg'
        )
        with open(testfile_path, 'rb') as file:
            photo = SimpleUploadedFile(
                file.name, content=file.read()
            )

        formset_data = {
            'name': self.category.name,
            'description': self.category.description,
            'images-TOTAL_FORMS': 1,
            'images-INITIAL_FORMS': 0,
            'images-0-photo': photo,
        }

        self.assertFalse(self.category.images.exists())
        response = self._post_response(
            self.staff_user, self.category.id, formset_data
        )
        self.assertEqual(response.status_code, 302)
        self.category.refresh_from_db()
        self.assertEqual(self.category.images.count(), 1)

    def test_adding_non_image(self):
        testfile_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'testpdf.pdf'
        )
        with open(testfile_path, 'rb') as file:
            photo = SimpleUploadedFile(
                file.name, content=file.read()
            )

        formset_data = {
            'name': self.category.name,
            'description': self.category.description,
            'images-TOTAL_FORMS': 1,
            'images-INITIAL_FORMS': 0,
            'images-0-photo': photo,
        }

        response = self._post_response(
            self.staff_user, self.category.id, formset_data
        )
        self.assertEqual(response.status_code, 200)
        formset = response.context_data['image_formset']
        img_form = formset.forms[0]
        self.assertFalse(formset.is_valid())
        self.assertEquals(
            img_form.errors,
            {
                'photo': [
                    'Upload a valid image. The file you uploaded was either '
                    'not an image or a corrupted image.'
                ]
            }
        )
