from django.core.management.base import BaseCommand, CommandError
from datetime import time
from timetable.models import Location, WeeklySession
from flex_bookings.models import EventType


class Command(BaseCommand):

    def handle(self, *args, **options):

        """
        Create the default locations and timetable sessions
        """
        self.stdout.write('Creating locations.')

        watermelon, created = Location.objects.get_or_create(short_name="Watermelon")
        if created:
            watermelon.full_name = "The Watermelon Studio"
            watermelon.address = "19 Beaverbank Place, Edinburgh"
            watermelon.map_url = "https://www.google.com/maps/embed?" \
                                 "pb=!1m18!1m12!1m3!1d2233.164515680218!2d-" \
                                 "3.1966306841146395!3d55.963851483162244!" \
                                 "2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!" \
                                 "3m3!1m2!1s0x4887c7ed775410a7%3" \
                                 "A0x68d8d1661faf7a7c!2sThe+Watermelon+Studio" \
                                 "!5e0!3m2!1sen!2suk!4v1461918815072"
            watermelon.save()
        self.stdout.write('Location "{}" {}'.format(
            watermelon, 'created' if created else 'already exists'
        ))

        self.stdout.write('Creating timetable weekly sessions.')

        yc, _ = EventType.objects.get_or_create(
            event_type='CL', subtype='Yoga class'
        )

        # Wednesday classes
        WeeklySession.objects.get_or_create(
            name="Flexibility for Splits",
            day=WeeklySession.WED,
            event_type=yc,
            time=time(hour=19, minute=00),
            location=watermelon,
            contact_person="Alicia Alexandra",
            contact_email="flexibeast@hotmail.com",
            block_info="6 week block"
        )
        WeeklySession.objects.get_or_create(
            name="Flexibility for Splits",
            day=WeeklySession.WED,
            event_type=yc,
            time=time(hour=20, minute=10),
            location=watermelon,
            contact_person="Alicia Alexandra",
            contact_email="flexibeast@hotmail.com",
            block_info="6 week block"
        )
        # FRI CLASSES
        WeeklySession.objects.get_or_create(
            name="Booty Blast",
            day=WeeklySession.FRI,
            event_type=yc,
            time=time(hour=11, minute=00),
            location=watermelon,
            contact_person="Alicia Alexandra",
            contact_email="flexibeast@hotmail.com",
            block_info=""
        )
        # SUN CLASSES
        WeeklySession.objects.get_or_create(
            name="Flexibility for Backs",
            day=WeeklySession.SUN,
            event_type=yc,
            time=time(hour=19, minute=00),
            location=watermelon,
            contact_person="Alicia Alexandra",
            contact_email="flexibeast@hotmail.com",
            block_info="6 week block"
        )
        WeeklySession.objects.get_or_create(
            name="Happy Hips",
            day=WeeklySession.SUN,
            event_type=yc,
            time=time(hour=20, minute=10),
            location=watermelon,
            contact_person="Alicia Alexandra",
            contact_email="flexibeast@hotmail.com",
            block_info="6 week block"
        )
