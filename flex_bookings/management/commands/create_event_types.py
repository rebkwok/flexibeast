from django.core.management.base import BaseCommand, CommandError
from flex_bookings.models import EventType

class Command(BaseCommand):
    """
    Create event types
    """
    def handle(self, *args, **options):

        self.stdout.write("Creating event types")
        yc, _ = EventType.objects.get_or_create(
            event_type='CL',
            subtype='Yoga class'
        )
        cl, _ = EventType.objects.get_or_create(
            event_type='CL',
            subtype='Other class'
        )
        pv, _ = EventType.objects.get_or_create(
            event_type='CL',
            subtype='Private'
        )
        ws = EventType.objects.get_or_create(
            event_type='EV',
            subtype='Workshop'
        )
