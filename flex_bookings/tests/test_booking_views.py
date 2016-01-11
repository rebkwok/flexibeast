from datetime import datetime, timedelta
from mock import Mock, patch
from model_mommy import mommy

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone
from django.contrib.auth.models import Permission

from flex_bookings.models import Event, Booking, Block
from flex_bookings.views import BookingListView, BookingHistoryListView, \
    BookingCreateView, BookingDeleteView, duplicate_booking, fully_booked, \
    cancellation_period_past
from flex_bookings.tests.helpers import set_up_fb, _create_session

class BookingListViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')
        # name events explicitly to avoid invoice id conflicts in tests
        # (should never happen in reality since the invoice id is built from
        # (event name initials and datetime)
        self.events = [
            mommy.make_recipe('flex_bookings.future_EV',  name="First Event"),
            mommy.make_recipe('flex_bookings.future_EV',  name="Scnd Event"),
            mommy.make_recipe('flex_bookings.future_EV',  name="Third Event")
        ]
        future_bookings = [mommy.make_recipe(
            'flex_bookings.booking', user=self.user,
            event=event) for event in self.events]
        mommy.make_recipe('flex_bookings.past_booking', user=self.user)

    def _get_response(self, user):
        url = reverse('flexbookings:bookings')
        request = self.factory.get(url)
        request.user = user
        view = BookingListView.as_view()
        return view(request)

    def test_login_required(self):
        """
        test that page redirects if there is no user logged in
        """
        url = reverse('flexbookings:bookings')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_booking_list(self):
        """
        Test that only future bookings are listed)
        """
        resp = self._get_response(self.user)

        self.assertEquals(Booking.objects.all().count(), 4)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context_data['bookings'].count(), 3)

    def test_booking_list_by_user(self):
        """
        Test that only bookings for this user are listed
        """
        another_user = mommy.make_recipe('flex_bookings.user')
        mommy.make_recipe(
            'flex_bookings.booking', user=another_user, event=self.events[0]
        )
        # check there are now 5 bookings
        self.assertEquals(Booking.objects.all().count(), 5)
        resp = self._get_response(self.user)

        # event listing should still only show this user's future bookings
        self.assertEquals(resp.context_data['bookings'].count(), 3)

    def test_cancelled_booking_not_showing_in_booking_list(self):
        """
        Test that all future bookings for this user are listed
        """
        ev = mommy.make_recipe('flex_bookings.future_EV', name="future event")
        mommy.make_recipe(
            'flex_bookings.booking', user=self.user, event=ev,
            status='CANCELLED'
        )
        # check there are now 5 bookings (3 future, 1 past, 1 cancelled)
        self.assertEquals(Booking.objects.all().count(), 5)
        resp = self._get_response(self.user)

        # booking listing should show this user's future bookings,
        # including the cancelled one
        self.assertEquals(resp.context_data['bookings'].count(), 4)


class BookingHistoryListViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')
        event = mommy.make_recipe('flex_bookings.future_EV')
        self.booking = mommy.make_recipe(
            'flex_bookings.booking', user=self.user, event=event
        )
        self.past_booking = mommy.make_recipe(
            'flex_bookings.past_booking', user=self.user
        )

    def _get_response(self, user):
        url = reverse('flexbookings:booking_history')
        request = self.factory.get(url)
        request.user = user
        view = BookingHistoryListView.as_view()
        return view(request)

    def test_login_required(self):
        """
        test that page redirects if there is no user logged in
        """
        url = reverse('flexbookings:booking_history')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_booking_history_list(self):
        """
        Test that only past bookings are listed)
        """
        resp = self._get_response(self.user)

        self.assertEquals(Booking.objects.all().count(), 2)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context_data['bookings'].count(), 1)

    def test_booking_history_list_by_user(self):
        """
        Test that only past booking for this user are listed
        """
        another_user = mommy.make_recipe('flex_bookings.user')
        mommy.make_recipe(
            'flex_bookings.booking', user=another_user, event=self.past_booking.event
        )
        # check there are now 3 bookings
        self.assertEquals(Booking.objects.all().count(), 3)
        resp = self._get_response(self.user)

        #  listing should still only show this user's past bookings
        self.assertEquals(resp.context_data['bookings'].count(), 1)


class BookingCreateViewTests(TestCase):
    def setUp(self):
        set_up_fb()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')

    def _post_response(self, user, event, form_data={}):
        url = reverse('flexbookings:book_event', kwargs={'event_slug': event.slug})
        store = _create_session()
        form_data['event'] = event.id
        request = self.factory.post(url, form_data)
        request.session = store
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = BookingCreateView.as_view()
        return view(request, event_slug=event.slug)

    def _get_response(self, user, event):
        url = reverse('flexbookings:book_event', kwargs={'event_slug': event.slug})
        store = _create_session()
        request = self.factory.get(url, {'event': event.id})
        request.session = store
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = BookingCreateView.as_view()
        return view(request, event_slug=event.slug)

    def test_get_create_booking_page(self):
        """
        Get the booking page with the event context
        """
        event = mommy.make_recipe('flex_bookings.future_EV', max_participants=3)
        resp = self._get_response(self.user, event)
        self.assertEqual(resp.context_data['event'], event)

    def test_create_booking(self):
        """
        Test creating a booking
        """
        event = mommy.make_recipe('flex_bookings.future_EV', max_participants=3)
        self.assertEqual(Booking.objects.all().count(), 0)
        self._post_response(self.user, event)
        self.assertEqual(Booking.objects.all().count(), 1)

    def test_cannot_create_duplicate_booking(self):
        """
        Test trying to create a duplicate booking redirects
        """
        event = mommy.make_recipe('flex_bookings.future_EV', max_participants=3)

        resp = self._post_response(self.user, event)
        booking_id = Booking.objects.all()[0].id
        booking_url = reverse('flexbookings:bookings')
        self.assertEqual(resp.url, booking_url)

        resp1 = self._get_response(self.user, event)
        duplicate_url = reverse('flexbookings:duplicate_booking',
                                kwargs={'event_slug': event.slug}
                                )
        # test redirect to duplicate booking url
        self.assertEqual(resp1.url, duplicate_url)

    def test_cannot_book_for_full_event(self):
        """
        Test trying to create a duplicate booking redirects
        """
        event = mommy.make_recipe('flex_bookings.future_EV', max_participants=3)
        users = mommy.make_recipe('flex_bookings.user', _quantity=3)
        for user in users:
            mommy.make_recipe('flex_bookings.booking', event=event, user=user)
        # check event is full
        self.assertEqual(event.spaces_left(), 0)

        # try to book for event
        resp = self._get_response(self.user, event)
        # test redirect to duplicate booking url
        self.assertEqual(
            resp.url,
            reverse(
                'flexbookings:fully_booked',
                kwargs={'event_slug': event.slug}
            )
        )

    def test_cancelled_booking_can_be_rebooked(self):
        """
        Test can load create booking page with a cancelled booking
        """

        event = mommy.make_recipe('flex_bookings.future_EV')
        # book for event
        resp = self._post_response(self.user, event)

        booking = Booking.objects.get(user=self.user, event=event)
        # cancel booking
        booking.status = 'CANCELLED'
        booking.save()

        # try to book again
        resp = self._get_response(self.user, event)
        self.assertEqual(resp.status_code, 200)

    def test_rebook_cancelled_booking(self):
        """
        Test can rebook a cancelled booking
        """

        event = mommy.make_recipe('flex_bookings.future_EV')
        # book for event
        resp = self._post_response(self.user, event)

        booking = Booking.objects.get(user=self.user, event=event)
        # cancel booking
        booking.status = 'CANCELLED'
        booking.save()

        # try to book again
        resp = self._post_response(self.user, event)
        booking = Booking.objects.get(user=self.user, event=event)
        self.assertEqual('OPEN', booking.status)

    def test_rebook_cancelled_booking_still_paid(self):

        """
        Test rebooking a cancelled booking still marked as paid makes
        booking status open but does not confirm space
        """
        event = mommy.make_recipe('flex_bookings.future_EV')
        booking = mommy.make_recipe(
            'flex_bookings.booking', event=event, user=self.user, status='CANCELLED'
        )

        # try to book again
        resp = self._post_response(self.user, event)
        booking = Booking.objects.get(user=self.user, event=event)
        self.assertEqual('OPEN', booking.status)
        self.assertFalse(booking.payment_confirmed)


class BookingErrorRedirectPagesTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')

    def test_duplicate_booking(self):
        """
        Get the duplicate booking page with the event context
        """
        event = mommy.make_recipe('flex_bookings.future_EV')
        url = reverse(
            'flexbookings:duplicate_booking', kwargs={'event_slug': event.slug}
        )
        session = _create_session()
        request = self.factory.get(url)
        request.session = session
        request.user = self.user
        messages = FallbackStorage(request)
        request._messages = messages
        resp = duplicate_booking(request, event.slug)
        self.assertIn(event.name, str(resp.content))

    def test_fully_booked(self):
        """
        Get the fully booked page with the event context
        """
        event = mommy.make_recipe('flex_bookings.future_EV')
        url = reverse(
            'flexbookings:fully_booked', kwargs={'event_slug': event.slug}
        )
        session = _create_session()
        request = self.factory.get(url)
        request.session = session
        request.user = self.user
        messages = FallbackStorage(request)
        request._messages = messages
        resp = fully_booked(request, event.slug)
        self.assertIn(event.name, str(resp.content))

    def test_cannot_cancel_after_cancellation_period(self):
        """
        Get the cannot cancel page with the event context
        """
        event = mommy.make_recipe('flex_bookings.future_EV')
        url = reverse(
            'flexbookings:cancellation_period_past',
            kwargs={'event_slug': event.slug}
        )
        session = _create_session()
        request = self.factory.get(url)
        request.session = session
        request.user = self.user
        messages = FallbackStorage(request)
        request._messages = messages
        resp = cancellation_period_past(request, event.slug)
        self.assertIn(event.name, str(resp.content))


class BookingDeleteViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')

    def _get_response(self, user, booking):
        url = reverse('flexbookings:delete_booking', args=[booking.id])
        session = _create_session()
        request = self.factory.delete(url)
        request.session = session
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = BookingDeleteView.as_view()
        return view(request, pk=booking.id)

    def test_get_delete_booking_page(self):
        """
        Get the delete booking page with the event context
        """
        event = mommy.make_recipe('flex_bookings.future_EV')
        booking = mommy.make_recipe('flex_bookings.booking', event=event, user=self.user)
        url = reverse(
            'flexbookings:delete_booking', args=[booking.id]
        )
        session = _create_session()
        request = self.factory.get(url)
        request.session = session
        request.user = self.user
        messages = FallbackStorage(request)
        request._messages = messages
        view = BookingDeleteView.as_view()
        resp = view(request, pk=booking.id)
        self.assertEqual(resp.context_data['event'], event)

    def test_cancel_booking(self):
        """
        Test deleting a booking
        """
        event = mommy.make_recipe('flex_bookings.future_EV')
        booking = mommy.make_recipe('flex_bookings.booking', event=event,
                                    user=self.user)
        self.assertEqual(Booking.objects.all().count(), 1)
        self._get_response(self.user, booking)
        # after cancelling, the booking is still there, but status has changed
        self.assertEqual(Booking.objects.all().count(), 1)
        booking = Booking.objects.get(id=booking.id)
        self.assertEqual('CANCELLED', booking.status)

    def test_cancelling_only_this_booking(self):
        """
        Test cancelling a booking when user has more than one
        """
        events = mommy.make_recipe('flex_bookings.future_EV', _quantity=3)

        for event in events:
            mommy.make_recipe('flex_bookings.booking', user=self.user, event=event)

        self.assertEqual(Booking.objects.all().count(), 3)
        booking = Booking.objects.all()[0]
        self._get_response(self.user, booking)
        self.assertEqual(Booking.objects.all().count(), 3)
        cancelled_bookings = Booking.objects.filter(status='CANCELLED')
        self.assertEqual([cancelled.id for cancelled in cancelled_bookings],
                         [booking.id])

    def test_cancelling_booking_sets_payment_confirmed_to_False(self):
        event_with_cost = mommy.make_recipe('flex_bookings.future_EV', cost=10)
        booking = mommy.make_recipe('flex_bookings.booking', user=self.user,
                                    event=event_with_cost)
        booking.confirm_space()
        self.assertTrue(booking.payment_confirmed)
        self._get_response(self.user, booking)

        booking = Booking.objects.get(user=self.user,
                                      event=event_with_cost)
        self.assertEqual('CANCELLED', booking.status)
        self.assertFalse(booking.payment_confirmed)

    @patch("flex_bookings.views.timezone")
    def test_cannot_cancel_after_cancellation_period(self, mock_tz):
        """
        Test trying to cancel after cancellation period
        """
        mock_tz.now.return_value = datetime(2015, 2, 1, tzinfo=timezone.utc)
        event = mommy.make_recipe(
            'flex_bookings.future_EV',
            date=datetime(2015, 2, 2, tzinfo=timezone.utc),
            cancellation_period=48
        )
        booking = mommy.make_recipe(
            'flex_bookings.booking', event=event, user=self.user
        )

        url = reverse('flexbookings:delete_booking', args=[booking.id])
        session = _create_session()
        request = self.factory.get(url)
        request.session = session
        request.user = self.user
        messages = FallbackStorage(request)
        request._messages = messages
        view = BookingDeleteView.as_view()
        resp = view(request, pk=booking.id)

        cannot_cancel_url = reverse('flexbookings:cancellation_period_past',
                                kwargs={'event_slug': event.slug}
        )
        # test redirect to cannot cancel url
        self.assertEqual(302, resp.status_code)
        self.assertEqual(resp.url, cannot_cancel_url)


