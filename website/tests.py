import os
from model_mommy import mommy
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core import management
from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory, TestCase, override_settings

from flex_bookings.tests.helpers import set_up_fb, _create_session

from website.forms import ContactForm
from website.models import Page, Picture
from website.views import contact as contact_view
from website.views import page as page_view


class TestMixin(object):
    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')
        self.staff_user = mommy.make_recipe('flex_bookings.user')
        self.staff_user.is_staff = True
        self.staff_user.save()
        perm = Permission.objects.get(codename='can_view_restricted')
        self.restricted_user = mommy.make_recipe('flex_bookings.user')
        self.restricted_user.user_permissions.add(perm)


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
        page = mommy.make(Page, active=True, name='new-page')
        self.assertEqual(str(page), 'New-Page page content')

    def test_spaces_in_name_replaced_with_dash(self):
        page = mommy.make(Page, active=True, name='new page')
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


class PageViewsTests(TestMixin, TestCase):

    def _get_response(self, user, page):
        url = reverse('website:page', kwargs={'page_name': page.name})
        request = self.factory.get(url)
        request.user = user
        return page_view(request, page.name)

    def test_can_get_page(self):
        page = mommy.make(Page, active=True, name="testname")
        resp = self.client.get(
            reverse('website:page', kwargs={'page_name': page.name})
        )
        self.assertEqual(resp.status_code, 200)

        resp = self._get_response(self.user, page)
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
        page = mommy.make(Page, active=True, name="testname", restricted=True)
        resp = self.client.get(
            reverse('website:page', kwargs={'page_name': page.name})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(
            resp.url, reverse('website:restricted_page_not_logged_in')
        )

    def test_cannot_get_restricted_page_without_permission(self):
        page = mommy.make(Page, active=True, name="testname", restricted=True)
        resp = self._get_response(self.user, page)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse('permission_denied'))

    def test_can_get_restricted_page_if_has_permission(self):
        page = mommy.make(Page, active=True, name="testname", restricted=True)
        resp = self._get_response(self.restricted_user, page)
        self.assertEqual(resp.status_code, 200)

        # staff message not shown on page
        self.assertNotIn(
            "THIS IS A RESTRICTED PAGE.", resp.rendered_content
        )

    def test_can_get_restricted_page_if_staff_user(self):
        page = mommy.make(Page, active=True, name="testname", restricted=True)
        resp = self._get_response(self.staff_user, page)
        self.assertEqual(resp.status_code, 200)

        # staff message shown on page
        self.assertIn(
            "THIS IS A RESTRICTED PAGE.", resp.rendered_content
        )

    def test_get_correct_default_template_layout(self):
        page = mommy.make(Page, active=True, name="testname")
        resp = self._get_response(self.user, page)

        # default template is page.html
        self.assertEqual(resp.template_name, 'website/page.html')

    def test_get_default_template_layout_if_no_pictures(self):
        page = mommy.make(Page, active=True, name="testname", layout='img-col-right')
        resp = self._get_response(self.user, page)

        # if no pictures, default template is used
        self.assertEqual(resp.template_name, 'website/page.html')

    def test_get_relevant_template_layout_if_pictures(self):
        page = mommy.make(Page, active=True, name="testname", layout='img-col-right')
        mommy.make(Picture, page=page)

        resp = self._get_response(self.user, page)
        self.assertEqual(resp.template_name, 'website/page_col.html')

    def test_include_extra_html_for_about_page(self):
        page = mommy.make(Page, active=True, name="testname")
        resp = self._get_response(self.user, page)
        self.assertEqual(resp.context_data['include_html'], '')

        page = mommy.make(Page, active=True, name="about")
        resp = self._get_response(self.user, page)
        self.assertEqual(
            resp.context_data['include_html'], 'website/about_extra.html'
        )

    def test_cannot_get_inactive_page_if_not_staff(self):
        page = mommy.make(Page, active=False, name="testname")
        resp = self._get_response(self.user, page)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse('permission_denied'))

        # permission denied page if restricted user and restricted page too
        page.restricted = True
        page.save()
        resp = self._get_response(self.restricted_user, page)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse('permission_denied'))

    def test_cannot_get_inactive_page_if_not_logged_in(self):
        page = mommy.make(Page, active=False, name="testname")
        resp = self.client.get(
            reverse('website:page', kwargs={'page_name': page.name})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse('permission_denied'))

    def test_can_get_inactive_page_if_staff_user(self):
        page = mommy.make(Page, active=False, name="testname")
        resp = self._get_response(self.staff_user, page)
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
                'last_name': ''
            }
        )

        session_data = {
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
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
            }
        )

    def test_populate_subject_based_on_previous_page(self):
        class_page = mommy.make(Page, active=True, name='classes')
        workshop_page = mommy.make(Page, active=True, name='workshops')
        other_page = mommy.make(Page)

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

    def test_process_valid_contact_form(self):

        form_data = {
            'subject': 'General Enquiry',
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
            'message': 'Hello',
            'cc': False
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
            'cc': False
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
            'cc': True
        }

        self._post_response(form_data)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['flexibeasttest@gmail.com'])
        self.assertEqual(email.reply_to, ['test@test.com'])
        self.assertEqual(email.cc, ['test@test.com'])

    def test_message(self):
        form_data = {
            'subject': 'General Enquiry',
            'first_name': 'test',
            'last_name': 'testname',
            'email_address': 'test@test.com',
            'message': 'Hello',
            'cc': True
        }
        resp = self.client.post(reverse('website:contact'), form_data, follow=True)
        messages = []
        for c in resp.context:
            messages = list(c.get('messages'))

        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0].message,
            "Thank you for your enquiry! Your email has been sent and we'll "
            "get back to you as soon as possible."
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
