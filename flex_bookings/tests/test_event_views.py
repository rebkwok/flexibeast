from model_mommy import mommy

from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import Permission

from flex_bookings.models import Event, Booking
from flex_bookings.views import EventListView, EventDetailView
from flex_bookings.tests.helpers import set_up_fb


class EventListViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        mommy.make_recipe(
            'flex_bookings.future_WS', booking_open=True, _quantity=3
        )
        mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True, _quantity=6
        )
        self.user = mommy.make_recipe('flex_bookings.user')

    def _get_response(self, user, ev_type):
        url = reverse('flexbookings:events')
        request = self.factory.get(url)
        request.user = user
        view = EventListView.as_view()
        return view(request, ev_type=ev_type)

    def test_event_list(self):
        """
        Test that only events are listed (workshops and other events)
        """
        url = reverse('flexbookings:events')
        resp = self.client.get(url)

        self.assertEquals(Event.objects.all().count(), 9)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context['events'].count(), 3)

    def test_event_list_past_event(self):
        """
        Test that past events is not listed
        """
        mommy.make_recipe('flex_bookings.past_event')
        # check there are now 4 events
        self.assertEquals(Event.objects.all().count(), 10)
        url = reverse('flexbookings:events')
        resp = self.client.get(url)

        # event listing should still only show future events
        self.assertEquals(resp.context['events'].count(), 3)

    def test_event_list_with_anonymous_user(self):
        """
        Test that no booked_events in context
        """
        url = reverse('flexbookings:events')
        resp = self.client.get(url)

        # event listing should still only show future events
        self.assertFalse('booked_events' in resp.context)

    def test_event_list_with_logged_in_user(self):
        """
        Test that booked_events in context
        """
        resp = self._get_response(self.user, 'events')
        self.assertTrue('booked_events' in resp.context_data)

    def test_event_list_with_booked_events(self):
        """
        test that booked events are shown on listing
        """
        resp = self._get_response(self.user, 'events')
        # check there are no booked events yet
        booked_events = [event for event in resp.context_data['booked_events']]
        self.assertEquals(len(resp.context_data['booked_events']), 0)

        # create a booking for this user
        booked_event = Event.objects.all()[0]
        mommy.make_recipe('flex_bookings.booking', user=self.user, event=booked_event)
        resp = self._get_response(self.user, 'events')
        booked_events = [event for event in resp.context_data['booked_events']]
        self.assertEquals(len(booked_events), 1)
        self.assertTrue(booked_event in booked_events)

    def test_event_list_shows_only_current_user_bookings(self):
        """
        Test that only user's booked events are shown as booked
        """
        events = Event.objects.all()
        event1 = events[0]
        event2 = events[1]

        resp = self._get_response(self.user, 'events')
        # check there are no booked events yet
        booked_events = [event for event in resp.context_data['booked_events']]
        self.assertEquals(len(resp.context_data['booked_events']), 0)

        # create booking for this user
        mommy.make_recipe('flex_bookings.booking', user=self.user, event=event1)
        # create booking for another user
        user1 = mommy.make_recipe('flex_bookings.user')
        mommy.make_recipe('flex_bookings.booking', user=user1, event=event2)

        # check only event1 shows in the booked events
        resp = self._get_response(self.user, 'events')
        booked_events = [event for event in resp.context_data['booked_events']]
        self.assertEquals(Booking.objects.all().count(), 2)
        self.assertEquals(len(booked_events), 1)
        self.assertTrue(event1 in booked_events)

    def test_event_list_does_not_show_unopen_events(self):
        event =  mommy.make_recipe('flex_bookings.future_WS', booking_open=True)
        resp = self._get_response(self.user, 'events')
        self.assertEqual(resp.context_data['events'].count(), 4)

        # make the new event closed
        event.booking_open = False
        event.save()
        resp = self._get_response(self.user, 'events')
        self.assertEqual(resp.context_data['events'].count(), 3)

    def test_filter_events(self):
        """
        Test that we can filter the classes by name
        """
        mommy.make_recipe(
            'flex_bookings.future_WS',
            name='test_name', booking_open=True, _quantity=3
        )
        mommy.make_recipe(
            'flex_bookings.future_WS', name='test_name1',
            booking_open=True, _quantity=4
        )

        url = reverse('flexbookings:events')
        resp = self.client.get(url, {'name': 'test_name'})
        self.assertEquals(resp.context_data['events'].count(), 3)


class EventDetailViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.event = mommy.make_recipe(
            'flex_bookings.future_WS', booking_open=True
        )
        self.not_open_event = mommy.make_recipe('flex_bookings.future_WS')
        mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True, _quantity=2
        )
        self.user = mommy.make_recipe('flex_bookings.user')

    def _get_response(self, user, event, ev_type):
        url = reverse('flexbookings:event_detail', args=[event.slug])
        request = self.factory.get(url)
        request.user = user
        view = EventDetailView.as_view()
        return view(request, slug=event.slug, ev_type=ev_type)

    def test_login_required(self):
        """
        test that page shows login link if there is no user logged in
        """
        url = reverse('flexbookings:event_detail', kwargs={'slug': self.event.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Sign in to book', resp.rendered_content)

    def test_with_logged_in_user(self):
        """
        test that page loads if there is a user available
        """
        resp = self._get_response(self.user, self.event, 'event')
        self.assertEqual(resp.status_code, 200)
        self.assertEquals(resp.context_data['type'], 'workshop')
        self.assertNotIn('Sign in to book', resp.rendered_content)

    def test_with_booked_event(self):
        """
        Test that booked event is shown as booked
        """
        #create a booking for this event and user
        mommy.make_recipe(
            'flex_bookings.booking', user=self.user, event=self.event
        )
        resp = self._get_response(self.user, self.event, 'event')
        self.assertTrue(resp.context_data['booked'])
        self.assertEquals(resp.context_data['booking_info_text'],
                          'You have booked for this workshop.')

    def test_with_not_open_event(self):
        """
        Test that not open event redirects
        """
        resp = self._get_response(self.user, self.not_open_event, 'event')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp.url,
            reverse(
                'flexbookings:not_open',
                kwargs={'event_slug': self.not_open_event.slug}
            )
        )

    def test_with_booked_event_for_different_user(self):
        """
        Test that the event is not shown as booked if the current user has
        not booked it
        """
        user1 = mommy.make_recipe('flex_bookings.user')
        #create a booking for this event and a different user
        mommy.make_recipe('flex_bookings.booking', user=user1, event=self.event)

        resp = self._get_response(self.user, self.event,'event')
        self.assertFalse('booked' in resp.context_data)
        self.assertEquals(resp.context_data['booking_info_text'], '')


class LessonListViewTests(TestCase):
    """
    Test EventListView with lessons; reuses the event templates and context
    data helpers
    """
    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        mommy.make_recipe('flex_bookings.future_WS', booking_open=True)
        mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True, _quantity=6
        )
        self.user = mommy.make_recipe('flex_bookings.user')

    def _get_response(self, user, ev_type):
        url = reverse('flexbookings:lessons')
        request = self.factory.get(url)
        request.user = user
        view = EventListView.as_view()
        return view(request, ev_type=ev_type)

    def test_with_logged_in_user(self):
        """
        test that page loads if there is a user is available
        """
        resp = self._get_response(self.user, 'lessons')
        self.assertEqual(resp.status_code, 200)
        self.assertEquals(resp.context_data['type'], 'lessons')
        self.assertTrue('booked_events' in resp.context_data)

    def test_lesson_list_with_anonymous_user(self):
        """
        Test that no booked_events in context
        """
        url = reverse('flexbookings:lessons')
        resp = self.client.get(url)

        # event listing should still only show future events
        self.assertFalse('booked_events' in resp.context)

    def test_lesson_list(self):
        """
        Test that only classes are listed (pole classes and other classes)
        """
        url = reverse('flexbookings:lessons')
        resp = self.client.get(url)

        self.assertEquals(Event.objects.all().count(), 7)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context['events'].count(), 6)
        self.assertEquals(resp.context['type'], 'lessons')

    def test_filter_lessons(self):
        """
        Test that we can filter the classes by name
        """
        mommy.make_recipe(
            'flex_bookings.future_EV', name='test_name',
            booking_open=True, _quantity=3)
        mommy.make_recipe(
            'flex_bookings.future_EV', name='test_name1',
            booking_open=True, _quantity=4
        )

        url = reverse('flexbookings:lessons')
        resp = self.client.get(url, {'name': 'test_name'})
        self.assertEquals(resp.context_data['events'].count(), 3)
        resp = self.client.get(url, {'name': 'test_name1'})
        self.assertEquals(resp.context_data['events'].count(), 4)

    def test_lesson_list_shows_only_current_user_bookings(self):
        """
        Test that only user's booked events are shown as booked
        """
        events = Event.objects.filter(event_type__event_type="CL")
        event1,  event2 = events[0:2]

        resp = self._get_response(self.user, 'lessons')
        # check there are no booked events yet
        booked_events = [event for event in resp.context_data['booked_events']]
        self.assertEquals(len(resp.context_data['booked_events']), 0)

        # create booking for this user
        mommy.make_recipe('flex_bookings.booking', user=self.user, event=event1)
        # create booking for another user
        user1 = mommy.make_recipe('flex_bookings.user')
        mommy.make_recipe('flex_bookings.booking', user=user1, event=event2)

        # check only event1 shows in the booked events
        resp = self._get_response(self.user, 'lessons')
        booked_events = [event for event in resp.context_data['booked_events']]
        self.assertEquals(Booking.objects.all().count(), 2)
        self.assertEquals(len(booked_events), 1)
        self.assertTrue(event1 in booked_events)

    def test_lesson_list_only_shows_open_bookings(self):
        events = Event.objects.filter(event_type__event_type="CL")
        event1,  event2 = events[0:2]

        resp = self._get_response(self.user, 'lessons')
        # check there are no booked events yet
        booked_events = [event for event in resp.context_data['booked_events']]
        self.assertEquals(len(resp.context_data['booked_events']), 0)

        # create open and cancelled booking for this user
        mommy.make_recipe('flex_bookings.booking', user=self.user, event=event1)
        mommy.make_recipe(
            'flex_bookings.booking', user=self.user, event=event2,
            status='CANCELLED'
        )

        # check only event1 shows in the booked events
        resp = self._get_response(self.user, 'lessons')
        booked_events = [event for event in resp.context_data['booked_events']]
        self.assertEquals(Booking.objects.all().count(), 2)
        self.assertEquals(len(booked_events), 1)
        self.assertTrue(event1 in booked_events)


class LessonDetailViewTests(TestCase):
    """
    Test EventDetailView with lessons; reuses the event templates and
    context data helpers
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.lesson = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True
        )
        set_up_fb()
        self.user = mommy.make_recipe('flex_bookings.user')

    def test_with_logged_in_user(self):
        """
        test that page loads if there user is available
        """
        url = reverse('flexbookings:lesson_detail', args=[self.lesson.slug])
        request = self.factory.get(url)
        # Set the user on the request
        request.user = self.user
        view = EventDetailView.as_view()
        resp = view(request, slug=self.lesson.slug, ev_type='lesson')

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(resp.context_data['type'], 'lesson')
        self.assertNotIn('Sign in to book', resp.rendered_content)
