from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import time
from timetable.models import Session
from flex_bookings.models import EventType

class Command(BaseCommand):

    def handle(self, *args, **options):

        """
        Create the default timetable sessions
        """
        self.stdout.write('Creating timetable sessions.')

        yc, _ = EventType.objects.get_or_create(
            event_type='CL', subtype='Yoga class'
        )

        # Wednesday classes
        Session.objects.get_or_create(
            name="Flexibility for Splits",
            day=Session.WED,
            event_type=yc,
            time=time(hour=19, minute=00),
            booking_open=False,
            contact_person="Alicia Alexandra",
            contact_email="flexibeast@hotmail.com",
            advance_payment_required=True
        )
        Session.objects.get_or_create(
            name="Flexibility for Splits",
            day=Session.WED,
            event_type=yc,
            time=time(hour=20, minute=10),
            booking_open=False,
            contact_person="Alicia Alexandra",
            contact_email="flexibeast@hotmail.com",
            advance_payment_required=True
        )

        # SUN CLASSES
        Session.objects.get_or_create(
            name="Flexibility for Backs",
            day=Session.SUN,
            event_type=yc,
            time=time(hour=19, minute=00),
            booking_open=False,
            contact_person="Alicia Alexandra",
            contact_email="flexibeast@hotmail.com",
            advance_payment_required=True
        )