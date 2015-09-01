"""
Helper functions to return context and reduce logic in templates
"""
from django.conf import settings
from django.utils import timezone
from django.core.urlresolvers import reverse

from flex_bookings.models import WaitingListUser


def get_event_context(context, event, user):

    if event.event_type.event_type == 'CL':
        context['type'] = "lesson"
        event_type_str = "class"
    else:
        context['type'] = "event"
        event_type_str = "event"

    if event.date <= timezone.now():
        context['past'] = True

    # payment info text to be displayed
    if event.cost == 0:
        payment_text = "There is no cost associated with this {}.".format(
            event_type_str
        )
    context['payment_text'] = event.payment_info

    # booked flag
    if user.is_authenticated():
        user_bookings = user.bookings.all()
        user_booked_events = [booking.event for booking in user_bookings
                                 if booking.status == 'OPEN']
        user_cancelled_events = [booking.event for booking in user_bookings
                                 if booking.status == 'CANCELLED']
        booked = event in user_booked_events
        cancelled = event in user_cancelled_events

        # waiting_list flag
        try:
            WaitingListUser.objects.get(user=user, event=event)
            context['waiting_list'] = True
        except WaitingListUser.DoesNotExist:
            pass

        # booking info text and bookable
        booking_info_text = ""
        context['bookable'] = event.bookable()
        if booked:
            context['bookable'] = False
            booking_info_text = "You have booked for this {}.".format(event_type_str)
            context['booked'] = True
        else:
            if cancelled:
                context['cancelled'] = True
                booking_info_text_cancelled = "You have previously booked for this {} and" \
                                        " cancelled.".format(event_type_str)
                context['booking_info_text_cancelled'] = booking_info_text_cancelled

            if event.spaces_left() <= 0:
                booking_info_text = "This {} is now full.".format(event_type_str)
            if event.payment_due_date:
                if event.payment_due_date < timezone.now():
                    booking_info_text = "Bookings for this event are now closed."

        context['booking_info_text'] = booking_info_text
    return context


def get_booking_create_context(event, request, context):

    # Add in the event name
    context['event'] = event

    ev_type = 'workshop' if \
        event.event_type.event_type == 'EV' else 'class'

    context['ev_type'] = ev_type

    bookings_count = event.bookings.filter(status='OPEN').count()
    if event.max_participants:
        event_full = True if \
            (event.max_participants - bookings_count) <= 0 else False
        context['event_full'] = event_full

    return context


def get_paypal_dict(host, cost, item_name, invoice_id, custom):

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": cost,
        "item_name": item_name,
        "custom": custom,
        "invoice": invoice_id,
        "currency_code": "GBP",
        "notify_url": host + reverse('paypal-ipn'),
        "return_url": host + reverse('payments:paypal_confirm'),
        "cancel_return": host + reverse('payments:paypal_cancel'),

    }
    return paypal_dict