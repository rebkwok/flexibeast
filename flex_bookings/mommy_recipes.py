from datetime import timedelta, datetime
from django.contrib.auth.models import User

from django.utils import timezone

from model_mommy.recipe import Recipe, foreign_key, seq

from allauth.socialaccount.models import SocialApp
from flex_bookings.models import Event, EventType, Block, Booking, \
    WaitingListUser
from timetable.models import Session

now = timezone.now()
past = now - timedelta(30)
future = now + timedelta(30)

user = Recipe(User,
              username=seq("test_user"),
              password="password",
              email="test_user@test.com",
              )

# events; use defaults apart from dates
# override when using recipes, eg. mommy.make_recipe('future_event', cost=10)

event_type_YC = Recipe(EventType, event_type="CL", subtype=seq("Yoga class"))
event_type_WS = Recipe(EventType, event_type="EV", subtype=seq("Workshop"))

future_EV = Recipe(Event,
                      date=future,
                      event_type=foreign_key(event_type_YC))

future_WS = Recipe(Event,
                   date=future,
                   event_type=foreign_key(event_type_WS))

# past event
past_event = Recipe(Event,
                    date=past,
                    event_type=foreign_key(event_type_WS),
                    advance_payment_required=True,
                    cost=10,
                    payment_due_date=past-timedelta(10)
                    )

block = Recipe(Block)

booking = Recipe(Booking)

past_booking = Recipe(Booking,
                      event=foreign_key(past_event)
                      )

fb_app = Recipe(SocialApp,
                provider='facebook')

mon_session = Recipe(Session, event_type=foreign_key(event_type_YC), day=Session.MON)
tue_session = Recipe(Session, event_type=foreign_key(event_type_YC), day=Session.TUE)
wed_session = Recipe(Session, event_type=foreign_key(event_type_YC), day=Session.WED)

waiting_list_user = Recipe(WaitingListUser)
