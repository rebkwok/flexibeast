import os
from tempfile import NamedTemporaryFile

from django.test import Client, RequestFactory, TestCase, override_settings

from model_mommy import mommy

from website.forms import ContactForm
from website.models import Page, Picture


class WebsiteFormsTests(TestCase):

    def test_contact_form_valid(self):

        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email_address': 'test@test.com',
            'subject': 'General Enquiry',
            'message': 'message'
        }

        form = ContactForm(data)
        self.assertTrue(form.is_valid())

    def test_contact_form_not_valid(self):
        data = {
            'first_name': '',
            'last_name': 'User',
            'email_address': 'test@test.com',
            'subject': 'General Enquiry',
            'message': 'message'
        }

        form = ContactForm(data)
        self.assertFalse(form.is_valid())

        self.assertEqual(
            form.errors,
            {'first_name': ['This field is required.']}
        )

        data['first_name'] = 'Test'
        data['email_address'] = 'test.test.com'
        form = ContactForm(data)
        self.assertFalse(form.is_valid())

        self.assertEqual(
            form.errors,
            {'email_address': ['Enter a valid email address.']}
        )


@override_settings(MEDIA_ROOT='/tmp/')
class WebsiteModelsTests(TestCase):

    def test_page_str(self):
        page = mommy.make(Page, name='new-page')
        self.assertEqual(str(page), 'New-Page page content')

    def test_spaces_in_name_replaced_with_dash(self):
        page = mommy.make(Page, name='new page')
        self.assertEqual(page.name, 'new-page')

    def test_creating_picture_instance(self):
        page = mommy.make(Page)
        pic_file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        pic = Picture.objects.create(image=pic_file.name, page=page)
        self.assertEqual(pic.image, pic_file.name)
        os.unlink(pic_file.name)

    def test_deleting_picture_instance_deletes_file(self):
        page = mommy.make(Page)
        pic_file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        pic = Picture.objects.create(image=pic_file.name, page=page)

        self.assertTrue(os.path.exists(pic_file.name))
        pic.delete()
        self.assertFalse(os.path.exists(pic_file.name))

        # clean up temp file if it wasn't properly deleted in the test
        with self.assertRaises(FileNotFoundError):
            os.unlink(pic_file.name)

    def test_uploading_new_picture_overrides_existing_file(self):
        page = mommy.make(Page)
        pic_file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        pic_file1 = NamedTemporaryFile(suffix='.jpg', dir='/tmp')

        pic = Picture.objects.create(image=pic_file.name, page=page)
        self.assertTrue(os.path.exists(pic_file.name))
        self.assertTrue(os.path.exists(pic_file1.name))

        pic.image = pic_file1.name
        pic.save()
        # overwriting the image file has deleted the original one
        self.assertFalse(os.path.exists(pic_file.name))
        self.assertTrue(os.path.exists(pic_file1.name))

        os.unlink(pic_file1.name)
        # check and clean up overwritten temp file if it wasn't properly deleted
        with self.assertRaises(FileNotFoundError):
            os.unlink(pic_file.name)


class PageViewsTests(TestCase):

    def test_can_get_page(self):
        pass

    def test_return_404_if_page_does_not_exist(self):
        pass

    def test_cannot_get_restricted_page(self):
        pass

    def test_can_get_restricted_page_if_has_permission(self):
        pass

    def test_can_get_restricted_page_if_staff_user(self):
        pass

    def test_get_correct_template_layout(self):
        pass


class ContactViewsTests(TestCase):

    def test_can_get_contact_form_page(self):
        pass

    def test_contact_form_retrieves_user_info_from_session(self):
        pass

    def test_populate_subject_based_on_previous_page(self):
        pass

    def test_process_contact_form(self):
        pass
