from model_mommy import mommy

from datetime import time

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core import management
from django.test import TestCase

from flex_bookings.tests.helpers import set_up_fb

from timetable.models import Location, Session, WeeklySession


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


class TimetableViewsTests(TestMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super(TimetableViewsTests, cls).setUpTestData()
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


class TimeTableModelTests(TestCase):

    def test_session_str(self):
        session = mommy.make(
            Session, name="Test", day=WeeklySession.MON, time=time(19, 0)
        )
        self.assertEqual(
            str(session), "Monday 19:00 - Test"
        )

    def test_weekly_session_str(self):
        wsession = mommy.make(
            WeeklySession, name="Test", day=WeeklySession.MON, time=time(19, 0)
        )
        self.assertEqual(
            str(wsession), "Test - Monday 19:00"
        )

    def test_location_str(self):
        location = mommy.make(
            Location, short_name="test", full_name="a test location"
        )
        self.assertEqual(str(location), 'test')

    def test_session_fields_set_on_save(self):
        """
        If no cost, adv payment req is set to False
        """
        session = mommy.make(
            Session, cost=0, advance_payment_required=True,
        )
        self.assertFalse(session.advance_payment_required)


class TimetableManagementTests(TestMixin, TestCase):

    def test_create_locations_and_weekly_sessions(self):
        self.assertFalse(Location.objects.exists())
        self.assertFalse(WeeklySession.objects.exists())

        management.call_command('create_locations_and_weekly_sessions')
        self.assertTrue(Location.objects.exists())
        self.assertTrue(WeeklySession.objects.exists())
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(WeeklySession.objects.count(), 5)

    def test_locations_and_weekly_sessions_not_recreated(self):
        management.call_command('create_locations_and_weekly_sessions')
        self.assertTrue(Location.objects.exists())
        self.assertTrue(WeeklySession.objects.exists())
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(WeeklySession.objects.count(), 5)
        session_ids = [sess.id for sess in WeeklySession.objects.all()]

        # call again; counts stay the same
        management.call_command('create_locations_and_weekly_sessions')
        self.assertTrue(Location.objects.exists())
        self.assertTrue(WeeklySession.objects.exists())
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(WeeklySession.objects.count(), 5)
        session_ids1 = [sess.id for sess in WeeklySession.objects.all()]

        # sessions are the same,  not created again
        self.assertEqual(sorted(session_ids), sorted(session_ids1))

    def test_existing_sessions_restored_to_default(self):
        management.call_command('create_locations_and_weekly_sessions')

        # get the Friday session
        fri_sess = WeeklySession.objects.get(
            day=WeeklySession.FRI, time=time(11, 0)
        )
        self.assertEqual(fri_sess.description, '')
        fri_sess.description = 'new'
        fri_sess.save()

        self.assertEqual(fri_sess.description, 'new')
        management.call_command('create_locations_and_weekly_sessions')

        fri_sess.refresh_from_db()
        # description has been set back to default
        self.assertEqual(fri_sess.description, '')

    def test_create_timetable_sessions(self):
        self.assertFalse(Session.objects.exists())
        management.call_command('create_timetable')

        self.assertTrue(Session.objects.exists())
        self.assertEqual(Session.objects.count(), 3)
