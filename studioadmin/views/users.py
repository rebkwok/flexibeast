import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponseRedirect, HttpResponse, redirect, \
    render, get_object_or_404
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import send_mail

from braces.views import LoginRequiredMixin

from activitylog.models import ActivityLog
# from flex_bookings.models import Event, Booking, Block, WaitingListUser, \
#     BookingError
# from flex_bookings.email_helpers import send_support_email, \
#     send_waiting_list_email
# from studioadmin.forms import BookingStatusFilter, UserBookingFormSet, \
#     UserBlockFormSet
from studioadmin.views.utils import StaffUserMixin, staff_required
from website.models import RestrictedAccessTracker


logger = logging.getLogger(__name__)


class UserListView(LoginRequiredMixin, StaffUserMixin, ListView):
    model = User
    template_name = 'studioadmin/user_list.html'
    context_object_name = 'users'
    queryset = User.objects.all().order_by('first_name')

    def get(self, request, *args, **kwargs):
        perm = Permission.objects.get(codename='can_view_restricted')
        if 'remove_all' in self.request.GET:
            users = [
                user for user in User.objects.all() if
                user.has_perm('website.can_view_restricted')
                ]
            RestrictedAccessTracker.objects.all().delete()
            if users:
                for user in users:
                    if not user.is_staff:
                        user.user_permissions.remove(perm)
                messages.success(
                    request,
                    "Restricted access permission has been removed for all "
                    "users (except staff and superusers)"
                )
                ActivityLog.objects.create(
                    log='Restricted access permission has been removed for all '
                        'users (except staff and superusers) by admin user {}'.format(request.user.username)
                )
            else:
                messages.error(
                    request,
                    "No users currently have restricted access permission"
                )


        if 'change_user' in self.request.GET:
            change_user_id = self.request.GET.getlist('change_user')[0]
            user_to_change = User.objects.get(id=change_user_id)
            can_view_restricted = user_to_change.has_perm(
                'website.can_view_restricted'
            )
            if can_view_restricted:
                user_to_change.user_permissions.remove(perm)
                RestrictedAccessTracker.objects.filter(
                    user=user_to_change
                ).delete()
                if user_to_change.is_superuser:
                    messages.error(
                        request,
                        "{} {} ({}) is a superuser; you cannot remove "
                        "permissions".format(
                            user_to_change.first_name,
                            user_to_change.last_name,
                            user_to_change.username
                        )
                    )
                else:
                    messages.success(
                        request,
                        "Permission to view restricted pages removed for "
                        "{} {} ({}) and timer stopped".format(
                            user_to_change.first_name,
                            user_to_change.last_name,
                            user_to_change.username
                        )
                    )
                    ActivityLog.objects.create(
                        log="Permission to view restricted pages "
                            "has been removed for {} {} ({}) by admin "
                            "user {}".format(
                            user_to_change.first_name,
                            user_to_change.last_name,
                            user_to_change.username,
                            request.user.username
                        )
                    )

            else:
                user_to_change.user_permissions.add(perm)
                tracker, created = RestrictedAccessTracker.objects.get_or_create(
                    user=user_to_change
                )
                if not created:
                    tracker.start_date = timezone.now()
                    tracker.save()
                messages.success(
                    request,
                    "Permission to view restricted pages has been added for "
                    "{} {} ({}) and timer started".format(
                        user_to_change.first_name,
                        user_to_change.last_name,
                        user_to_change.username
                    )
                )
                ActivityLog.objects.create(
                    log="Permission to view restricted pages has been added "
                        "for {} {} ({}) by admin user {}".format(
                        user_to_change.first_name,
                            user_to_change.last_name,
                            user_to_change.username,
                            request.user.username
                        )
                )
            user_to_change.save()
            return HttpResponseRedirect(reverse('studioadmin:users'))

        return super(UserListView, self).get(request, *args, **kwargs)

    def get_context_data(self):
        context = super(UserListView, self).get_context_data()
        context['sidenav_selection'] = 'users'
        return context


# @login_required
# @staff_required
# def user_bookings_view(request, user_id, booking_status='future'):
#     user = get_object_or_404(User, id=user_id)
#
#     msg_texts = {
#         'no change':  "No changes were made",
#         'send_conf_no_change': "'Send confirmation' checked for '{}' "
#                                "but no changes were made; email has not "
#                                "been sent to user.",
#         'bk_error': '<span class="cancel-warning">ERROR:</span> Booking '
#                     'cannot be made for fully booked event {}',
#     }
#
#     if request.method == 'POST':
#         booking_status = request.POST.getlist('booking_status')[0]
#         userbookingformset = UserBookingFormSet(
#             request.POST, instance=user, user=user,
#         )
#         if userbookingformset.is_valid():
#             if not userbookingformset.has_changed() and \
#                     request.POST.get('formset_submitted'):
#                 messages.info(request, msg_texts['no change'])
#             else:
#                 for form in userbookingformset:
#                     if form.is_valid() and form.has_changed():
#                         if form.changed_data == ['send_confirmation']:
#                             messages.info(
#                                 request, msg_texts['send_conf_no_change']
#                                     .format(form.instance.event)
#                             )
#                         else:
#                             booking = form.save(commit=False)
#                             was_full = booking.event.spaces_left() == 0
#                             action = 'updated' if form.instance.id else 'created'
#                             if 'status' in form.changed_data and action == 'updated':
#                                 if booking.status == 'CANCELLED':
#                                     if not booking.block:
#                                         booking.paid = False
#                                         booking.payment_confirmed = False
#                                     action = 'cancelled'
#                                 elif booking.status == 'OPEN':
#                                     action = 'reopened'
#
#                             if 'paid' in form.changed_data:
#                                 if booking.paid:
#                                     # assume that if booking is being done via
#                                     # studioadmin, marking paid also means payment
#                                     # is confirmed
#                                     booking.payment_confirmed = True
#                                 else:
#                                     booking.payment_confirmed = False
#
#                             # save the form
#                             try:
#                                 booking.save()
#                             except BookingError:
#                                 messages.error(
#                                     request,
#                                     mark_safe(msg_texts['bk_error'].format(
#                                         booking.event
#                                     ))
#                                 )
#                             else:
#                                 _process_confirmation_email(
#                                     request, form, booking, action
#                                 )
#
#                                 ActivityLog.objects.create(
#                                     log='Booking id {} (user {}) for "{}" {} '
#                                             'by admin user {}'.format(
#                                         booking.id, booking.user.username,
#                                         booking.event,
#                                         action, request.user.username
#                                     )
#                                 )
#
#                                 _process_warning_msgs_and_waiting_list(
#                                     request, booking, action, was_full
#                                 )
#                     else:
#                         for error in form.errors:
#                             messages.error(request, mark_safe("{}".format(error)))
#
#                     userbookingformset.save(commit=False)
#
#             return HttpResponseRedirect(
#                 reverse(
#                     'studioadmin:user_bookings_list',
#                     kwargs={
#                         'user_id': user.id,
#                         'booking_status': booking_status
#                     }
#                 )
#             )
#         else:
#             messages.error(request,mark_safe(
#                     "There were errors in the following fields:\n{}".format(
#                         '\n'.join(
#                             ["{}".format(error) for error in
#                              userbookingformset.errors]
#                         )
#                     )
#             ))
#     else:
#         all_bookings = Booking.objects.filter(user=user)
#         if booking_status == 'all':
#             queryset = all_bookings
#         elif booking_status == 'past':
#             queryset = all_bookings.filter(event__date__lt=timezone.now()).\
#                 order_by('event__date')
#         else:
#             # 'future' by default
#             queryset = all_bookings.filter(event__date__gte=timezone.now()).\
#                 order_by('event__date')
#
#         userbookingformset = UserBookingFormSet(
#             instance=user,
#             queryset=queryset,
#             user=user
#         )
#
#     booking_status_filter = BookingStatusFilter(
#         initial={'booking_status': booking_status}
#     )
#
#     template = 'studioadmin/user_booking_list.html'
#     return TemplateResponse(
#         request, template, {
#             'userbookingformset': userbookingformset, 'user': user,
#             'sidenav_selection': 'users',
#             'booking_status_filter': booking_status_filter,
#             'booking_status': booking_status
#         }
#     )
#
#
# def _process_confirmation_email(request, form, booking, action):
#
#     if 'send_confirmation' in form.changed_data:
#
#         try:
#             # send confirmation email
#             host = 'http://{}'.format(request.META.get('HTTP_HOST'))
#             # send email to studio
#             ctx = {
#                 'host': host,
#                 'event': booking.event,
#                 'user': booking.user,
#                 'action': action,
#             }
#             send_mail('{} Your booking for {} has been {}'.format(
#                 settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, booking.event, action
#                 ),
#                 get_template(
#                     'studioadmin/email/booking_change_confirmation.txt'
#                 ).render(ctx),
#                 settings.DEFAULT_FROM_EMAIL,
#                 [booking.user.email],
#                 html_message=get_template(
#                     'studioadmin/email/booking_change_confirmation.html'
#                     ).render(ctx),
#                 fail_silently=False)
#             send_confirmation_msg = "and confirmation email sent to user"
#         except Exception as e:
#             # send mail to tech support with Exception
#             send_support_email(
#                 e, __name__, "user_booking_list - "
#                 "send confirmation email"
#             )
#             send_confirmation_msg = ". There was a problem sending the " \
#                                     "confirmation email to the user.  Tech " \
#                                     "support has been notified."
#
#     else:
#         send_confirmation_msg = ""
#
#     messages.success(
#         request, 'Booking for {} has been {} {}'.format(
#             booking.event, action, send_confirmation_msg
#         )
#     )
#
#
# def _process_warning_msgs_and_waiting_list(request, booking, action, was_full):
#
#     msg_texts = {
#         'reopen_warning': '<span class="cancel-warning">Payment status has '
#                           'not been automatically updated. Please review the '
#                           'booking and update if paid .</span>',
#         'cancel_warning': 'The booking has automatically been marked as '
#                           'unpaid (refunded)',
#     }
#
#     if action =='reopened' and not booking.block:
#         messages.info(request, mark_safe(msg_texts['reopen_warning']))
#     elif action == 'cancelled' and not  booking.block:
#         messages.info(request, msg_texts['cancel_warning'])
#
#         if was_full:
#             _process_waiting_list(booking, request)
#
#     if action == 'created' or action == 'reopened':
#         try:
#             waiting_list_user = WaitingListUser.objects.get(
#                 user=booking.user, event=booking.event
#             )
#             waiting_list_user.delete()
#             ActivityLog.objects.create(
#                 log='User {} has been removed from the waiting list for {}'
#                     .format(
#                         booking.user.username,
#                         booking.event
#                     )
#                 )
#         except WaitingListUser.DoesNotExist:
#             pass
#
#
# def _process_waiting_list(booking, request):
#     waiting_list_users = WaitingListUser.objects.filter(event=booking.event)
#     if waiting_list_users:
#         try:
#             send_waiting_list_email(
#                 booking.event,
#                 [wluser.user for wluser in waiting_list_users],
#                 host='http://{}'.format(request.META.get('HTTP_HOST'))
#             )
#             ActivityLog.objects.create(
#                 log='Waiting list email sent to user(s) {} for event {}'.
#                     format(', '.join(
#                         [wluser.user.username for wluser in waiting_list_users]
#                     ), booking.event
#                     )
#                 )
#         except Exception as e:
#             # send mail to tech support with Exception
#             send_support_email(
#                 e, __name__, "Automatic cancel job - waiting list email"
#             )
#
# @login_required
# @staff_required
# def block_bookings_view(request):
#
#     userblocks = []
#     for block in Block.objects.all():
#         users = set([booking.user for booking in block.bookings.all()])
#         [userblocks.append({'user': user.id, 'block': block.id}) for user in users]
#
#     if request.method == 'POST':
#         userblocksformset = UserBlockFormSet(request.POST, initial=userblocks)
#
#         if userblocksformset.is_valid():
#             if not userblocksformset.has_changed():
#                 # don't report this message if form is empty
#                 messages.info(request, 'No changes made')
#
#             else:
#                 for form in userblocksformset:
#                     if form.is_valid() and form.has_changed():
#                         if form.changed_data == ['send_confirmation']:
#                             messages.info(
#                                 request,
#                                 "'Send confirmation' checked for '{}' "
#                                "but no changes were made; email has not "
#                                "been sent to user." .format(
#                                     form.instance.event
#                                 )
#                             )
#                         else:
#                             block = form.cleaned_data['block']
#                             user = form.cleaned_data['user']
#
#                             if form.cleaned_data['DELETE']:
#                                 bookings = [
#                                     bk for bk in user.bookings.all()
#                                     if bk.block == block
#                                     and bk.event.date > timezone.now()
#                                     ]
#                                 for booking in bookings:
#                                     was_full = booking.event.spaces_left() == 0
#                                     booking.status = 'CANCELLED'
#                                     booking.save()
#                                     if was_full:
#                                         _process_waiting_list(booking, request)
#
#                                 messages.success(
#                                     request,
#                                     mark_safe(
#                                         'Remaining bookings in block {} have '
#                                         'been cancelled for user {}: '
#                                         '<ul>{}</ul>'.format(
#                                             block.name, user.username,
#                                             ''.join(['<li>{}</li>'.format(bk.event)
#                                                  for bk in bookings])
#                                             )
#                                         )
#                                     )
#                                 ActivityLog.objects.create(
#                                     log='Block {} for user {} cancelled by admin'
#                                         'user {} (booking ids {})'.format(
#                                         block.name, user.username,
#                                         request.user.username,
#                                         ', '.join([str(bk.id) for bk in bookings])
#                                     )
#                                 )
#                                 _process_block_confirmation_email(
#                                     request, user, form, block, 'cancelled'
#                                 )
#                             else:
#                                 for event in block.events.all():
#                                     Booking.objects.create(
#                                         event=event, user=user, block=block,
#                                         paid=True, payment_confirmed=True
#                                     )
#                                     try:
#                                         waiting_list_user = WaitingListUser.objects.get(
#                                             user=user, event=event
#                                         )
#                                         waiting_list_user.delete()
#                                         ActivityLog.objects.create(
#                                             log='User {} has been removed '
#                                                 'from the waiting list for {}'
#                                                 .format(user.username, event)
#                                             )
#                                     except WaitingListUser.DoesNotExist:
#                                         pass
#
#                                 messages.success(
#                                     request,
#                                     'Block {} booked for user {}. Bookings for '
#                                     'classes in this block are marked as paid and'
#                                     ' confirmed'.format(
#                                         block.name, user.username
#                                     )
#                                 )
#                                 ActivityLog.objects.create(
#                                     log='Block {} booked for user {} by admin '
#                                         'user {}'.format(
#                                         block.name, user.username,
#                                         request.user.username
#                                         )
#                                     )
#                                 _process_block_confirmation_email(
#                                     request, user, form, block, 'created'
#                                 )
#                     else:
#                         for error in form.errors:
#                             messages.error(request, mark_safe("{}".format(error)))
#             return HttpResponseRedirect(reverse('studioadmin:block_bookings'))
#
#         else:
#             messages.error(
#                 request, mark_safe(
#                     "There were errors in the following fields:\n{}".format(
#                         '\n'.join(
#                             ["{}".format(error) for error in
#                              userblocksformset.errors]
#                         )
#                     )
#                 )
#             )
#
#     # initial data for UserBlockFormSet needs to be a list of dictionaries
#     # with user and block info
#
#     userblocksformset = UserBlockFormSet(initial=userblocks)
#
#     return TemplateResponse(
#         request,
#         'studioadmin/block_bookings_list.html',
#         {
#             'userblocksformset': userblocksformset,
#             'sidenav_selection': 'block_bookings'
#         }
#     )
#
# def _process_block_confirmation_email(request, user, form, block, action):
#
#     if 'send_confirmation' in form.changed_data:
#
#         try:
#             # send confirmation email
#             host = 'http://{}'.format(request.META.get('HTTP_HOST'))
#             # send email to studio
#             ctx = {
#                 'host': host,
#                 'block': block,
#                 'user': user,
#                 'action': action,
#             }
#             send_mail('{} block {} has been {}'.format(
#                 settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, block.name, action
#                 ),
#                 get_template(
#                     'studioadmin/email/block_change_confirmation.txt'
#                 ).render(ctx),
#                 settings.DEFAULT_FROM_EMAIL,
#                 [user.email],
#                 html_message=get_template(
#                     'studioadmin/email/block_change_confirmation.html'
#                     ).render(ctx),
#                 fail_silently=False)
#         except Exception as e:
#             # send mail to tech support with Exception
#             send_support_email(
#                 e, __name__, "block_bookings_list - "
#                 "send confirmation email"
#             )
