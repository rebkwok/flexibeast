from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404

from flex_bookings.models import Booking, Event, WaitingListUser
from studioadmin.views.utils import staff_required

@login_required
@staff_required
def event_waiting_list_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    waiting_list_users = WaitingListUser.objects.filter(
        event__id=event_id).order_by('user__username')
    ev_type = 'class' if event.event_type.event_type == 'CL' else 'workshop'

    booking_users = [booking.user for booking in Booking.objects.filter(
        event__id=event_id, status='OPEN'
    ).order_by('user__username')]


    template = 'studioadmin/event_bookings_and_waiting_list.html'
    return TemplateResponse(
        request, template, {
            'waiting_list_users': waiting_list_users,
            'booking_users': booking_users,
            'ev_type': ev_type,
            'event': event,
            'sidenav_selection': 'events' if ev_type == 'workshop' else 'lessons'
        }
    )