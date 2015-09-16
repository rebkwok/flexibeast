from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from flex_bookings.models import Event, EventType


class Command(BaseCommand):

    def handle(self, *args, **options):

        ws, _ = EventType.objects.get_or_create(event_type='EV', subtype='Workshop')

        self.stdout.write("Creating events")
        now = timezone.now()
        # create 2 with defaults, 1 with max participants
        Event.objects.get_or_create(
            name="Workshop",
            event_type=ws,
            description="Workshop with awesome unnamed instructor!",
            date=now + timedelta(30),
            max_participants=20,
            cost=10,
            booking_open=True,
            advance_payment_required=True,
            payment_due_date=now + timedelta(27),
        )

        # non-default contact
        Event.objects.get_or_create(
            name="Workshop 1",
            event_type=ws,
            description="Workshop with another awesome unnamed instructor!\n",
            date=now + timedelta(30),
            max_participants=20,
            cost=10,
            booking_open=True,
            contact_person="Someone else",
            contact_email="someone@else.com",
            payment_due_date=now + timedelta(30),
        )

        # Past event
        Event.objects.get_or_create(
            name="An old workshop",
            event_type=ws,
            description="Workshop that happened in the past!\n",
            date=now - timedelta(30),
            advance_payment_required=True,
            max_participants=20,
            cost=10,
            booking_open=True,
            payment_due_date=now - timedelta(40),
        )
