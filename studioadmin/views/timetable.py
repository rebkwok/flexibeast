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
from flex_bookings import utils
from flex_bookings.email_helpers import send_support_email, send_waiting_list_email

from timetable.models import Session
from studioadmin.forms import DAY_CHOICES, SessionAdminForm, \
    TimetableSessionFormSet, UploadTimetableForm
from studioadmin.views.utils import staff_required, StaffUserMixin

from activitylog.models import ActivityLog


logger = logging.getLogger(__name__)



@login_required
@staff_required
def timetable_admin_list(request):

    if request.method == 'POST':
        sessionformset = TimetableSessionFormSet(request.POST)

        if sessionformset.is_valid():
            if not sessionformset.has_changed():
                messages.info(request, "No changes were made")
            else:
                for form in sessionformset:
                    if form.has_changed():
                        if 'DELETE' in form.changed_data:
                            messages.success(
                                request, mark_safe(
                                    'Session <strong>{} {} {}</strong> has '
                                    'been deleted!'.format(
                                        form.instance.name,
                                        DAY_CHOICES[form.instance.day],
                                        form.instance.time.strftime('%H:%M')
                                    )
                                )
                            )
                            ActivityLog.objects.create(
                                log='Session {} (id {}) deleted by admin '
                                    'user {}'.format(
                                    form.instance, form.instance.id,
                                    request.user.username
                                )
                            )
                        else:
                            for field in form.changed_data:
                                messages.success(
                                    request, mark_safe(
                                        "<strong>{}</strong> updated for "
                                        "<strong>{}</strong>".format(
                                            field.title().replace("_", " "),
                                            form.instance
                                            )
                                    )
                                )
                                ActivityLog.objects.create(
                                    log='Session {} (id {}) updated by admin '
                                        'user {}: field_changed: {}'.format(
                                            form.instance, form.instance.id,
                                            request.user.username,
                                            field.title().replace("_", " ")
                                        )
                                    )
                        form.save()

                    for error in form.errors:
                        messages.error(request, mark_safe("{}".format(error)))
                sessionformset.save()
            return HttpResponseRedirect(
                reverse('studioadmin:timetable')
            )
        else:
            messages.error(
                request,
                mark_safe(
                    "There were errors in the following fields:\n{}".format(
                        '\n'.join(
                            ["{}".format(error) for error
                             in sessionformset.errors]
                        )
                    )
                )
            )

    else:
        sessionformset = TimetableSessionFormSet(
            queryset=Session.objects.all().order_by('day', 'time')
        )

    return render(
        request, 'studioadmin/timetable_list.html', {
            'sessionformset': sessionformset,
            'sidenav_selection': 'timetable'
            }
    )


class TimetableSessionUpdateView(
    LoginRequiredMixin, StaffUserMixin, UpdateView
):

    form_class = SessionAdminForm
    model = Session
    template_name = 'studioadmin/session_create_update.html'
    context_object_name = 'session'

    def get_object(self):
        queryset = Session.objects.all()
        return get_object_or_404(queryset, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(
            TimetableSessionUpdateView, self
        ).get_context_data(**kwargs)
        context['sidenav_selection'] = 'timetable'
        context['session_day'] = DAY_CHOICES[self.object.day]

        return context

    def form_valid(self, form):
        if form.has_changed():
            session = form.save()
            msg = 'Session <strong>{} {} {}</strong> has been updated!'.format(
                session.name, DAY_CHOICES[session.day],
                session.time.strftime('%H:%M')
            )
            ActivityLog.objects.create(
                log='Session {} (id {}) updated by admin user {}'.format(
                    session, session.id, self.request.user.username
                )
            )
        else:
            msg = 'No changes made'
        messages.success(self.request, mark_safe(msg))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:timetable')


class TimetableSessionCreateView(
    LoginRequiredMixin, StaffUserMixin, CreateView
):

    form_class = SessionAdminForm
    model = Session
    template_name = 'studioadmin/session_create_update.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super(
            TimetableSessionCreateView, self
        ).get_context_data(**kwargs)
        context['sidenav_selection'] = 'add_session'
        return context

    def form_valid(self, form):
        session = form.save()
        msg = 'Session <strong>{} {} {}</strong> has been created!'.format(
            session.name, DAY_CHOICES[session.day],
            session.time.strftime('%H:%M')
        )
        ActivityLog.objects.create(
            log='Session {} (id {}) created by admin user {}'.format(
                session, session.id, self.request.user.username
            )
        )
        messages.success(self.request, mark_safe(msg))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:timetable')


@login_required
@staff_required
def upload_timetable_view(
        request, template_name="studioadmin/upload_timetable_form.html"
):
    if request.method == 'POST':
        form = UploadTimetableForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            session_ids = form.cleaned_data['sessions']

            created_classes, existing_classes = \
                utils.upload_timetable(
                    start_date, end_date, session_ids, request.user
                )
            context = {'start_date': start_date,
                       'end_date': end_date,
                       'created_classes': created_classes,
                       'existing_classes': existing_classes,
                       'sidenav_selection': 'upload_timetable'}
            return render(
                request, 'studioadmin/upload_timetable_confirmation.html',
                context
            )
    else:
        form = UploadTimetableForm()
    return render(request, template_name,
                  {'form': form, 'sidenav_selection': 'upload_timetable'})