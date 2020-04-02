import os
from datetime import time
from model_bakery import baker
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core import management
from django.urls import reverse
from django.test import Client, RequestFactory, TestCase, override_settings

from common.helpers import set_up_fb, _create_session

from timetable.models import WeeklySession
from website.forms import ContactForm
from website.models import Page, Picture
from website.views import contact as contact_view


class TestMixin(object):

    @classmethod
    def setUpTestData(cls):
        set_up_fb()
        cls.user = User.objects.create_user(
            username='user', email='user@test.com', password='test'
        )
        cls.staff_user = User.objects.create_user(
            username='staff_user', email='staff@test.com', password='test'
        )
        cls.staff_user.is_staff = True
        cls.staff_user.save()
        perm = Permission.objects.get(codename='can_view_restricted')
        cls.restricted_user = User.objects.create_user(
            username='restricted_user', email='restr@test.com', password='test'
        )
        cls.restricted_user.user_permissions.add(perm)

    def setUp(self):
        self.factory = RequestFactory()


class WebsiteFormsTests(TestCase):

    def test_contact_form_valid(self):

        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email_address': 'test@test.com',
            'subject': 'General Enquiry',
            'message': 'message',
            'data_privacy_accepted': True
        }

        form = ContactForm(data)
        self.assertTrue(form.is_valid())

    def test_contact_form_not_valid(self):
        data = {
            'first_name': '',
            'last_name': 'User',
            'email_address': 'test@test.com',
            'subject': 'General Enquiry',
            'message': 'message',
            'data_privacy_accepted': True
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
        page = baker.make(Page, active=True, name='new-page')
        self.assertEqual(str(page), 'New-Page page content')

    def test_spaces_in_name_replaced_with_dash(self):
        page = baker.make(Page, active=True, name='new page')
        self.assertEqual(page.name, 'new-page')

    def test_creating_picture_instance(self):
        page = baker.make(Page)
        pic_file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        pic = Picture.objects.create(image=pic_file.name, page=page)
        self.assertEqual(pic.image, pic_file.name)
        os.unlink(pic_file.name)

    def test_deleting_picture_instance_deletes_file(self):
        page = baker.make(Page)
        pic_file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')
        pic = Picture.objects.create(image=pic_file.name, page=page)

        self.assertTrue(os.path.exists(pic_file.name))
        pic.delete()
        self.assertFalse(os.path.exists(pic_file.name))

        # clean up temp file if it wasn't properly deleted in the test
        with self.assertRaises(FileNotFoundError):
            os.unlink(pic_file.name)

    def test_uploading_new_picture_overrides_existing_file(self):
        page = baker.make(Page)
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


class PageViewsTests(TestMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super(PageViewsTests, cls).setUpTestData()
        cls.restricted_page = baker.make(
            Page, active=True, name="test/name", restricted=True
        )
        cls.restricted_page_url = reverse(
            'website:page', kwargs={'page_name': cls.restricted_page.name}
        )
        cls.public_page = baker.make(Page, active=True, name="testname1")
        cls.public_page_url = reverse(
            'website:page', kwargs={'page_name': cls.public_page.name}
        )

    def login(self, user):
        self.client.login(username=user.username, password='test')

    def test_can_get_page(self):
        resp = self.client.get(self.public_page_url)
        self.assertEqual(resp.status_code, 200)

        self.login(self.user)
        resp = self.client.get(self.public_page_url)
        self.assertEqual(resp.status_code, 200)

        # no staff messages shown
        self.assertNotIn(
            "THIS IS A RESTRICTED PAGE.", resp.rendered_content
        )
        self.assertNotIn(
            "THIS PAGE IS NOT LIVE", resp.rendered_content
        )

    def test_return_404_if_page_does_not_exist(self):
        resp = self.client.get(
            reverse('website:page', kwargs={'page_name': 'nonexistant'})
        )
        self.assertEqual(resp.status_code, 404)

    def test_cannot_get_restricted_page_if_not_logged_in(self):
        resp = self.client.get(self.restricted_page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(
            resp.url, reverse('website:restricted_page_not_logged_in')
        )

    def test_cannot_get_restricted_page_without_permission(self):
        self.login(self.user)
        resp = self.client.get(self.restricted_page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse('permission_denied'))

    def test_can_get_restricted_page_if_has_permission(self):
        self.login(self.restricted_user)
        resp = self.client.get(self.restricted_page_url)
        self.assertEqual(resp.status_code, 200)

        # staff message not shown on page
        self.assertNotIn(
            "THIS IS A RESTRICTED PAGE.", resp.rendered_content
        )

    def test_can_get_restricted_page_if_staff_user(self):
        self.login(self.staff_user)
        resp = self.client.get(self.restricted_page_url)
        self.assertEqual(resp.status_code, 200)

        # staff message shown on page
        self.assertIn(
            "THIS IS A RESTRICTED PAGE.", resp.rendered_content
        )

    def test_get_correct_default_template_layout(self):
        resp = self.client.get(self.public_page_url)
        # default template is page.html
        self.assertEqual(resp.template_name, 'website/page.html')

    def test_get_default_template_layout_if_no_pictures(self):
        self.public_page.layout = '1-img-left'
        self.public_page.save()
        resp = self.client.get(self.public_page_url)

        # if no pictures, default template is used
        self.assertEqual(resp.template_name, 'website/page.html')

    def test_get_relevant_template_layout_if_pictures(self):
        self.public_page.layout = '1-img-left'
        self.public_page.save()
        baker.make(Picture, page=self.public_page)

        resp = self.client.get(self.public_page_url)
        self.assertEqual(resp.template_name, 'website/page_side.html')

    def test_cannot_get_inactive_page_if_not_staff(self):
        page = baker.make(Page, active=False, name="testname2")
        self.login(self.user)
        resp = self.client.get(
            reverse('website:page', kwargs={'page_name': page.name})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse('permission_denied'))

        # permission denied page if restricted user and restricted page too
        page.restricted = True
        page.save()
        resp = self.client.get(
            reverse('website:page', kwargs={'page_name': page.name})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse('permission_denied'))

    def test_cannot_get_inactive_page_if_not_logged_in(self):
        page = baker.make(Page, active=False, name="testname3")
        resp = self.client.get(
            reverse('website:page', kwargs={'page_name': page.name})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse('permission_denied'))

    def test_can_get_inactive_page_if_staff_user(self):
        page = baker.make(Page, active=False, name="testname4")
        self.login(self.staff_user)
        resp = self.client.get(
            reverse('website:page', kwargs={'page_name': page.name})
        )
        self.assertEqual(resp.status_code, 200)

        # message shown on page
        self.assertIn("THIS PAGE IS NOT LIVE", resp.rendered_content)


class ContactViewsTests(TestMixin, TestCase):

    def _get_response(self, user=None, session_data={}, referer=None):
        url = reverse('website:contact')
        request = self.factory.get(url)
        if user:
            request.user = user
        if referer:
            request.META['HTTP_REFERER'] = referer
        store = _create_session()
        request.session = store

        for k, v in session_data.items():
            request.session[k] = v

        return contact_view(request)

    def _post_response(self, form_data):
        url = reverse('website:contact')
        request = self.factory.post(url, form_data)

        store = _create_session()
        request.session = store
        messages = FallbackStorage(request)
        request._messages = messages
        return contact_view(request)

    def test_can_get_contact_form_page(self):
        resp = self.client.get(reverse('website:contact'))
        self.assertEqual(resp.status_code, 200)

        resp = self._get_response(self.user)
        self.assertEqual(resp.status_code, 200)

    def test_contact_form_retrieves_user_info_from_session(self):
        resp = self._get_response()
        form = resp.context_data['form']
        self.assertEqual(
            form.initial,
            {
                'subject': 'General Enquiry',
                'other_subject': '',
                'first_name': '',
                'email_address': '',
                'last_name': '',
                'data_privacy_accepted': False,
            }
        )

        session_data = {
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
            'data_privacy_accepted': True,
        }
        resp = self._get_response(session_data=session_data)
        form = resp.context_data['form']
        self.assertEqual(
            form.initial,
            {
                'subject': 'General Enquiry',
                'other_subject': '',
                'first_name': 'test',
                'last_name': 'testname',
                'email_address': 'test@test.com',
                'data_privacy_accepted': True,
            }
        )

    def test_populate_subject_based_on_previous_page(self):
        class_page = baker.make(Page, active=True, name='classes')
        workshop_page = baker.make(Page, active=True, name='workshops')
        other_page = baker.make(Page)

        referer = reverse(
            'website:page', kwargs={'page_name': class_page.name}
        )
        resp = self._get_response(referer=referer)
        form = resp.context_data['form']
        self.assertEqual(form.initial['subject'], 'Booking Enquiry')

        referer = reverse('website:page', kwargs={'page_name': workshop_page.name})
        resp = self._get_response(referer=referer)
        form = resp.context_data['form']
        self.assertEqual(form.initial['subject'], 'Workshop Enquiry')

        referer = reverse('website:page', kwargs={'page_name': other_page.name})
        resp = self._get_response(referer=referer)
        form = resp.context_data['form']
        self.assertEqual(form.initial['subject'], 'General Enquiry')

        ttsession = baker.make(
            WeeklySession, name="Splits", day='01MON',
            time=time(hour=19, minute=00)
        )
        resp = self.client.get(
            reverse('website:contact') + '?enq={}'.format(ttsession.id)
        )
        form = resp.context_data['form']
        self.assertEqual(form.initial['subject'], 'Booking Enquiry')
        self.assertEqual(
            str(form.initial['other_subject']), 'Splits - Monday 19:00'
        )

    def test_process_valid_contact_form(self):

        form_data = {
            'subject': 'General Enquiry',
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
            'message': 'Hello',
            'cc': False,
            'data_privacy_accepted': True
        }

        self._post_response(form_data)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(
            email.subject,
            '{} General Enquiry'.format(settings.ACCOUNT_EMAIL_SUBJECT_PREFIX)
        )
        self.assertEqual(email.to, ['flexibeasttest@gmail.com'])
        self.assertEqual(email.reply_to, ['test@test.com'])
        self.assertEqual(email.cc, [])

    def test_process_invalid_contact_form(self):

        form_data = {
            'subject': 'General Enquiry',
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
            'cc': False,
            'data_privacy_accepted': True
        }

        resp = self._post_response(form_data)
        self.assertEqual(len(mail.outbox), 0)

        # form is returned in context with errors
        form = resp.context_data['form']
        self.assertEqual(
            form.errors, {'message': ['This field is required.']}
        )

    def test_process_valid_contact_form_with_cc(self):

        form_data = {
            'subject': 'General Enquiry',
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
            'message': 'Hello',
            'cc': True,
            'data_privacy_accepted': True
        }

        self._post_response(form_data)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['flexibeasttest@gmail.com'])
        self.assertEqual(email.reply_to, ['test@test.com'])
        self.assertEqual(email.cc, ['test@test.com'])

    def test_process_contact_form_with_additional_subject(self):

        form_data = {
            'subject': 'General Enquiry',
            'other_subject': 'My subject',
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
            'message': 'Hello',
            'cc': True,
            'data_privacy_accepted': True
        }

        self._post_response(form_data)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['flexibeasttest@gmail.com'])
        self.assertEqual(email.reply_to, ['test@test.com'])
        self.assertEqual(email.cc, ['test@test.com'])
        self.assertEqual(
            email.subject, '{} General Enquiry: My subject'.format(
                settings.ACCOUNT_EMAIL_SUBJECT_PREFIX
            )
        )

    def test_message(self):
        form_data = {
            'subject': 'General Enquiry',
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
            'message': 'Hello',
            'cc': True,
            'data_privacy_accepted': True
        }
        resp = self.client.post(
            reverse('website:contact'), form_data, follow=True
        )

        self.assertIn(
            "Thank you for your enquiry! Your email has been sent and "
            "we&#x27;ll get back to you as soon as possible.",
            resp.rendered_content
        )


class WebsiteManagementTests(TestCase):

    def test_create_about_page(self):
        self.assertFalse(Page.objects.exists())
        management.call_command('create_about_page')
        self.assertEqual(Page.objects.count(), 1)
        self.assertEqual(Page.objects.first().name, 'about')

    def test_about_page_not_overwritten_if_already_exists(self):
        management.call_command('create_about_page')
        self.assertEqual(Page.objects.count(), 1)
        self.assertEqual(Page.objects.first().name, 'about')
        self.assertEqual(Page.objects.first().content, 'Coming Soon')

        page = Page.objects.first()
        page.content = 'new content'
        page.save()

        management.call_command('create_about_page')
        self.assertEqual(Page.objects.count(), 1)
        self.assertEqual(Page.objects.first().name, 'about')
        self.assertEqual(Page.objects.first().content, 'new content')
