import pytz

from datetime import datetime, timedelta
from mock import Mock, patch
from model_mommy import mommy

from django.core.urlresolvers import reverse
from django.core import mail
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import User, Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone

from activitylog.models import ActivityLog
from common.helpers import set_up_fb, _create_session

from studioadmin.tests.utils import TestPermissionMixin
from studioadmin.views.activitylog import ActivityLogListView
from studioadmin.views.email_users import choose_users_to_email, \
    email_users_view
from studioadmin.views.users import UserListView


class TestPermissionMixin(object):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('common.user')
        self.staff_user = mommy.make_recipe('common.user')
        self.staff_user.is_staff = True
        self.staff_user.save()


class UserListViewTests(TestPermissionMixin, TestCase):

    def _get_response(self, user, form_data={}):
        url = reverse('studioadmin:users')
        session = _create_session()
        request = self.factory.get(url, form_data)
        request.session = session
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = UserListView.as_view()
        return view(request)

    def test_cannot_access_if_not_logged_in(self):
        """
        test that the page redirects if user is not logged in
        """
        url = reverse('studioadmin:users')
        resp = self.client.get(url)
        redirected_url = reverse('account_login') + "?next={}".format(url)
        self.assertEquals(resp.status_code, 302)
        self.assertIn(redirected_url, resp.url)

    def test_cannot_access_if_not_staff(self):
        """
        test that the page redirects if user is not a staff user
        """
        resp = self._get_response(self.user)
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(resp.url, reverse('permission_denied'))

    def test_can_access_as_staff_user(self):
        """
        test that the page can be accessed by a staff user
        """
        resp = self._get_response(self.staff_user)
        self.assertEquals(resp.status_code, 200)

    def test_all_users_are_displayed(self):
        mommy.make_recipe('common.user', _quantity=6)
        # 8 users total, incl self.user and self.staff_user
        self.assertEqual(User.objects.count(), 8)
        resp = self._get_response(self.staff_user)
        self.assertEqual(
            list(resp.context_data['users']), list(User.objects.all())
        )

    def test_display_restricted_users(self):
        not_restr_student = mommy.make_recipe('common.user')
        restr_student = mommy.make_recipe('common.user')
        perm = Permission.objects.get(codename='can_view_restricted')
        restr_student.user_permissions.add(perm)
        restr_student.save()

        resp = self._get_response(self.staff_user)
        resp.render()
        self.assertIn(
            'id="can_view_restricted_button" value="{}">Yes'.format(restr_student.id),
            str(resp.content)
        )
        self.assertIn(
            'id="can_view_restricted_button" value="{}">No'.format(
                not_restr_student.id
            ),
            str(resp.content)
        )

    def test_change_restricted_user(self):
        not_restr_student = mommy.make_recipe('common.user')
        restr_student = mommy.make_recipe('common.user')
        perm = Permission.objects.get(codename='can_view_restricted')
        restr_student.user_permissions.add(perm)
        restr_student.save()

        self.assertTrue(
            restr_student.has_perm('website.can_view_restricted')
        )
        self._get_response(
            self.staff_user, {'change_user': [restr_student.id]}
        )
        changed_student = User.objects.get(id=restr_student.id)
        self.assertFalse(
            changed_student.has_perm('website.can_view_restricted')
        )

        self.assertFalse(
            not_restr_student.has_perm('website.can_view_restricted')
        )
        self._get_response(
            self.staff_user, {'change_user': [not_restr_student.id]}
        )
        changed_student = User.objects.get(id=not_restr_student.id)
        self.assertTrue(
            changed_student.has_perm('website.can_view_restricted')
        )


class ChooseUsersToEmailTests(TestPermissionMixin, TestCase):

    def _get_response(self, user):
        url = reverse('studioadmin:choose_email_users')
        session = _create_session()
        request = self.factory.get(url)
        request.session = session
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        return choose_users_to_email(request)

    def _post_response(self, user, form_data):
        url = reverse('studioadmin:choose_email_users')
        session = _create_session()
        request = self.factory.post(url, form_data)
        request.session = session
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        return choose_users_to_email(request)

    def formset_data(self, extra_data={}):

        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': str(self.user.id),
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_cannot_access_if_not_logged_in(self):
        """
        test that the page redirects if user is not logged in
        """
        url = reverse('studioadmin:choose_email_users')
        resp = self.client.get(url)
        redirected_url = reverse('account_login') + "?next={}".format(url)
        self.assertEquals(resp.status_code, 302)
        self.assertIn(redirected_url, resp.url)

    def test_cannot_access_if_not_staff(self):
        """
        test that the page redirects if user is not a staff user
        """
        resp = self._get_response(self.user)
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(resp.url, reverse('permission_denied'))

    def test_can_access_as_staff_user(self):
        """
        test that the page can be accessed by a staff user
        """
        resp = self._get_response(self.staff_user)
        self.assertEquals(resp.status_code, 200)


class EmailUsersTests(TestPermissionMixin, TestCase):

    def _get_response(self, user, users_to_email):
        url = reverse('studioadmin:email_users_view')
        session = _create_session()
        request = self.factory.get(url)
        request.session = session
        request.session['users_to_email'] = users_to_email
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        return email_users_view(request)

    def _post_response(self, user, users_to_email, form_data):
        url = reverse('studioadmin:email_users_view')
        session = _create_session()
        request = self.factory.post(url, form_data)
        request.session = session
        request.session['users_to_email'] = users_to_email
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        return email_users_view(request)

    def test_cannot_access_if_not_logged_in(self):
        """
        test that the page redirects if user is not logged in
        """
        url = reverse('studioadmin:email_users_view')
        resp = self.client.get(url)
        redirected_url = reverse('account_login') + "?next={}".format(url)
        self.assertEquals(resp.status_code, 302)
        self.assertIn(redirected_url, resp.url)

    def test_cannot_access_if_not_staff(self):
        """
        test that the page redirects if user is not a staff user
        """
        resp = self._get_response(self.user, [self.user.id])
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(resp.url, reverse('permission_denied'))

    def test_can_access_as_staff_user(self):
        """
        test that the page can be accessed by a staff user
        """
        resp = self._get_response(self.staff_user, [self.user.id])
        self.assertEquals(resp.status_code, 200)

    def test_users_in_context(self):
        resp = self._get_response(self.staff_user, [self.user.id])
        self.assertEqual(
            [user for user in resp.context_data['users_to_email']], [self.user]
        )

    def test_emails_sent(self):
        self._post_response(
            self.staff_user, [self.user.id],
            form_data={
                'subject': 'Test email',
                'message': 'Test message',
                'from_address': 'test@test.com'}
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.body, 'Test message')
        self.assertEqual(email.subject, '[flexibeast] Test email')
        self.assertEqual(email.to, [self.user.email])
        self.assertEqual(email.cc, [])
        self.assertEqual(email.reply_to, ['test@test.com'])

    def test_cc_email_sent(self):
        self._post_response(
            self.staff_user, [self.user.id],
            form_data={
                'subject': 'Test email',
                'message': 'Test message',
                'from_address': 'test@test.com',
                'cc': True}
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertEqual(email.cc, ['test@test.com'])
        self.assertEqual(email.reply_to, ['test@test.com'])


class ActivityLogListViewTests(TestPermissionMixin, TestCase):

    def setUp(self):
        super(ActivityLogListViewTests, self).setUp()
        # 9 logs
        # 2 logs when self.user and self.staff_user are created in setUp
        # 2 for empty cron jobs
        # 3 with log messages to test search text
        # 2 with fixed dates to test search date
        mommy.make(
            ActivityLog,
            log='email_warnings job run; no unpaid booking warnings to send'
        )
        mommy.make(
            ActivityLog,
            log='cancel_unpaid_bookings job run; no bookings to cancel'
        )
        mommy.make(ActivityLog, log='Test log message')
        mommy.make(ActivityLog, log='Test log message1 One')
        mommy.make(ActivityLog, log='Test log message2 Two')
        mommy.make(
            ActivityLog,
            timestamp=datetime(2015, 1, 1, 16, 0, tzinfo=timezone.utc),
            log='Log with test date'
        )
        mommy.make(
            ActivityLog,
            timestamp=datetime(2015, 1, 1, 4, 0, tzinfo=timezone.utc),
            log='Log with test date for search'
        )

    def _get_response(self, user, form_data={}):
        url = reverse('studioadmin:activitylog')
        session = _create_session()
        request = self.factory.get(url, form_data)
        request.session = session
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = ActivityLogListView.as_view()
        return view(request)

    def test_cannot_access_if_not_logged_in(self):
        """
        test that the page redirects if user is not logged in
        """
        url = reverse('studioadmin:activitylog')
        resp = self.client.get(url)
        redirected_url = reverse('account_login') + "?next={}".format(url)
        self.assertEquals(resp.status_code, 302)
        self.assertIn(redirected_url, resp.url)

    def test_cannot_access_if_not_staff(self):
        """
        test that the page redirects if user is not a staff user
        """
        resp = self._get_response(self.user)
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(resp.url, reverse('permission_denied'))

    def test_can_access_as_staff_user(self):
        """
        test that the page can be accessed by a staff user
        """
        resp = self._get_response(self.staff_user)
        self.assertEquals(resp.status_code, 200)

    def test_empty_cron_job_logs_filtered_by_default(self):
        resp = self._get_response(self.staff_user)
        self.assertEqual(len(resp.context_data['logs']), 7)

    def test_filter_out_empty_cron_job_logs(self):
        resp = self._get_response(
            self.staff_user, {'hide_empty_cronjobs': True}
        )
        self.assertEqual(len(resp.context_data['logs']), 7)

    def test_search_text(self):
        resp = self._get_response(self.staff_user, {
            'search_submitted': 'Search',
            'search': 'message1'})
        self.assertEqual(len(resp.context_data['logs']), 1)

        resp = self._get_response(self.staff_user, {
            'search_submitted': 'Search',
            'search': 'message'})
        self.assertEqual(len(resp.context_data['logs']), 3)

    def test_search_text_is_case_insensitive(self):
        resp = self._get_response(self.staff_user, {
            'search_submitted': 'search',
            'search': 'meSSAge1'})
        self.assertEqual(len(resp.context_data['logs']), 1)

        resp = self._get_response(self.staff_user, {
            'search_submitted': 'Search',
            'search': 'meSSage'})
        self.assertEqual(len(resp.context_data['logs']), 3)

    def test_search_date(self):
        resp = self._get_response(
            self.staff_user, {
                'search_submitted': 'Search',
                'search_date': '01-Jan-2015'
            }
        )
        self.assertEqual(len(resp.context_data['logs']), 2)

    def test_invalid_search_date_format(self):
        """
        invalid search date returns all results and a message
        """
        resp = self._get_response(
            self.staff_user, {
                'search_submitted': 'Search',
                'search_date': '01-34-2015'}
        )
        self.assertEqual(len(resp.context_data['logs']), 9)

    def test_search_date_and_text(self):
        resp = self._get_response(
            self.staff_user, {
                'search_submitted': 'Search',
                'search_date': '01-Jan-2015',
                'search': 'test date for search'}
        )
        self.assertEqual(len(resp.context_data['logs']), 1)

    def test_search_multiple_terms(self):
        """
        Search with multiple terms returns only logs that contain all terms
        """
        resp = self._get_response(self.staff_user, {
            'search_submitted': 'Search',
            'search': 'Message'})
        self.assertEqual(len(resp.context_data['logs']), 3)

        resp = self._get_response(self.staff_user, {
            'search_submitted': 'Search',
            'search': 'Message One'})
        self.assertEqual(len(resp.context_data['logs']), 1)

        resp = self._get_response(self.staff_user, {
            'search_submitted': 'Search',
            'search': 'test one'})
        self.assertEqual(len(resp.context_data['logs']), 1)

    def test_reset(self):
        """
        Test that reset button resets the search text and date and excludes
        empty cron job messages
        """
        resp = self._get_response(
            self.staff_user, {
                'search_submitted': 'Search',
                'search_date': '01-Jan-2015',
                'search': 'test date for search'
            }
        )
        self.assertEqual(len(resp.context_data['logs']), 1)

        resp = self._get_response(
            self.staff_user, {
                'search_date': '01-Jan-2015',
                'search': 'test date for search',
                'reset': 'Reset'
            }
        )
        self.assertEqual(len(resp.context_data['logs']), 7)
