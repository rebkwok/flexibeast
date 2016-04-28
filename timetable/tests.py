from model_mommy import mommy

from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse

from flex_bookings.tests.helpers import set_up_fb

from timetable.models import WeeklySession
from timetable.views import WeeklySessionListView


class TimetableViewsTests(TestCase):

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
        cls.url = reverse('timetable:timetable')

    def setUp(self):
        self.full_session = mommy.make(WeeklySession, full=True)
        self.spaces_session = mommy.make(WeeklySession, full=False)

    def test_sessions_displayed(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted([session.id for session in resp.context_data['sessions']]),
            sorted([self.full_session.id, self.spaces_session.id])
        )

    def test_toggle_spaces_button_only_shown_for_staff(self):
        resp = self.client.get(self.url)
        self.assertNotIn('toggle_spaces_button', resp.rendered_content)

        self.client.login(username=self.user.username, password='test')
        resp = self.client.get(self.url)
        self.assertNotIn('toggle_spaces_button', resp.rendered_content)

        self.client.login(username=self.staff_user.username, password='test')
        resp = self.client.get(self.url)
        self.assertIn('toggle_spaces_button', resp.rendered_content)

    def test_toggle_spaces_only_allowed_for_staff(self):
        self.assertTrue(self.full_session.full)
        toggle_url = reverse(
            'timetable:toggle_spaces', args=[self.full_session.id]
        )

        resp = self.client.get(toggle_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(
            reverse('account_login') + "?next={}".format(toggle_url),
            resp.url
        )
        self.full_session.refresh_from_db()
        self.assertTrue(self.full_session.full)

        self.client.login(username=self.user.username, password='test')
        resp = self.client.get(toggle_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(
            reverse('permission_denied'),
            resp.url
        )
        self.full_session.refresh_from_db()
        self.assertTrue(self.full_session.full)

        self.client.login(username=self.staff_user.username, password='test')
        resp = self.client.get(toggle_url)
        self.assertEqual(resp.status_code, 200)
        self.full_session.refresh_from_db()
        self.assertFalse(self.full_session.full)
