from datetime import timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.utils import timezone
from django.contrib.messages.storage.fallback import FallbackStorage

from model_mommy import mommy

from flex_bookings.views import EventDetailView
from flex_bookings.tests.helpers import set_up_fb

import flex_bookings.templatetags as templatetags

from studioadmin.views.events import event_admin_list, registers_by_date

class CancellationFormatTagsTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')

    def _get_response(self, user, event, ev_type):
        url = reverse('flexbookings:event_detail', args=[event.slug])
        request = self.factory.get(url)
        request.user = user
        view = EventDetailView.as_view()
        return view(request, slug=event.slug, ev_type=ev_type)

    def test_cancellation_format_tag_event_detail(self):
        """
        Test that cancellation period is formatted correctly
        """
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True,
            cancellation_period=24
        )
        resp = self._get_response(self.user, event, 'lesson')
        resp.render()
        self.assertIn('24 hours', str(resp.content))

        event.cancellation_period = 619
        event.save()
        resp = self._get_response(self.user, event, 'lesson')
        resp.render()
        self.assertIn('3 weeks, 4 days and 19 hours', str(resp.content))

        event.cancellation_period = 168
        event.save()
        resp = self._get_response(self.user, event, 'lesson')
        resp.render()
        self.assertIn('1 week', str(resp.content))

        event.cancellation_period = 192
        event.save()
        resp = self._get_response(self.user, event, 'lesson')
        resp.render()
        self.assertIn('1 week, 1 day and 0 hours', str(resp.content))


class RegisterExtraLinesTagsTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')
        self.user.is_staff = True
        self.user.save()

    def _post_response(self, user, date, event_ids):
        url = reverse('studioadmin:registers_by_date')
        request = self.factory.post(
            url, {
                'register_date': date,
                'register_format': 'full',
                'print': 'print',
                'select_events': event_ids
            }
        )
        request.user = user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return registers_by_date(request)

    def test_get_range(self):
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True, date=timezone.now(),
            max_participants=3
        )
        resp = self._post_response(
            self.user, event.date.strftime('%a %d %b %Y'),
            [event.id]
        )
        # no bookings; should have 3 extra lines. Look for extra_checkbox_# ids

        for cbx_id in ['extra_checkbox_{}'.format(i) for i in range(3)]:
            self.assertIn(cbx_id, resp.rendered_content)

        mommy.make('flex_bookings.booking', event=event)

        resp = self._post_response(
            self.user, event.date.strftime('%a %d %b %Y'),
            [event.id]
        )
        # 1 bookings; should have 2 extra lines. Look for extra_checkbox_# ids
        for cbx_id in ['extra_checkbox_{}'.format(i) for i in range(2)]:
            self.assertIn(cbx_id, resp.rendered_content)
        self.assertNotIn('"extra_checkbox_2"', resp.rendered_content)

    def test_get_index_open(self):
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True, date=timezone.now(),
            max_participants=3
        )
        mommy.make('flex_bookings.booking', event=event)

        resp = self._post_response(
            self.user, event.date.strftime('%a %d %b %Y'),
            [event.id]
        )

        # Should have same indexes as max participants
        for idx in ['>{}.<'.format(i) for i in range(1, 4)]:
            self.assertIn(idx, resp.rendered_content)
        self.assertNotIn('>0.<', resp.rendered_content)
        self.assertNotIn('>4.<', resp.rendered_content)


class BookingsCountTagsTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')
        self.user.is_staff = True
        self.user.save()

    def _get_response(self, user):
        url = reverse('studioadmin:events')
        request = self.factory.get(url)
        request.user = user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return event_admin_list(request, 'lessons')

    def test_bookings_count(self):
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True,
            date=timezone.now() + timedelta(1),
            max_participants=3
        )
        mommy.make('flex_bookings.booking', event=event)

        resp = self._get_response(self.user)
        self.assertIn(
            '<a href="/studioadmin/bookings-waitinglists/{}">{}</a>'.format(
                event.id, event.bookings.count()
            ),
            str(resp.content)
        )
