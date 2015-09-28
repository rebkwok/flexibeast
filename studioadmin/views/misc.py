import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.template import Context
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



class ConfirmPaymentView(LoginRequiredMixin, StaffUserMixin, UpdateView):

    model = Booking
    template_name = 'studioadmin/confirm_payment.html'
    success_message = 'Payment status changed to {}. An update email ' \
                      'has been sent to user {}.'

    def get_initial(self, **kwargs):
        return {
            'payment_confirmed': self.object.payment_confirmed
        }

    def form_valid(self, form):
        if form.has_changed():
            booking = form.save(commit=False)

            if booking.payment_confirmed and 'payment_confirmed' \
                    in form.changed_data:
                # if user leaves paid unchecked but checks payment confirmed
                # as true, booking should be marked as paid
                booking.paid = True
                booking.date_payment_confirmed = timezone.now()

            if not booking.paid and 'paid' in form.changed_data:
                # if booking is changed to unpaid, reset payment_confirmed to
                # False too
                booking.payment_confirmed = False
            booking.save()

            if booking.paid and booking.payment_confirmed:
                payment_status = 'paid and confirmed'
            elif booking.paid:
                payment_status = "paid - payment not confirmed yet"
            else:
                payment_status = 'not paid'

            messages.success(
                self.request,
                self.success_message.format(payment_status, booking.user.username)
            )

            ctx = Context({
                'event': booking.event,
                'host': 'http://{}'.format(self.request.META.get('HTTP_HOST')),
                'payment_status': payment_status
            })
            try:
                send_mail(
                    '{} Payment status updated for {}'.format(
                        settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, booking.event),
                    get_template(
                        'studioadmin/email/confirm_payment.html').render(ctx),
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.user.email],
                    html_message=get_template(
                        'studioadmin/email/confirm_payment.html').render(ctx),
                    fail_silently=False)
            except Exception as e:
                logger.error(
                        'EXCEPTION "{}"" while sending email for booking '
                        'id {}'.format(e, booking.id)
                        )

            ActivityLog(log='Payment status for booking id {} for event {}, '
                'user {} has been updated by admin user {}'.format(
                booking.id, booking.event, booking.user.username,
                self.request.user.username
                )
            )
        else:
            messages.info(
                self.request, "No changes made to the payment "
                              "status for {}'s booking for {}.".format(
                    self.object.user.username, self.object.event)
            )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:users')


@staff_required
@login_required
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

        ctx = Context({
            'event': booking.event,
            'host': 'http://{}'.format(request.META.get('HTTP_HOST')),
            'user': booking.user
        })
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


@staff_required
@login_required
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

        ctx = Context({
            'block_obj': block,
            'host': 'http://{}'.format(request.META.get('HTTP_HOST')),
            'user': user
        })
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


    #
    # def form_valid(self, form):
    #     if form.has_changed():
    #         booking = form.save(commit=False)
    #
    #         if booking.payment_confirmed and 'payment_confirmed' \
    #                 in form.changed_data:
    #             # if user leaves paid unchecked but checks payment confirmed
    #             # as true, booking should be marked as paid
    #             booking.paid = True
    #             booking.date_payment_confirmed = timezone.now()
    #
    #         if not booking.paid and 'paid' in form.changed_data:
    #             # if booking is changed to unpaid, reset payment_confirmed to
    #             # False too
    #             booking.payment_confirmed = False
    #         booking.save()
    #
    #         if booking.paid and booking.payment_confirmed:
    #             payment_status = 'paid and confirmed'
    #         elif booking.paid:
    #             payment_status = "paid - payment not confirmed yet"
    #         else:
    #             payment_status = 'not paid'
    #
    #         messages.success(
    #             self.request,
    #             self.success_message.format(payment_status, booking.user.username)
    #         )
    #
    #         ctx = Context({
    #             'event': booking.event,
    #             'host': 'http://{}'.format(self.request.META.get('HTTP_HOST')),
    #             'payment_status': payment_status
    #         })
    #         try:
    #             send_mail(
    #                 '{} Payment status updated for {}'.format(
    #                     settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, booking.event),
    #                 get_template(
    #                     'studioadmin/email/confirm_payment.html').render(ctx),
    #                 settings.DEFAULT_FROM_EMAIL,
    #                 [booking.user.email],
    #                 html_message=get_template(
    #                     'studioadmin/email/confirm_payment.html').render(ctx),
    #                 fail_silently=False)
    #         except Exception as e:
    #             logger.error(
    #                     'EXCEPTION "{}"" while sending email for booking '
    #                     'id {}'.format(e, booking.id)
    #                     )
    #
    #         ActivityLog(log='Payment status for booking id {} for event {}, '
    #             'user {} has been updated by admin user {}'.format(
    #             booking.id, booking.event, booking.user.username,
    #             self.request.user.username
    #             )
    #         )
    #     else:
    #         messages.info(
    #             self.request, "No changes made to the payment "
    #                           "status for {}'s booking for {}.".format(
    #                 self.object.user.username, self.object.event)
    #         )
    #
    #     return HttpResponseRedirect(self.get_success_url())
    #
    # def get_success_url(self):
    #     return reverse('studioadmin:users')


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

            ctx = Context({
                'event': booking.event,
                'host': 'http://{}'.format(self.request.META.get('HTTP_HOST'))

            })

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

