import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.shortcuts import HttpResponseRedirect, HttpResponse, redirect, \
    render, get_object_or_404
from django.views.generic import \
    CreateView, ListView, UpdateView, DeleteView
from django.template.response import TemplateResponse
from django.utils import timezone
from django.core.mail import send_mail

from braces.views import LoginRequiredMixin

from flex_bookings.models import Booking, Block
from studioadmin.views.utils import StaffUserMixin, staff_required

from activitylog.models import ActivityLog

logger = logging.getLogger(__name__)


@login_required
@staff_required
def confirm_user_booking_payment(request, pk):

    template = 'studioadmin/confirm_payment.html'
    booking = get_object_or_404(Booking, id=pk)

    if request.method == 'POST' and 'confirm' in request.POST:
        booking.paid = True
        booking.payment_confirmed = True
        booking.save()

        messages.success(
            request, "Payment confirmed for {}, user {} {} ({})".format(
                booking.event, booking.user.first_name,
                booking.user.last_name, booking.user.username
            )
        )

        ctx = {
            'event': booking.event,
            'host': 'http://{}'.format(request.META.get('HTTP_HOST')),
            'user': booking.user
        }
        try:
            send_mail(
                '{} Payment status updated for {}'.format(
                    settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, booking.event),
                get_template(
                    'studioadmin/email/confirm_payment.txt').render(ctx),
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                html_message=get_template(
                    'studioadmin/email/confirm_payment.html').render(ctx),
                fail_silently=False)
        except Exception as e:
            logger.error(
                    'EXCEPTION "{}"" while sending email for booking payment '
                    'confirmation - booking id {} - user {}'
                    'id {}'.format(e, booking.id, booking.user.username)
                    )

        ActivityLog(log='Payment for event {} (booking id {}) for  '
            'user {} has been confirmed by admin user {}'.format(
                booking.event, booking.id, booking.user.username,
                request.user.username
            )
        )

        return HttpResponseRedirect(reverse('studioadmin:users'))

    return TemplateResponse(request, template, {'booking': booking})


@login_required
@staff_required
def confirm_user_block_payment(request, user_id, block_id):

    template = 'studioadmin/confirm_block_payment.html'
    user = get_object_or_404(User, id=user_id)
    block = get_object_or_404(Block, id=block_id)

    if request.method == 'POST' and 'confirm' in request.POST:
        user_block_bookings = Booking.objects.filter(user=user, block=block)
        for booking in user_block_bookings:
            booking.paid = True
            booking.payment_confirmed = True
            booking.save()

        messages.success(
            request, "Payment confirmed for {}, user {} {} ({})".format(
                block.name, user.first_name, user.last_name, user.username)
            )

        ctx = {
            'block_obj': block,
            'host': 'http://{}'.format(request.META.get('HTTP_HOST')),
            'user': user
        }
        try:
            send_mail(
                '{} Payment status updated for {}'.format(
                    settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, block.name),
                get_template(
                    'studioadmin/email/confirm_block_payment.txt').render(ctx),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=get_template(
                    'studioadmin/email/confirm_block_payment.html').render(ctx),
                fail_silently=False)
        except Exception as e:
            logger.error(
                    'EXCEPTION "{}"" while sending email for block payment '
                    'confirmation - block id {} - user {}'
                    'id {}'.format(e, block.id, user.username)
                    )

        ActivityLog(log='Payment for block {} (id {}) for  '
            'user {} has been confirmed by admin user {}'.format(
                block.name, block.id, user.username, request.user.username
            )
        )

        return HttpResponseRedirect(reverse('studioadmin:users'))

    return TemplateResponse(
        request, template, {'user': user, 'block_obj': block}
    )


class ConfirmRefundView(LoginRequiredMixin, StaffUserMixin, UpdateView):

    model = Booking
    template_name = 'studioadmin/confirm_refunded.html'
    success_message = "Refund of payment for {}'s booking for {} has been " \
                      "confirmed.  An update email has been sent to {}."
    fields = ('id',)


    def form_valid(self, form):
        booking = form.save(commit=False)

        if 'confirmed' in self.request.POST:
            booking.paid = False
            booking.payment_confirmed = False
            booking.date_payment_confirmed = None
            booking.save()

            messages.success(
                self.request,
                self.success_message.format(booking.user.username,
                                            booking.event,
                                            booking.user.username)
            )

            ctx = {
                'event': booking.event,
                'host': 'http://{}'.format(self.request.META.get('HTTP_HOST'))
            }

            send_mail(
                '{} Payment refund confirmed for {}'.format(
                    settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, booking.event),
                get_template('studioadmin/email/confirm_refund.txt').render(ctx),
                settings.DEFAULT_FROM_EMAIL,
                [self.request.user.email],
                html_message=get_template(
                    'studioadmin/email/confirm_refund.html').render(ctx),
                fail_silently=False)

            ActivityLog(
                log='Payment refund for booking id {} for event {}, '
                    'user {} has been updated by admin user {}'.format(
                    booking.id, booking.event, booking.user.username,
                    self.request.user.username
                )
            )

        if 'cancelled' in self.request.POST:
            messages.info(
                self.request,
                "Cancelled; no changes to payment status for {}'s booking "
                "for {}".format(booking.user.username, booking.event)
            )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:users')

