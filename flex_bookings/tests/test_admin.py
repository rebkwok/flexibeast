from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from model_mommy import mommy
from flex_bookings.models import Event, Booking
import flex_bookings.admin as admin


class EventAdminTests(TestCase):

    def test_event_date_list_filter(self):
        past_event = mommy.make_recipe('flex_bookings.past_event', name='past')
        future_event = mommy.make_recipe('flex_bookings.future_EV', name='future')

        filter = admin.EventDateListFilter(
            None, {'date': 'past'}, Event, admin.EventAdmin
        )
        event = filter.queryset(None, Event.objects.all())[0]
        self.assertEqual(event.name, 'past')

        filter = admin.EventDateListFilter(
            None, {'date': 'upcoming'}, Event, admin.EventAdmin
        )
        event = filter.queryset(None, Event.objects.all())[0]
        self.assertEqual(event.name, 'future')


class BookingAdminTests(TestCase):

    def setUp(self):
        self.user = mommy.make_recipe(
            'flex_bookings.user', first_name="Test", last_name="User"
        )

    def test_booking_date_list_filter(self):
        past_event = mommy.make_recipe('flex_bookings.past_event', name='past')
        future_event = mommy.make_recipe('flex_bookings.future_EV', name='future')
        mommy.make_recipe('flex_bookings.booking', user=self.user, event=past_event)
        mommy.make_recipe('flex_bookings.booking', user=self.user, event=future_event)

        filter = admin.BookingDateListFilter(
            None, {'event__date': 'past'}, Booking, admin.BookingAdmin
        )
        booking = filter.queryset(None, Booking.objects.all())[0]
        self.assertEqual(booking.event.name, 'past')

        filter = admin.BookingDateListFilter(
            None, {'event__date': 'upcoming'}, Booking, admin.BookingAdmin
        )
        booking = filter.queryset(None, Booking.objects.all())[0]
        self.assertEqual(booking.event.name, 'future')

    def test_booking_admin_display(self):
        event = mommy.make_recipe('flex_bookings.future_EV', cost=6)

        booking = mommy.make_recipe(
            'flex_bookings.booking', user=self.user, event=event
        )

        booking_admin = admin.BookingAdmin(Booking, AdminSite())
        booking_query = booking_admin.get_queryset(None)[0]

        self.assertEqual(
            booking_admin.get_date(booking_query), booking.event.date
        )
        self.assertEqual(
            booking_admin.get_user_first_name(booking_query), 'Test'
        )
        self.assertEqual(
            booking_admin.get_user_last_name(booking_query), 'User'
        )
        self.assertEqual(booking_admin.event_name(booking_query), event.name)


