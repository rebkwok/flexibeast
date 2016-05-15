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
        watermelon_defaults = {
                'full_name': "The Watermelon Studio",
                'address': "19 Beaverbank Place, Edinburgh",
                'map_url': "https://www.google.com/maps/embed?"
                                 "pb=!1m18!1m12!1m3!1d2233.164515680218!2d-"
                                 "3.1966306841146395!3d55.963851483162244!"
                                 "2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!"
                                 "3m3!1m2!1s0x4887c7ed775410a7%3"
                                 "A0x68d8d1661faf7a7c!2sThe+Watermelon+Studio"
                                 "!5e0!3m2!1sen!2suk!4v1461918815072"
            }
        watermelon, created = Location.objects.update_or_create(
            short_name="Watermelon Studio", defaults=watermelon_defaults)
        self.stdout.write('Location "{}" {}'.format(
            watermelon, 'created' if created else 'already exists'
        ))

        bellview_defaults = {
                'full_name': "Bellview Centre",
                'address': "33 West St, Belford",
                'map_url': "https://www.google.com/maps/embed?pb=!1m18!1m12!"
                           "1m3!1d2254.2514538966893!2d-1.8345816842737208!"
                           "3d55.597637280512146!2m3!1f0!2f0!3f0!3m2!1i1024!"
                           "2i768!4f13.1!3m3!1m2!1s0x488753a64283f699%3A0x3d"
                           "d2773b9bddebd9!2sBell+View+Care!5e0!3m2!1sen!2suk"
                           "!4v1463178001647"
            }
        bellview, created = Location.objects.update_or_create(
            short_name="Bellview Centre", defaults=bellview_defaults)
        self.stdout.write('Location "{}" {}'.format(
            watermelon, 'created' if created else 'already exists'
        ))

        self.stdout.write('Creating timetable weekly sessions.')

        yc, _ = EventType.objects.get_or_create(
            event_type='CL', subtype='Yoga class'
        )
        self.stdout.write('Event Type "{}" {}'.format(
            yc, 'created' if created else 'already exists'
        ))


        class_defaults = {
            'event_type': yc,
            'location': watermelon,
            'description': '',
            'contact_person': "Alicia Alexandra",
            'contact_email': "flexibeast@hotmail.com",
            'block_info': "Drop in £7.50; 6 session block £39; booking essential"
        }

        bv_class_defaults = class_defaults.copy()
        bv_class_defaults.update(location=bellview)

        # Monday classes
        bv1 = WeeklySession.objects.update_or_create(
            name="Restorative Yoga",
            day=WeeklySession.MON,
            time=time(hour=18, minute=00),
            defaults=bv_class_defaults
        )
        bv2 = WeeklySession.objects.update_or_create(
            name="Vinyasa Flow Yoga",
            day=WeeklySession.MON,
            time=time(hour=19, minute=00),
            defaults=bv_class_defaults
        )

        # Wednesday classes
        cl1 = WeeklySession.objects.update_or_create(
            name="Sensible Splits",
            day=WeeklySession.WED,
            time=time(hour=19, minute=00),
            defaults=class_defaults
        )
        cl2 = WeeklySession.objects.update_or_create(
            name="Sensible Splits",
            day=WeeklySession.WED,
            time=time(hour=20, minute=10),
            defaults=class_defaults
        )
        # FRI CLASSES
        # cl3 = WeeklySession.objects.update_or_create(
        #     name="Booty Blast",
        #     day=WeeklySession.FRI,
        #     time=time(hour=11, minute=00),
        #     defaults=class_defaults
        # )
        # SUN CLASSES
        cl4 = WeeklySession.objects.update_or_create(
            name="Healthy Bendy Backs",
            day=WeeklySession.SUN,
            time=time(hour=19, minute=00),
            defaults=class_defaults
        )
        cl5 = WeeklySession.objects.update_or_create(
            name="Sensible Splits",
            day=WeeklySession.SUN,
            time=time(hour=20, minute=10),
            defaults=class_defaults
        )

        created_cls = []
        updated_cls = []

        for cl in [bv1, bv2, cl1, cl2, cl4, cl5]:
        # for cl in [cl1, cl2, cl3, cl4, cl5]:
            if cl[1]:
                created_cls.append(cl[0])
            else:
                updated_cls.append(cl[0])

        if created_cls:
            self.stdout.write(
                'Sessions ids {} created'.format(
                    ', '.join([str(sess.id) for sess in created_cls])
                )
            )

        if updated_cls:
            self.stdout.write(
                'Sessions ids {} updated with default values'.format(
                    ', '.join([str(sess.id) for sess in updated_cls])
                )
            )
