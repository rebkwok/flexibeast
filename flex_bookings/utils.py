import logging
import pytz
import time

from django.utils import timezone
from datetime import timedelta, datetime, date
from flex_bookings.models import Event
from timetable.models import Session
from activitylog.models import ActivityLog


logger = logging.getLogger(__name__)

def upload_timetable(start_date, end_date, session_ids, user=None):

    daylist = [
        '01MON',
        '02TUE',
        '03WED',
        '04THU',
        '05FRI',
        '06SAT',
        '07SUN'
        ]

    created_classes = []
    existing_classes = []

    d = start_date
    delta = timedelta(days=1)
    while d <= end_date:
        sessions_to_create = Session.objects.filter(
            day=daylist[d.weekday()],
            id__in=session_ids
        )
        for session in sessions_to_create:

            # create date in Europe/London, convert to UTC
            localtz = pytz.timezone('Europe/London')
            local_date = localtz.localize(datetime.combine(d,
                session.time))
            converted_date = local_date.astimezone(pytz.utc)

            cl, created = Event.objects.get_or_create(
                name=session.name,
                event_type=session.event_type,
                date=converted_date,
                location=session.location
            )
            if created:
                cl.description=session.description
                cl.max_participants=session.max_participants
                cl.contact_person=session.contact_person
                cl.contact_email=session.contact_email
                cl.cost=session.cost
                cl.advance_payment_required=session.advance_payment_required
                cl.payment_info=session.payment_info
                cl.cancellation_period=session.cancellation_period
                cl.email_studio_when_booked = session.email_studio_when_booked
                cl.save()

                created_classes.append(cl)
            else:
                existing_classes.append(cl)
        d += delta

    if created_classes:
        ActivityLog.objects.create(
            log='Classes uploaded from timetable for {} to {} {}'.format(
                start_date.strftime('%a %d %B %Y'),
                end_date.strftime('%a %d %B %Y'),
                'by admin user {}'.format(user.username) if user else ''
            )
        )

    return created_classes, existing_classes
