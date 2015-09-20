import urllib.parse
import ast
import logging

from datetime import datetime
from functools import wraps


from django.db.utils import IntegrityError
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template.loader import get_template
from django.template import Context
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponseRedirect, HttpResponse, redirect, \
    render, get_object_or_404
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import send_mail

from braces.views import LoginRequiredMixin

from flex_bookings.models import Event, Booking, Block, WaitingListUser, \
    BookingError
# from flex_bookings import utils
from flex_bookings.email_helpers import send_support_email, send_waiting_list_email

# from timetable.models import Session
# from studioadmin.forms import BookingStatusFilter, \
#     EventFormSet, \
#     EventAdminForm, SimpleBookingRegisterFormSet, StatusFilter, \
#     TimetableSessionFormSet, SessionAdminForm, DAY_CHOICES, \
#     UploadTimetableForm, EmailUsersForm, ChooseUsersFormSet, UserFilterForm, \
#     BlockStatusFilter, UserBookingFormSet, UserBlockFormSet, \
from studioadmin.forms import ActivityLogSearchForm, ConfirmPaymentForm

from activitylog.models import ActivityLog


logger = logging.getLogger(__name__)





#
#
# class BlockListView(LoginRequiredMixin, StaffUserMixin, ListView):
#
#     model = Block
#     template_name = 'studioadmin/block_list.html'
#     context_object_name = 'blocks'
#     default_sort_params = ('block_type', 'asc')
#
#     def get_queryset(self):
#         block_status = self.request.GET.get('block_status', 'current')
#         all_blocks = Block.objects.all()
#         if block_status == 'all':
#             return all_blocks
#         elif block_status == 'current':
#             current = (block.id for block in all_blocks
#                       if not block.expired and not block.full)
#             return Block.objects.filter(id__in=current)
#         elif block_status == 'active':
#             active = (block.id for block in all_blocks if block.active_block())
#             return Block.objects.filter(id__in=active)
#         elif block_status == 'unpaid':
#             unpaid = (block.id for block in all_blocks
#                       if not block.expired and not block.paid
#                       and not block.full)
#             return Block.objects.filter(id__in=unpaid)
#         elif block_status == 'expired':
#             expired = (block.id for block in all_blocks if block.expired or block.full)
#             return Block.objects.filter(id__in=expired)
#
#     def get_context_data(self):
#         context = super(BlockListView, self).get_context_data()
#         context['sidenav_selection'] = 'blocks'
#
#         block_status = self.request.GET.get('block_status', 'current')
#         form = BlockStatusFilter(initial={'block_status': block_status})
#         context['form'] = form
#         context['block_status'] = block_status
#
#         return context
#
#
# @login_required
# @staff_required
# def choose_users_to_email(request,
#                           template_name='studioadmin/choose_users_form.html'):
#
#     initial_userfilterdata={'events': [''], 'lessons': ['']}
#
#     if 'filter' in request.POST:
#         event_ids = request.POST.getlist('filter-events')
#         lesson_ids = request.POST.getlist('filter-lessons')
#
#         if event_ids == ['']:
#             if request.session.get('events'):
#                 del request.session['events']
#             event_ids = []
#         else:
#             request.session['events'] = event_ids
#             initial_userfilterdata['events'] = event_ids
#
#         if lesson_ids == ['']:
#             if request.session.get('lessons'):
#                 del request.session['lessons']
#             lesson_ids = []
#         else:
#             request.session['lessons'] = lesson_ids
#             initial_userfilterdata['lessons'] = lesson_ids
#
#         if not event_ids and not lesson_ids:
#             usersformset = ChooseUsersFormSet(
#                 queryset=User.objects.all().order_by('username'))
#         else:
#             event_and_lesson_ids = event_ids + lesson_ids
#             bookings = Booking.objects.filter(event__id__in=event_and_lesson_ids)
#             user_ids = set([booking.user.id for booking in bookings
#                             if booking.status == 'OPEN'])
#             usersformset = ChooseUsersFormSet(
#                 queryset=User.objects.filter(id__in=user_ids).order_by('username')
#             )
#
#     elif request.method == 'POST':
#         usersformset = ChooseUsersFormSet(request.POST)
#
#         if usersformset.is_valid():
#
#             event_ids = request.session.get('events', [])
#             lesson_ids = request.session.get('lessons', [])
#             users_to_email = []
#
#             for form in usersformset:
#                 # check checkbox value to determine if that user is to be
#                 # emailed; add user_id to list
#                 if form.is_valid():
#                     if form.cleaned_data.get('email_user'):
#                         users_to_email.append(form.instance.id)
#                 else:
#                     for error in form.errors:
#                         messages.error(request, mark_safe("{}".format(error)))
#
#             request.session['users_to_email'] = users_to_email
#
#             return HttpResponseRedirect(url_with_querystring(
#                 reverse('studioadmin:email_users_view'), events=event_ids, lessons=lesson_ids)
#             )
#
#         else:
#             messages.error(
#                 request,
#                 mark_safe(
#                     "There were errors in the following fields:\n{}".format(
#                         '\n'.join(
#                             ["{}".format(error) for error in usersformset.errors]
#                         )
#                     )
#                 )
#             )
#
#     else:
#         usersformset = ChooseUsersFormSet(
#             queryset=User.objects.all().order_by('username'),
#         )
#
#     userfilterform = UserFilterForm(prefix='filter', initial=initial_userfilterdata)
#
#     return TemplateResponse(
#         request, template_name, {
#             'usersformset': usersformset,
#             'userfilterform': userfilterform,
#             'sidenav_selection': 'email_users',
#             }
#     )
#
#
# def url_with_querystring(path, **kwargs):
#     return path + '?' + urllib.parse.urlencode(kwargs)
#
#
# @login_required
# @staff_required
# def email_users_view(request,
#                      template_name='studioadmin/email_users_form.html'):
#
#         users_to_email = User.objects.filter(id__in=request.session['users_to_email'])
#
#         if request.method == 'POST':
#
#             form = EmailUsersForm(request.POST)
#
#             if form.is_valid():
#                 subject = '{} {}'.format(
#                     settings.ACCOUNT_EMAIL_SUBJECT_PREFIX,
#                     form.cleaned_data['subject'])
#                 from_address = form.cleaned_data['from_address']
#                 message = form.cleaned_data['message']
#                 cc = form.cleaned_data['cc']
#
#                 # do this per email address so recipients are not visible to
#                 # each
#                 email_addresses = [user.email for user in users_to_email]
#                 if cc:
#                     email_addresses.append(from_address)
#                 for email_address in email_addresses:
#                     try:
#                         send_mail(subject, message, from_address,
#                               [email_address],
#                               html_message=get_template(
#                                   'studioadmin/email/email_users.html').render(
#                                   Context({
#                                       'subject': subject,
#                                       'message': message})
#                               ),
#                               fail_silently=False)
#                     except Exception as e:
#                         # send mail to tech support with Exception
#                         send_support_email(e, __name__, "Bulk Email to students")
#                         ActivityLog.objects.create(log="Possible error with "
#                             "sending bulk email; notification sent to tech support")
#                 ActivityLog.objects.create(
#                     log='Bulk email with subject "{}" sent to users {} by '
#                         'admin user {}'.format(
#                         subject, email_addresses, request.user.username
#                     )
#                 )
#
#                 return render(request,
#                     'studioadmin/email_users_confirmation.html')
#
#             else:
#                 event_ids = request.session.get('events')
#                 lesson_ids = request.session.get('lessons')
#                 events = Event.objects.filter(id__in=event_ids)
#                 lessons = Event.objects.filter(id__in=lesson_ids)
#                 totaleventids = event_ids + lesson_ids
#                 totalevents = Event.objects.filter(id__in=totaleventids)
#                 messages.error(request, mark_safe("Please correct errors in form: {}".format(form.errors)))
#                 form = EmailUsersForm(initial={'subject': "; ".join((str(event) for event in totalevents))})
#
#         else:
#             event_ids = ast.literal_eval(request.GET.get('events'))
#             events = Event.objects.filter(id__in=event_ids)
#             lesson_ids = ast.literal_eval(request.GET.get('lessons'))
#             lessons = Event.objects.filter(id__in=lesson_ids)
#             totaleventids = event_ids + lesson_ids
#             totalevents = Event.objects.filter(id__in=totaleventids)
#             form = EmailUsersForm(initial={'subject': "; ".join((str(event) for event in totalevents))})
#
#         return TemplateResponse(
#             request, template_name, {
#                 'form': form,
#                 'users_to_email': users_to_email,
#                 'sidenav_selection': 'email_users',
#                 'events': events,
#                 'lessons': lessons
#             }
#         )
#
#

# @login_required
# @staff_required
# def user_blocks_view(request, user_id):
#
#     user = get_object_or_404(User, id=user_id)
#     if request.method == 'POST':
#         userblockformset = UserBlockFormSet(
#             request.POST,
#             instance=user,
#             user=user
#         )
#         if userblockformset.is_valid():
#             if not userblockformset.has_changed():
#                 messages.info(request, "No changes were made")
#             else:
#                 for form in userblockformset:
#                     if form.has_changed():
#
#                         block = form.save(commit=False)
#
#                         if 'DELETE' in form.changed_data:
#                             messages.success(
#                                 request, mark_safe(
#                                     'Block <strong>{}</strong> has been '
#                                     'deleted!  Any bookings made with this '
#                                     'block have been changed to unpaid.  '
#                                     'Please inform user {} ({})'.format(
#                                         block, block.user.username,
#                                         block.user.email
#                                     )
#                                 )
#                             )
#                             ActivityLog.objects.create(
#                                 log='Block {} (id {}) deleted by admin user {}'.format(
#                                 form.instance, form.instance.id, request.user.username)
#                             )
#                             block.delete()
#                         else:
#                             new = False if form.instance.id else True
#                             msg = 'created' if new else 'updated'
#
#                             messages.success(
#                                 request,
#                                 'Block for {} has been {}'.format(
#                                     block.block_type.event_type, msg
#                                 )
#                             )
#                             block.save()
#                             ActivityLog.objects.create(
#                                 log='Block id {} ({}), user {}, has been {}'
#                                         ' by admin user {}'.format(
#                                     block.id, block.block_type,
#                                     block.user.username, msg,
#                                     request.user.username
#                                 )
#                             )
#                     for error in form.errors:
#                         messages.error(request, mark_safe("{}".format(error)))
#                 userblockformset.save(commit=False)
#
#             return HttpResponseRedirect(
#                 reverse('studioadmin:user_blocks_list',
#                         kwargs={'user_id': user.id}
#                         )
#             )
#         else:
#             messages.error(
#                 request,
#                 mark_safe(
#                     "There were errors in the following fields:\n{}".format(
#                         '\n'.join(
#                             ["{}".format(error) for error in userblockformset.errors]
#                         )
#                     )
#                 )
#             )
#     else:
#         queryset = Block.objects.filter(
#             user=user).order_by('start_date')
#         userblockformset = UserBlockFormSet(
#             instance=user,
#             queryset=queryset,
#             user=user
#         )
#
#     template = 'studioadmin/user_block_list.html'
#     return TemplateResponse(
#         request, template, {
#             'userblockformset': userblockformset, 'user': user,
#             'sidenav_selection': 'users'
#         }
#     )






