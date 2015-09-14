from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.utils import timezone
from model_mommy import mommy
from datetime import datetime
from mock import patch
from flex_bookings.views import EventDetailView
from flex_bookings.tests.helpers import set_up_fb


class EventDetailContextTests(TestCase):
    """
    Test that context helpers are passing correct contexts
    """

    def setUp(self):
        set_up_fb()
        self.factory = RequestFactory()
        self.past_event = mommy.make_recipe(
            'flex_bookings.past_event', booking_open=True
        )
        self.paid_event = mommy.make_recipe(
            'flex_bookings.future_EV', cost=10, booking_open=True
        )

        self.user = mommy.make_recipe('flex_bookings.user')

        self.CONTEXT_OPTIONS = {
            'payment_text_no_cost':         "There is no cost associated with "
                                            "this workshop.",
            'booking_info_text_not_booked': "",
            'booking_info_text_not_open':   "Bookings are not open for this "
                                            "workshop.",
            'booking_info_text_booked':     "You have booked for this workshop.",
            'booking_info_text_full':       "This workshop is now full.",
            'booking_info_payment_date_past': "Bookings for this workshop are now "
                                              "closed."
        }
        self.CONTEXT_FLAGS = {
            'booked': True,
            'past': True
        }

    def _get_response(self, user, event, ev_type):
        url = reverse('flexbookings:event_detail', args=[event.slug])
        request = self.factory.get(url)
        request.user = user
        view = EventDetailView.as_view()
        return view(request, slug=event.slug, ev_type=ev_type)

    def test_past_event(self):
        """
        Test correct context returned for a past event
        """
        self.past_event.payment_info = "pay please"
        self.past_event.save()
        resp = self._get_response(self.user, self.past_event, 'event')
        # user is not booked; include book button, payment text etc is still in
        # context; template handles the display
        self.assertFalse('booked' in resp.context_data.keys())
        self.assertTrue('past' in resp.context_data.keys())
        self.assertEquals(
            resp.context_data['payment_text'],
            self.past_event.payment_info
        )

        resp.render()
        # check the content for the past text
        self.assertIn("This workshop is now past.", str(resp.content))
        # and check that the payment_text is not there
        self.assertNotIn(resp.context_data['payment_text'], str(resp.content))

    def test_event_without_cost(self):
        """
        Test correct context returned for an event without associated cost
        """
        event = mommy.make_recipe(
            'flex_bookings.future_WS',
            cost=0,
            booking_open=True,
        )

        resp = self._get_response(self.user, event, 'event')
        self.assertEquals(
            resp.context_data['payment_text'],
            self.CONTEXT_OPTIONS['payment_text_no_cost']
        )

    def test_booking_not_open(self):
        """
        redirects to "booking not open" page
        """
        event = mommy.make_recipe(
            'flex_bookings.future_WS',
            booking_open=False,
        )
        resp = self._get_response(self.user, event, 'event')
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(
            resp.url,
            reverse('flexbookings:not_open', kwargs={'event_slug': event.slug})
        )

    @patch('flex_bookings.context_helpers.timezone')
    @patch('flex_bookings.models.timezone')
    def test_event_with_payment_due_date(self, models_mock_tz, helpers_mock_tz):
        """
        Test correct context returned for an event with payment due date
        """
        models_mock_tz.now.return_value = datetime(
            2015, 2, 1, tzinfo=timezone.utc
        )
        helpers_mock_tz.now.return_value = datetime(
            2015, 2, 1, tzinfo=timezone.utc
        )
        event = mommy.make_recipe(
            'flex_bookings.future_WS',
            cost=10,
            booking_open=True,
            payment_due_date=datetime(2015, 2, 2, tzinfo=timezone.utc)
        )
        resp = self._get_response(self.user, event, 'event')

        self.assertEquals(resp.context_data['booking_info_text'],
                          self.CONTEXT_OPTIONS['booking_info_text_not_booked'])
        self.assertTrue(resp.context_data['bookable'])

    @patch('flex_bookings.models.timezone')
    def test_event_with_past_payment_due_date(self, mock_tz):
        """
        Test correct context returned for an event with payment due date
        """
        mock_tz.now.return_value = datetime(2015, 2, 1, tzinfo=timezone.utc)
        event = mommy.make_recipe(
            'flex_bookings.future_WS',
            cost=10,
            booking_open=True,
            payment_due_date=datetime(2015, 1, 31, tzinfo=timezone.utc)
        )
        resp = self._get_response(self.user, event, 'event')

        self.assertEquals(resp.context_data['booking_info_text'],
                          self.CONTEXT_OPTIONS['booking_info_payment_date_past'])
        self.assertFalse(resp.context_data['bookable'])

    def test_lesson_and_event_format(self):
        """
        Test correct context returned for lessons and events
        """
        event = mommy.make_recipe(
            'flex_bookings.future_WS', name='Wshop', cost=10,
            booking_open=True,)

        lesson = mommy.make_recipe(
            'flex_bookings.future_EV', name='Lesson',
            cost=10, booking_open=True,
        )

        resp = self._get_response(self.user, event, 'event')
        self.assertEquals(resp.context_data['type'], 'workshop')

        url = reverse('flexbookings:lesson_detail', args=[lesson.slug])
        request = self.factory.get(url)
        request.user = self.user
        view = EventDetailView.as_view()
        resp = view(request, slug=lesson.slug, ev_type='lesson')
        self.assertEquals(resp.context_data['type'], 'lesson')
