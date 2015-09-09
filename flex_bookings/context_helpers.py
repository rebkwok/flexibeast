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

        # cannot book block if has already booked a single class in the block
        open_user_booked_events = [
            booking.event for booking in user.bookings.all()
            if booking.status == 'OPEN'
        ]
        available_blocks = []
        unavailable_reasons = []
        for block in event.blocks.all():
            available_blocks.append(block)
            related_events = block.events.all()
            for ev in related_events:
                if ev in open_user_booked_events:
                    available_blocks.remove(block)
                    unavailable_block = {
                        'block': block,
                        'reason':  "You have already booked at least "
                                   "one other class in this block"
                    }
                    unavailable_reasons.append(unavailable_block)
                    break

        # cannot book block if classes already started
        for block in list(available_blocks):
            first = block.events.first()
            first_date = first.date
            if first_date < timezone.now():
                available_blocks.remove(block)
                unavailable_block = {
                    'block': block, 'reason': "This block has already started"
                }
                unavailable_reasons.append(unavailable_block)

        # cannot book block if any class in the block is full
        for block in list(available_blocks):
            for event in block.events.all():
                if event.spaces_left() <= 0:
                    available_blocks.remove(block)
                    unavailable_block = {
                        'block': block,
                        'reason': "One or more classes in this block is full"
                    }
                    unavailable_reasons.append(unavailable_block)
                    break

        context['available_blocks'] = available_blocks
        context['unavailable_reasons'] = unavailable_reasons

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

    # cannot book block if has already booked a single class in the block
    open_user_booked_events = [
        booking.event for booking in request.user.bookings.all()
        if booking.status == 'OPEN'
    ]
    available_blocks = []
    unavailable_reasons = []
    for block in event.blocks.all():
        available_blocks.append(block)
        related_events = block.events.all()
        for ev in related_events:
            if ev in open_user_booked_events:
                available_blocks.remove(block)
                unavailable_block = {
                    'block': block,
                    'reason': "You have already booked at least one other "
                              "class in this block"
                }
                unavailable_reasons.append(unavailable_block)
                break

    # cannot book block if classes already started
    for block in list(available_blocks):
        first = block.events.first()
        first_date = first.date
        if first_date < timezone.now():
            available_blocks.remove(block)
            unavailable_block = {
                'block': block, 'reason':  "This block has already started"
            }
            unavailable_reasons.append(unavailable_block)

    # cannot book block if any class in the block is full
    for block in list(available_blocks):
        for event in block.events.all():
            if event.spaces_left() <= 0:
                available_blocks.remove(block)
                unavailable_block = {
                    'block': block,
                    'reason': "One or more classes in this block is full"
                }
                unavailable_reasons.append(unavailable_block)
                break

    context['available_blocks'] = available_blocks
    context['unavailable_reasons'] = unavailable_reasons

    context['individual_booking_allowed'] = True
    date_individual_booking_allowed = None
    for block in event.blocks.all():
        if block.individual_booking_date > timezone.now():
            context['individual_booking_allowed'] = False
            # set individual booking date to the latest date according to
            # the available block settings (in case an event is in multiple
            # blocks and different dates are set)
            if date_individual_booking_allowed and \
                            block.individual_booking_date > \
                            date_individual_booking_allowed:
                date_individual_booking_allowed = block.individual_booking_date
            else:
                date_individual_booking_allowed = block.individual_booking_date

    context['date_individual_booking_allowed'] = date_individual_booking_allowed
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