import random

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse

from datetime import timedelta, datetime
from mock import patch
from model_mommy import mommy

from flex_bookings.models import Event, Block, Booking, BookingError, EventType

now = timezone.now()


class EventTests(TestCase):

    def setUp(self):
        self.event = mommy.make_recipe(
            'flex_bookings.future_EV',
            booking_open=True
        )

    def tearDown(self):
        del self.event

    def test_bookable_with_no_payment_date(self):
        """
        Test that event bookable logic returns correctly
        """
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True
        )
        self.assertTrue(event.bookable())

    @patch('flex_bookings.models.timezone')
    def test_bookable_with_payment_dates(self, mock_tz):
        """
        Test that event bookable logic returns correctly for events with
        payment due dates
        """
        mock_tz.now.return_value = datetime(2015, 2, 1, tzinfo=timezone.utc)
        event = mommy.make_recipe(
            'flex_bookings.future_EV',
            cost=10,
            booking_open=True,
            payment_due_date=datetime(2015, 2, 2, tzinfo=timezone.utc))

        self.assertTrue(event.bookable())

        event1 = mommy.make_recipe(
            'flex_bookings.future_EV',
            cost=10,
            booking_open=True,
            payment_due_date=datetime(2015, 1, 31, tzinfo=timezone.utc)
        )
        self.assertFalse(event1.bookable())


    def test_event_pre_save(self):
        """
        Test that an event with no cost has correct fields set
        """
        # if an event is created with 0 cost, the following fields are set to
        # False/None/""
        # advance_payment_required, payment_due_date

        ev = mommy.make_recipe('flex_bookings.future_EV', cost=7)
        self.assertTrue(ev.advance_payment_required)
        #change cost to 0
        ev.cost = 0
        ev.save()
        self.assertFalse(ev.advance_payment_required)

    def test_absolute_url(self):
        self.assertEqual(
            self.event.get_absolute_url(),
            reverse(
                'flexbookings:event_detail', kwargs={'slug': self.event.slug}
            )
        )

    def test_str(self):
        event = mommy.make_recipe(
            'flex_bookings.past_event',
            name='Test event',
            date=datetime(2015, 1, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(str(event), 'Test event - 01 Jan 2015, 00:00')


class BookingTests(TestCase):

    def setUp(self):
        mommy.make_recipe('flex_bookings.user', _quantity=15)
        self.users = User.objects.all()
        self.event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True, max_participants=20,
            cost=0
        )
        self.event_with_cost = mommy.make_recipe('flex_bookings.future_EV',
                                                 booking_open=True,
                                                 advance_payment_required=True,
                                                 cost=10)

    def tearDown(self):
        del self.users
        del self.event

    def test_event_spaces_left(self):
        """
        Test that spaces left is calculated correctly
        """

        self.assertEqual(self.event.max_participants, 20)
        self.assertEqual(self.event.spaces_left(), 20)

        for user in self.users:
            mommy.make_recipe('flex_bookings.booking', user=user, event=self.event)

        self.assertEqual(self.event.spaces_left(), 5)

    def test_space_confirmed_no_cost(self):
        """
        Test that a booking for an event with no cost is automatically confirmed
        """

        booking = mommy.make_recipe('flex_bookings.booking',
                                    user=self.users[0], event=self.event)
        self.assertTrue(booking.space_confirmed())

    def test_confirm_space(self):
        """
        Test confirm_space method on a booking
        """

        booking = mommy.make_recipe('flex_bookings.booking',
                                    user=self.users[0],
                                    event=self.event_with_cost)
        self.assertFalse(booking.space_confirmed())
        self.assertFalse(booking.paid)
        self.assertFalse(booking.payment_confirmed)

        booking.confirm_space()
        self.assertTrue(booking.space_confirmed())
        self.assertTrue(booking.paid)
        self.assertTrue(booking.payment_confirmed)

    def test_space_confirmed_advance_payment_req(self):
        """
        Test space confirmed requires manual confirmation for events with
        advance payments required
        """
        event = self.event_with_cost
        booking = mommy.make_recipe('flex_bookings.booking',
                                    user=self.users[0],
                                    event=event)
        self.assertFalse(booking.space_confirmed())

        booking.confirm_space()
        self.assertTrue(booking.space_confirmed())

    def test_space_confirmed_advance_payment_not_required(self):
        """
        Test space confirmed automatically for events with advance payments
        not required
        """
        event = self.event_with_cost
        event.advance_payment_required = False

        booking = mommy.make_recipe('flex_bookings.booking',
                                    user=self.users[0],
                                    event=event)
        self.assertTrue(booking.space_confirmed())

    def test_date_payment_confirmed(self):
        """
        Test autopopulating date payment confirmed.
        """
        booking = mommy.make_recipe('flex_bookings.booking',
                                    user=self.users[0],
                                    event=self.event_with_cost)
        # booking is created with no payment confirmed date
        self.assertFalse(booking.date_payment_confirmed)

        booking.payment_confirmed = True
        booking.save()
        self.assertTrue(booking.date_payment_confirmed)

    def test_cancelled_booking_is_no_longer_confirmed(self):
        booking = mommy.make_recipe('flex_bookings.booking',
                                    user=self.users[0],
                                    event=self.event_with_cost)
        booking.confirm_space()
        self.assertTrue(booking.space_confirmed())

        booking.status = 'CANCELLED'
        booking.save()
        self.assertFalse(booking.space_confirmed())

    def test_str(self):
        booking = mommy.make_recipe(
            'flex_bookings.booking',
            event=mommy.make_recipe('flex_bookings.future_EV', name='Test event'),
            user=mommy.make_recipe('flex_bookings.user', username='Test user'),
            )
        self.assertEqual(str(booking), 'Test event - Test user')

    def test_booking_full_event(self):
        """
        Test that attempting to create new booking for full event raises
        BookingError
        """
        self.event_with_cost.max_participants = 3
        self.event_with_cost.save()
        mommy.make_recipe(
            'flex_bookings.booking', event=self.event_with_cost, _quantity=3
        )
        with self.assertRaises(BookingError):
            Booking.objects.create(
                event=self.event_with_cost, user=self.users[0]
            )

    def test_reopening_booking_full_event(self):
        """
        Test that attempting to reopen a cancelled booking for now full event
        raises BookingError
        """
        self.event_with_cost.max_participants = 3
        self.event_with_cost.save()
        user = self.users[0]
        booking = mommy.make_recipe(
            'flex_bookings.booking', event=self.event_with_cost, user=user,
            status='CANCELLED'
        )
        mommy.make_recipe(
            'flex_bookings.booking', event=self.event_with_cost, _quantity=3
        )
        with self.assertRaises(BookingError):
            booking.status = 'OPEN'
            booking.save()

    def test_can_create_cancelled_booking_for_full_event(self):
        """
        Test that attempting to create new cancelled booking for full event
        does not raise error
        """
        self.event_with_cost.max_participants = 3
        self.event_with_cost.save()
        mommy.make_recipe(
            'flex_bookings.booking', event=self.event_with_cost, _quantity=3
        )
        Booking.objects.create(
            event=self.event_with_cost, user=self.users[0], status='CANCELLED'
        )
        self.assertEqual(
            Booking.objects.filter(event=self.event_with_cost).count(), 4
        )


class BlockTests(TestCase):

    def setUp(self):
        self.block = mommy.make_recipe('flex_bookings.block')

    def tearDown(self):
        del self.block


    @patch.object(timezone, 'now',
                  return_value=datetime(2015, 2, 1, tzinfo=timezone.utc))
    def test_block_is_past(self, mock_now):
        """
        Test that block is_past property returns correctly
        """
        # 5 past events attached to block
        events = mommy.make_recipe(
            'flex_bookings.future_EV',
            _quantity=5
        )
        for event in events:
            event.date = timezone.now() - timedelta(days=random.randint(1, 10))
            event.save()

        for event in events:
            self.block.events.add(event)

        # check events are ordered correctly by date
        self.assertTrue(
            self.block.events.last().date > self.block.events.first().date
        )
        self.assertTrue(self.block.is_past)

    @patch.object(timezone, 'now',
                  return_value=datetime(2015, 2, 1, tzinfo=timezone.utc))
    def test_block_is_not_past(self, mock_now):
        """
        Test that block is_past property returns correctly.  If any event
        attached to the block is in the future, is_past=False
        """
        # 5 past events attached to block
        past_events = mommy.make_recipe(
            'flex_bookings.future_EV',
            _quantity=5
        )
        for event in past_events:
            event.date = timezone.now() - timedelta(days=random.randint(1, 10))
            event.save()
        # 1 future events attached to block
        future_event = mommy.make_recipe(
            'flex_bookings.future_EV',
            date=timezone.now() + timedelta(days=1),
        )
        events = past_events + [future_event]

        for event in events:
            self.block.events.add(event)

        # check events are ordered correctly by date
        self.assertTrue(
            self.block.events.last().date > self.block.events.first().date
        )
        self.assertTrue(
            self.block.events.last().date > timezone.now()
        )

        self.assertFalse(self.block.is_past)

    def test_open_booking_on_block_opens_event_booking(self):
        """
        Saving a block as booking_open makes booking open on all attached
        events too
        """
        events = mommy.make_recipe(
            'flex_bookings.future_EV',
            _quantity=5
        )
        for event in events:
            event.date = timezone.now() + timedelta(days=random.randint(1, 10))
            event.save()
            self.block.events.add(event)

        # events are created with booking_open=False by default
        self.assertEqual(set([event.booking_open for event in events]), {False})
        # blocks are also created with booking_open=False
        self.assertFalse(self.block.booking_open)

        # open booking on the block
        self.block.booking_open = True
        self.block.save()

        for event in events:
            event.refresh_from_db()
        self.assertEqual(set([event.booking_open for event in events]), {True})

    def test_individual_booking_date(self):
        """
        Saving a block as sets the individual_booking_date to the beginning of
        the chosen day
        """
        date = datetime(2015, 2, 1, 18, 0, tzinfo=timezone.utc)
        self.block.individual_booking_date = date
        self.block.save()

        self.assertEqual(
            self.block.individual_booking_date,
            datetime(2015, 2, 1, 0, 0, tzinfo=timezone.utc)
        )


class EventTypeTests(TestCase):

    def test_str_class(self):
        evtype = mommy.make_recipe('flex_bookings.event_type_YC', subtype="class subtype")
        self.assertEqual(str(evtype), 'Class - class subtype')

    def test_str_event(self):
        evtype = mommy.make_recipe('flex_bookings.event_type_WS', subtype="event subtype")
        self.assertEqual(str(evtype), 'Event - event subtype')
