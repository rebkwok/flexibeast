import logging
from functools import wraps

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import HttpResponse, HttpResponseRedirect, render, get_object_or_404
from django.template.response import TemplateResponse

from django.views.generic import (
    ListView, DetailView, CreateView, DeleteView
)
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from django.template.loader import get_template
from braces.views import LoginRequiredMixin

from flex_bookings.models import Block, Booking, BookingError, \
    Event, WaitingListUser
from flex_bookings.forms import EventFilter, LessonFilter, BookingCreateForm
from flex_bookings.email_helpers import send_support_email, \
    send_waiting_list_email
import flex_bookings.context_helpers as context_helpers

from payments.forms import PayPalPaymentsListForm
from payments.helpers import create_booking_paypal_transaction, \
    create_block_paypal_transaction

from activitylog.models import ActivityLog

logger = logging.getLogger(__name__)


class EventListView(ListView):
    model = Event
    context_object_name = 'events'
    template_name = 'flex_bookings/events.html'

    def get_queryset(self):
        if self.kwargs['ev_type'] == 'events':
            ev_abbr = 'EV'
        else:
            ev_abbr = 'CL'

        name = self.request.GET.get('name')

        if name:
            return Event.objects.filter(
                Q(event_type__event_type=ev_abbr) & Q(date__gte=timezone.now())
                & Q(name=name) & Q(booking_open=True)).order_by('date')
        return Event.objects.filter(
            Q(event_type__event_type=ev_abbr) & Q(date__gte=timezone.now()) &
            Q(booking_open=True)
            ).order_by('date')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(EventListView, self).get_context_data(**kwargs)
        if not self.request.user.is_anonymous():
            # Add in the booked_events
            user_bookings = self.request.user.bookings.all()
            booked_events = [booking.event for booking in user_bookings
                             if not booking.status == 'CANCELLED']
            user_waiting_lists = WaitingListUser.objects.filter(user=self.request.user)
            waiting_list_events = [wluser.event for wluser in user_waiting_lists]
            context['booked_events'] = booked_events
            context['waiting_list_events'] = waiting_list_events

        context['type'] = self.kwargs['ev_type']

        event_name = self.request.GET.get('name', '')
        if self.kwargs['ev_type'] == 'events':
            form = EventFilter(initial={'name': event_name})
        else:
            form = LessonFilter(initial={'name': event_name})
        context['form'] = form
        return context


class EventDetailView(DetailView):

    model = Event
    context_object_name = 'event'
    template_name = 'flex_bookings/event.html'

    def get(self, *args, **kwargs):
        if self.kwargs['ev_type'] == 'event':
            ev_abbr = 'EV'
        else:
            ev_abbr = 'CL'

        queryset = Event.objects.filter(event_type__event_type=ev_abbr)
        obj = get_object_or_404(queryset, slug=self.kwargs['slug'])

        if not obj.booking_open:
            return HttpResponseRedirect(
                reverse('flexbookings:not_open', args=[obj.slug])
            )
        return super(EventDetailView, self).get(self, *args, **kwargs)

    def get_object(self):
        if self.kwargs['ev_type'] == 'event':
            ev_abbr = 'EV'
        else:
            ev_abbr = 'CL'
        queryset = Event.objects.filter(event_type__event_type=ev_abbr)

        return get_object_or_404(queryset, slug=self.kwargs['slug'])


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(EventDetailView, self).get_context_data()
        event = self.object
        return context_helpers.get_event_context(
            context, event, self.request.user
        )


class BookingListView(LoginRequiredMixin, ListView):

    model = Booking
    context_object_name = 'bookings'
    template_name = 'flex_bookings/bookings.html'

    def get_queryset(self):
        return Booking.objects.filter(
            Q(event__date__gte=timezone.now()) & Q(user=self.request.user)
        ).order_by('event__date')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BookingListView, self).get_context_data(**kwargs)

        bookingformlist = []
        for booking in self.object_list:
            # if booking.event.event_type not in active_block_event_types \
            #         and booking.status == 'OPEN' and not booking.paid:
            #     # ONLY DO THIS IF PAYPAL BUTTON NEEDED
            #     invoice_id = create_booking_paypal_transaction(
            #         self.request.user, booking).invoice_id
            #     host = 'http://{}'.format(self.request.META.get('HTTP_HOST'))
            #     paypal_form = PayPalPaymentsListForm(
            #         initial=context_helpers.get_paypal_dict(
            #             host,
            #             booking.event.cost,
            #             booking.event,
            #             invoice_id,
            #             '{} {}'.format('booking', booking.id)
            #         )
            #     )
            # else:
            #     paypal_form = None

            try:
                WaitingListUser.objects.get(
                    user=self.request.user, event=booking.event
                )
                on_waiting_list = True
            except WaitingListUser.DoesNotExist:
                on_waiting_list = False

            can_cancel = booking.event.can_cancel() and \
                booking.status == 'OPEN'
            bookingform = {
                'ev_type': booking.event.event_type.event_type,
                'booking': booking,
                # 'paypalform': paypal_form,
                'can_cancel': can_cancel,
                'on_waiting_list': on_waiting_list
                }
            bookingformlist.append(bookingform)
        context['bookingformlist'] = bookingformlist
        return context


class BookingHistoryListView(LoginRequiredMixin, ListView):

    model = Booking
    context_object_name = 'bookings'
    template_name = 'flex_bookings/bookings.html'

    def get_queryset(self):
        return Booking.objects.filter(
            event__date__lte=timezone.now(), user=self.request.user
        ).order_by('-event__date')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(
            BookingHistoryListView, self
            ).get_context_data(**kwargs)
        # Add in the history flag
        context['history'] = True

        bookingformlist = []
        for booking in self.object_list:
            bookingform = {'booking': booking}
            bookingformlist.append(bookingform)
        context['bookingformlist'] = bookingformlist
        return context


class BookingCreateView(LoginRequiredMixin, CreateView):

    model = Booking
    template_name = 'flex_bookings/create_booking.html'
    success_message = 'Your booking has been made for {}.'
    form_class = BookingCreateForm

    def dispatch(self, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=kwargs['event_slug'])
        return super(BookingCreateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        return {
            'event': self.event.pk
        }

    def get(self, request, *args, **kwargs):

        # redirect if fully booked or already booked
        if 'join waiting list' in request.GET:
            waitinglistuser, new = WaitingListUser.objects.get_or_create(
                    user=request.user, event=self.event
                )
            if new:
                msg = 'You have been added to the waiting list for {}. ' \
                    ' We will email you if a space becomes ' \
                    'available.'.format(self.event)
                ActivityLog.objects.create(
                    log='User {} has been added to the waiting list '
                    'for {}'.format(
                        request.user.username, self.event
                    )
                )
            else:
                msg = 'You are already on the waiting list for {}'.format(
                    self.event
                )
            messages.success(request, msg)

            ev_type = 'lessons' \
                if self.event.event_type.event_type == 'CL' else 'events'

            if 'bookings' in request.GET:
                return HttpResponseRedirect(reverse('flexbookings:bookings'))
            return HttpResponseRedirect(
                reverse('flexbookings:{}'.format(ev_type))
            )
        elif 'leave waiting list' in request.GET:
            try:
                waitinglistuser = WaitingListUser.objects.get(
                    user=request.user, event=self.event
                )
                waitinglistuser.delete()
                msg = 'You have been removed from the waiting list ' \
                    'for {}. '.format(self.event)
                ActivityLog.objects.create(
                    log='User {} has left the waiting list '
                    'for {}'.format(
                        request.user.username, self.event
                    )
                )
            except WaitingListUser.DoesNotExist:
                msg = 'You are not on the waiting list '\
                    'for {}. '.format(self.event)

            messages.success(request, msg)

            ev_type = 'lessons' \
                if self.event.event_type.event_type == 'CL' \
                else 'events'

            if 'bookings' in request.GET:
                return HttpResponseRedirect(
                    reverse('flexbookings:bookings')
                )
            return HttpResponseRedirect(
                reverse('flexbookings:{}'.format(ev_type))
            )
        elif self.event.spaces_left() <= 0:
            return HttpResponseRedirect(
                reverse('flexbookings:fully_booked', args=[self.event.slug])
            )

        try:
            booking = Booking.objects.get(
                user=self.request.user, event=self.event
            )
            if booking.status == 'CANCELLED':
                return super(
                    BookingCreateView, self
                    ).get(request, *args, **kwargs)
            return HttpResponseRedirect(reverse('flexbookings:duplicate_booking',
                                        args=[self.event.slug]))
        except Booking.DoesNotExist:
            return super(BookingCreateView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BookingCreateView, self).get_context_data(**kwargs)
        updated_context = context_helpers.get_booking_create_context(
            self.event, self.request, context
        )
        return updated_context

    def form_valid(self, form):

        booking = form.save(commit=False)

        open_user_booked_events = [
                bk.event for bk in self.request.user.bookings.all()
                if bk.status == 'OPEN'
            ]

        if booking.event in open_user_booked_events:
            messages.info(
                self.request, 'Already booked for {}'.format(booking.event)
            )
            return HttpResponseRedirect(reverse('flexbookings:lessons'))

        if 'book_block' in self.request.POST:

            block_id = int(self.request.POST['book_block'])
            block = Block.objects.get(id=block_id)

            # check that the user is not already booked into any of these events
            for event in block.events.all():
                if event in open_user_booked_events:
                    messages.error(
                        self.request, 'You cannot book this block as you already have '
                                 'a booking for one or more classes in the block')
                    return HttpResponseRedirect(reverse('flexbookings:lessons'))
                else:
                    try:
                        booking = Booking.objects.get(
                            event=event, user=self.request.user, status='CANCELLED'
                        )
                        # reopen booking
                        booking.status = 'OPEN'
                        booking.block = block
                        cost=block.item_cost
                        booking.save()
                    except Booking.DoesNotExist:
                        Booking.objects.create(
                            event=event, block=block, user=self.request.user,
                            cost=block.item_cost
                        )

            messages.success(
                self.request, mark_safe(
                    'You have been booked in to the following classes:</br>'
                    '{}'.format('</br>'.join([str(event) for event in block.events.all()]))
                )
            )

            host = 'http://{}'.format(self.request.META.get('HTTP_HOST'))
            # send email to user
            ctx = {
                'host': host, 'block_obj': block, 'block_name': block.name,
                'block_events': block.events.all(), 'user': self.request.user
                }

            try:
                send_mail('{} Booking for {}'.format(
                    settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, block.name),
                    get_template('flex_bookings/email/booking_received.txt').render(ctx),
                    settings.DEFAULT_FROM_EMAIL,
                    [self.request.user.email],
                    html_message=get_template(
                        'flex_bookings/email/booking_received.html'
                        ).render(ctx),
                    fail_silently=False)
                ActivityLog.objects.create(
                    log='Email sent to user {} regarding booking for '
                        'block {}'.format(
                        self.request.user.username,
                        block.name
                    )
                )
            except Exception as e:
                # send mail to tech support with Exception
                send_support_email(e, __name__, "BookingCreateView")

            try:
                send_mail('{} {} {} has just booked block {}'.format(
                    settings.ACCOUNT_EMAIL_SUBJECT_PREFIX,
                    self.request.user.first_name,
                    self.request.user.last_name, block.name),
                          get_template(
                            'flex_bookings/email/to_studio_booking.txt'
                            ).render(ctx),
                          settings.DEFAULT_FROM_EMAIL,
                          [settings.DEFAULT_STUDIO_EMAIL],
                          fail_silently=False)

                ActivityLog.objects.create(
                    log='Email sent to studio ({}) regarding booking for '
                        'block {} (for {})'.format(
                            settings.DEFAULT_STUDIO_EMAIL, block.name,
                            self.request.user.username,
                        )
                )
            except Exception as e:
                # send mail to tech support with Exception
                send_support_email(
                    e, __name__, "BookingCreateView - sending studio email"
                )

            return HttpResponseRedirect(reverse('flexbookings:payments_pending'))

        else:
            try:
                cancelled_booking = Booking.objects.get(
                    user=self.request.user,
                    event=booking.event,
                    status='CANCELLED'
                    )
                booking = cancelled_booking
                booking.status = 'OPEN'
                previously_cancelled = True
            except Booking.DoesNotExist:
                previously_cancelled = False

            # transaction_id = None
            # invoice_id = None
            #
            # if previously_cancelled and booking.paid:
                # pptrans = PaypalBookingTransaction.objects.filter(booking=booking)\
                #     .exclude(transaction_id__isnull=True)
                # if pptrans:
                #     transaction_id = pptrans[0].transaction_id
                #     invoice_id = pptrans[0].invoice_id

            booking.user = self.request.user
            booking.cost = booking.event.cost
            try:
                booking.save()
                ActivityLog.objects.create(
                    log='Booking {} {} for "{}" by user {}'.format(
                        booking.id,
                        'created' if not previously_cancelled else 'rebooked',
                        booking.event, booking.user.username)
                )
            except IntegrityError:
                logger.warning(
                    'Integrity error; redirected to duplicate booking page'
                )
                return HttpResponseRedirect(reverse('flexbookings:duplicate_booking',
                                                    args=[self.event.slug]))
            except BookingError:
                return HttpResponseRedirect(reverse('flexbookings:fully_booked',
                                                    args=[self.event.slug]))

            host = 'http://{}'.format(self.request.META.get('HTTP_HOST'))
            # send email to user
            ctx = {
                'host': host,
                'booking': booking,
                'event': booking.event,
                'date': booking.event.date.strftime('%A %d %B'),
                'time': booking.event.date.strftime('%H:%M'),
                'prev_cancelled_and_direct_paid':
                 previously_cancelled and booking.paid,
                'ev_type': 'workshop' if
                 self.event.event_type.event_type == 'EV' else 'class'
            }
            try:
                send_mail('{} Booking for {}'.format(
                    settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, booking.event.name),
                    get_template('flex_bookings/email/booking_received.txt').render(ctx),
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.user.email],
                    html_message=get_template(
                        'flex_bookings/email/booking_received.html'
                        ).render(ctx),
                    fail_silently=False)
                ActivityLog.objects.create(
                    log='Email sent to user {} regarding {}booking id {} '
                    '(for {})'.format(
                        booking.user.username,
                        're' if previously_cancelled else '', booking.id, booking.event
                    )
                )
            except Exception as e:
                # send mail to tech support with Exception
                send_support_email(e, __name__, "BookingCreateView")

            # send email to studio if flagged for the event or if previously
            # cancelled and direct paid
            if booking.event.email_studio_when_booked or \
                    (previously_cancelled and booking.paid):
                additional_subject = ""
                if previously_cancelled and booking.paid:
                    additional_subject = "ACTION REQUIRED!"
                try:
                    send_mail('{} {} {} {} has just booked for {}'.format(
                        settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, additional_subject,
                        booking.user.first_name, booking.user.last_name, booking.event.name),
                              get_template(
                                'flex_bookings/email/to_studio_booking.txt'
                                ).render(
                                  {
                                      'host': host,
                                      'booking': booking,
                                      'event': booking.event,
                                      'date': booking.event.date.strftime('%A %d %B'),
                                      'time': booking.event.date.strftime('%H:%M'),
                                      'prev_cancelled_and_direct_paid':
                                      previously_cancelled and booking.paid,
                                      # 'transaction_id': transaction_id,
                                      # 'invoice_id': invoice_id
                                  }
                              ),
                              settings.DEFAULT_FROM_EMAIL,
                              [settings.DEFAULT_STUDIO_EMAIL],
                              fail_silently=False)

                    ActivityLog.objects.create(
                        log = 'Email sent to studio ({}) regarding {}booking id {} '
                        '(for {})'.format(
                            settings.DEFAULT_STUDIO_EMAIL,
                            're' if previously_cancelled else '', booking.id,
                            booking.event
                        )
                    )
                except Exception as e:
                    # send mail to tech support with Exception
                    send_support_email(e, __name__, "BookingCreateView - sending studio email")

            messages.success(
                self.request,
                self.success_message.format(booking.event)
            )

            if previously_cancelled and booking.paid:
                messages.info(
                    self.request, 'You previously paid for this booking; your '
                                  'booking will remain as pending until the '
                                  'organiser has reviewed your payment status.'
                )

            try:
                waiting_list_user = WaitingListUser.objects.get(
                    user=booking.user, event=booking.event
                )
                waiting_list_user.delete()
                ActivityLog.objects.create(
                    log='User {} has been removed from the waiting list '
                    'for {}'.format(
                        booking.user.username, booking.event
                    )
                )
            except WaitingListUser.DoesNotExist:
                pass

            if "book_one_off" in form.data and booking.event.cost > 0:
                return HttpResponseRedirect(
                    reverse('flexbookings:payments_pending')
                )
            return HttpResponseRedirect(reverse('flexbookings:bookings'))


@login_required
def update_block(request, pk):

    block = get_object_or_404(Block, id=pk)
    user = request.user
    user_bookings = [
        bk for bk in block.bookings.all() if bk.user == user and
                        bk.status == 'OPEN'
        ]
    for booking in user_bookings:
        # mark all the user's bookings for this block as paid;
        # payment_confirmed will be done by the organiser
        booking.paid = True
        booking.save()

    # send email to studio
    host = 'http://{}'.format(request.META.get('HTTP_HOST'))
    ctx = {
        'host': host,
        'user': request.user,
        'block_obj': block
    }
    try:
        send_mail('{} Payment confirmed for {} by {} {}'.format(
            settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, block.name,
            request.user.first_name, request.user.last_name
        ),
            get_template(
                'flex_bookings/email/to_studio_payment_confirmed.txt'
            ).render(ctx),
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_STUDIO_EMAIL],
            fail_silently=False)
    except Exception as e:
        # send mail to tech support with Exception
        send_support_email(e, __name__, "update_block - email to studio")

    messages.success(
        request, "Thank you for confirming you have made Payment for "
                 "block {}.  The studio has been informed and your space "
                 "will be secured for the relevant classes once payment has "
                 "been reviewed and confirmed.".format(block)
    )

    return HttpResponseRedirect(reverse('flexbookings:bookings'))


@login_required
def update_booking(request, pk):

    booking = get_object_or_404(Booking, id=pk)
    booking.paid = True
    booking.save()

    messages.success(
        request, "Thank you for confirming you have made Payment for "
                 "{}.  The studio has been informed and your space "
                 "will be secured once payment has "
                 "been reviewed and confirmed.".format(booking.event)
    )

    # send email to studio
    host = 'http://{}'.format(request.META.get('HTTP_HOST'))
    ctx = {
        'host': host,
        'user': request.user,
        'booking': booking
    }
    try:
        send_mail('{} Payment confirmed for {} by {} {}'.format(
            settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, booking.event,
            request.user.first_name, request.user.last_name
        ),
            get_template(
                'flex_bookings/email/to_studio_payment_confirmed.txt'
            ).render(ctx),
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_STUDIO_EMAIL],
            fail_silently=False)
    except Exception as e:
        # send mail to tech support with Exception
        send_support_email(e, __name__, "update_booking - email to studio")

    return HttpResponseRedirect(reverse('flexbookings:bookings'))


@login_required
def payments_pending(request):
    unpaid_bookings = Booking.objects.filter(
        user=request.user, status='OPEN', paid=False
    )
    unpaid_booked_events = [booking.event for booking in unpaid_bookings]

    blocks = []
    unpaid_single_bookings = []

    for booking in unpaid_bookings:
        if booking.event in unpaid_booked_events and booking.block:
            blocks.append(booking.block)
        else:
            invoice_id = create_booking_paypal_transaction(
            request.user, booking).invoice_id
            host = 'http://{}'.format(request.META.get('HTTP_HOST'))
            paypal_form = PayPalPaymentsListForm(
                initial=context_helpers.get_paypal_dict(
                    host,
                    booking.cost,
                    booking.event,
                    invoice_id,
                    'userid {} {} {}'.format(
                        request.user.id, 'booking', booking.id
                    )
                )
            )
            unpaid_booking = {
                'booking': booking,
                'paypalform': paypal_form
                }
            unpaid_single_bookings.append(unpaid_booking)

    unpaid_blocks = []
    for block in set(blocks):
        invoice_id = create_block_paypal_transaction(
            request.user, block).invoice_id
        host = 'http://{}'.format(request.META.get('HTTP_HOST'))
        paypal_form = PayPalPaymentsListForm(
            initial=context_helpers.get_paypal_dict(
                host,
                block.item_cost * block.events.count(),
                block.name,
                invoice_id,
                'userid {} {} {}'.format(request.user.id, 'block', block.id)
            )
        )
        unpaid_block = {
            'block': block,
            'paypalform': paypal_form
            }
        unpaid_blocks.append(unpaid_block)


    context = {
        'unpaid_blocks': unpaid_blocks,
        'unpaid_bookings': unpaid_single_bookings
    }

    return TemplateResponse(
        request, 'flex_bookings/payments_pending.html', context
    )


class BookingDeleteView(LoginRequiredMixin, DeleteView):
    model = Booking
    template_name = 'flex_bookings/delete_booking.html'
    success_message = 'Booking cancelled for:</br> {}'

    def get(self, request, *args, **kwargs):
        # redirect if cancellation period past
        booking = get_object_or_404(Booking, pk=self.kwargs['pk'])
        if not booking.event.can_cancel():
            return HttpResponseRedirect(
                reverse('flexbookings:cancellation_period_past',
                        args=[booking.event.slug])
            )
        return super(BookingDeleteView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BookingDeleteView, self).get_context_data(**kwargs)
        booking = get_object_or_404(Booking, pk=self.kwargs['pk'])
        if booking.block:
            context['has_block'] = True
        event = Event.objects.get(id=booking.event.id)
        context['event'] = event

        return context

    def delete(self, request, *args, **kwargs):
        booking = self.get_object()
        block = booking.block

        if 'cancel_block' in request.POST:
            cancel_type = 'block'
            bookings = [
                bk for bk in request.user.bookings.all() if
                bk.block == block and bk.event.date > timezone.now() and
                booking.status == 'OPEN'
                ]
        else:
            cancel_type = 'single'
            bookings = [booking]

        for booking in bookings:
            event_was_full = booking.event.spaces_left() == 0
            booking.status = 'CANCELLED'
            # set block back to None.  If user decides to rebook later, they
            # can either rebook the entire block if it hasn't started yet, or
            # book single class at the individual rate
            booking.block = None
            # set payment confirmed to False but leave paid unchanged; email
            # will be sent to studio to confirm refunded and mark as unpaid
            booking.payment_confirmed = False
            booking.save()
            # if applicable, email users on waiting list
            if event_was_full:
                waiting_list_users = WaitingListUser.objects.filter(
                    event=booking.event
                )
                if waiting_list_users:
                    try:
                        send_waiting_list_email(
                            booking.event,
                            [wluser.user for wluser in waiting_list_users],
                            host='http://{}'.format(request.META.get('HTTP_HOST'))
                        )
                        ActivityLog.objects.create(
                            log='Waiting list email sent to user(s) {} for '
                            'event {}'.format(
                                ', '.join(
                                    [wluser.user.username for \
                                    wluser in waiting_list_users]
                                ),
                                booking.event
                            )
                        )
                    except Exception as e:
                        # send mail to tech support with Exception
                        send_support_email(e, __name__, "DeleteBookingView - waiting list email")
                        messages.error(self.request, "An error occured, please contact "
                            "the studio for information")
        # messages
        # logs
        if cancel_type == 'single':
            ActivityLog.objects.create(
                log='Booking id {} for event {}, user {}, was '
                    'cancelled'.format(
                    bookings[0].id, bookings[0].event, request.user.username
                )
            )
            messages.success(
                self.request,
                mark_safe(self.success_message.format(bookings[0].event))
            )
        else:
            ActivityLog.objects.create(
                log='User {} cancelled bookings from block {}: Booking '
                    'ids {}'.format(
                        request.user.username, block.name,
                        ', '.join(['{} ({})'.format(booking.id, booking.event)
                                   for booking in bookings])
                )
            )
            messages.success(
                self.request,
                mark_safe(self.success_message.format(
                    '</br>'.join(['{}'.format(booking.event)
                                   for booking in bookings])
                    )
                )
            )

        # send emails
        host = 'http://{}'.format(self.request.META.get('HTTP_HOST'))
        # send email to user

        ctx = {
            'host': host,
            'bookings': bookings,
            'block_obj': block,
            'user': request.user,
            'contact_person': bookings[0].event.contact_person,
            'contact_email': bookings[0].event.contact_email,
        }
        subject = "Block {} cancelled".format(block.name) \
            if cancel_type == 'block' \
            else "Booking for {} cancelled".format(bookings[0].event)
        try:
            send_mail('{} {}'.format(
                settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, subject),
                get_template('flex_bookings/email/booking_cancelled.txt').render(ctx),
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                html_message=get_template(
                    'flex_bookings/email/booking_cancelled.html').render(ctx),
                fail_silently=False)
        except Exception as e:
            # send mail to tech support with Exception
            send_support_email(e, __name__, "DeleteBookingView - cancelled email")

        try:
            subject = "block {}".format(block) if cancel_type == 'block' else \
                "a booking for {}".format(bookings[0].event)
            # send email to studio
            send_mail('{} {} {} has just cancelled {}'.format(
                settings.ACCOUNT_EMAIL_SUBJECT_PREFIX,
                'ACTION REQUIRED!' if not block else '',
                request.user.username, subject),
                get_template(
                  'flex_bookings/email/to_studio_booking_cancelled.txt'
                ).render(ctx),
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_STUDIO_EMAIL],
                fail_silently=False)
        except Exception as e:
            # send mail to tech support with Exception
            send_support_email(
                e, __name__, "DeleteBookingView - cancelled email to studio"
            )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('flexbookings:bookings')


def duplicate_booking(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    context = {'event': event}
    return render(request, 'flex_bookings/duplicate_booking.html', context)


def fully_booked(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    ev_type = 'class' if event.event_type.event_type == 'CL' else 'workshop'
    context = {'event': event, 'ev_type': ev_type}
    return render(request, 'flex_bookings/fully_booked.html', context)


def booking_not_open(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    ev_type = 'class' if event.event_type.event_type == 'CL' else 'workshop'
    return render(
        request, 'flex_bookings/booking_not_open.html',
        {'ev_type': ev_type}
    )


def cancellation_period_past(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    context = {'event': event}
    return render(request, 'flex_bookings/cancellation_period_past.html', context)

