import urllib.parse
import ast
import logging

from datetime import datetime, time
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

from flex_bookings.models import Event, Booking, Block, WaitingListUser
from studioadmin.forms import EventFormSet, EventAdminForm, RegisterDayForm
from studioadmin.views.utils import StaffUserMixin, staff_required
from activitylog.models import ActivityLog


@login_required
@staff_required
def event_admin_list(request, ev_type):

    ev_type_abbreviation = 'EV' if ev_type == 'events' else 'CL'
    ev_type_text = 'workshop' if ev_type == 'events' else 'class'

    queryset = Event.objects.filter(
        event_type__event_type=ev_type_abbreviation,
        date__gte=timezone.now()
    ).order_by('date')
    events = True if queryset.count() > 0 else False
    show_past = False

    if request.method == 'POST':
        if "past" in request.POST:
            queryset = Event.objects.filter(
                event_type__event_type=ev_type_abbreviation,
                date__lte=timezone.now()
            ).order_by('date')
            events = True if queryset.count() > 0 else False
            show_past = True
            eventformset = EventFormSet(queryset=queryset)
        elif "upcoming" in request.POST:
            queryset = queryset
            show_past = False
            eventformset = EventFormSet(queryset=queryset)
        else:
            eventformset = EventFormSet(request.POST)

            if eventformset.is_valid():
                if not eventformset.has_changed():
                    messages.info(request, "No changes were made")
                else:
                    for form in eventformset:
                        if form.has_changed():
                            if 'DELETE' in form.changed_data:
                                messages.success(
                                    request, mark_safe(
                                        '{} <strong>{}</strong> has been deleted!'.format(
                                            ev_type_text.title(), form.instance,
                                        )
                                    )
                                )
                                ActivityLog.objects.create(
                                    log='{} {} (id {}) deleted by admin user {}'.format(
                                        ev_type_text.title(), form.instance,
                                        form.instance.id, request.user.username
                                    )
                                )
                            else:
                                for field in form.changed_data:
                                    messages.success(
                                        request, mark_safe(
                                            "<strong>{}</strong> updated for "
                                            "<strong>{}</strong>".format(
                                                field.title().replace("_", " "),
                                                form.instance))
                                    )

                                    ActivityLog.objects.create(
                                        log='{} {} (id {}) updated by admin '
                                            'user {}: field_changed: '
                                            '{}'.format(
                                            ev_type_text.title(),
                                            form.instance, form.instance.id,
                                            request.user.username,
                                            field.title().replace("_", " ")
                                        )
                                    )

                            form.save()

                        for error in form.errors:
                            messages.error(request, mark_safe("{}".format(error)))
                    eventformset.save()
                return HttpResponseRedirect(
                    reverse('studioadmin:{}'.format(ev_type),)
                )
            else:
                messages.error(
                    request,
                    mark_safe(
                        "There were errors in the following fields:\n{}".format(
                            '\n'.join(
                                ["{}".format(error) for error in eventformset.errors]
                            )
                        )
                    )
                )

    else:
        eventformset = EventFormSet(queryset=queryset)

    return render(
        request, 'studioadmin/admin_events.html', {
            'eventformset': eventformset,
            'type': ev_type,
            'events': events,
            'sidenav_selection': ev_type,
            'show_past': show_past,
            }
    )


class EventAdminUpdateView(LoginRequiredMixin, StaffUserMixin, UpdateView):

    form_class = EventAdminForm
    model = Event
    template_name = 'studioadmin/event_create_update.html'
    context_object_name = 'event'

    def get_form_kwargs(self, **kwargs):
        form_kwargs = super(EventAdminUpdateView, self).get_form_kwargs(**kwargs)
        form_kwargs['ev_type'] = 'EV' if self.kwargs["ev_type"] == 'event' \
            else 'CL'
        return form_kwargs

    def get_object(self):
        queryset = Event.objects.all()
        return get_object_or_404(queryset, slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super(EventAdminUpdateView, self).get_context_data(**kwargs)
        context['type'] = self.kwargs["ev_type"]
        if self.kwargs["ev_type"] == "lesson":
            context['type'] = "class"
        context['sidenav_selection'] = self.kwargs['ev_type'] + 's'

        return context

    def form_valid(self, form):
        if form.has_changed():
            event = form.save()
            msg_ev_type = 'Workshop' if self.kwargs["ev_type"] == 'event' \
                else 'Class'
            msg = '<strong>{} {}</strong> has been updated!'.format(
                msg_ev_type, event.name
            )
            ActivityLog.objects.create(
                log='{} {} (id {}) updated by admin user {}'.format(
                    msg_ev_type, event, event.id,
                    self.request.user.username
                )
            )
        else:
            msg = 'No changes made'
        messages.success(self.request, mark_safe(msg))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:{}'.format(self.kwargs["ev_type"] + 's'))


class EventAdminCreateView(LoginRequiredMixin, StaffUserMixin, CreateView):

    form_class = EventAdminForm
    model = Event
    template_name = 'studioadmin/event_create_update.html'
    context_object_name = 'event'

    def get_form_kwargs(self, **kwargs):
        form_kwargs = super(EventAdminCreateView, self).get_form_kwargs(**kwargs)
        form_kwargs['ev_type'] = 'EV' if self.kwargs["ev_type"] == 'event' \
            else 'CL'
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super(EventAdminCreateView, self).get_context_data(**kwargs)
        context['type'] = 'workshop' if self.kwargs["ev_type"] == 'event' \
            else "class"
        context['sidenav_selection'] = 'add_{}'.format(self.kwargs['ev_type'])
        return context

    def form_valid(self, form):
        event = form.save()
        msg_ev_type = 'Workshop' if self.kwargs["ev_type"] == 'event' else 'Class'
        messages.success(self.request, mark_safe('<strong>{} {}</strong> has been '
                                    'created!'.format(msg_ev_type, event.name)))
        ActivityLog.objects.create(
            log='{} {} (id {}) created by admin user {}'.format(
                msg_ev_type, event, event.id, self.request.user.username
            )
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:{}'.format(self.kwargs["ev_type"] + 's'))


@login_required
@staff_required
def registers_by_date(request):

    if request.method == 'POST':
        form = RegisterDayForm(request.POST)

        if form.is_valid():
            register_date = form.cleaned_data['register_date']
            register_format = form.cleaned_data['register_format']

            events = Event.objects.filter(
                date__gt=datetime.combine(
                    register_date, time(hour=0, minute=0)
                ).replace(tzinfo=timezone.utc),
                date__lt=datetime.combine(
                    register_date, time(hour=23, minute=59)
                ).replace(tzinfo=timezone.utc),
            )

            new_form = RegisterDayForm(
                initial={'register_date': register_date,
                         'register_format': register_format},
                events=events
            )
            ctx = {'form': new_form, 'sidenav_selection': 'registers_by_date'}

            if not events:
                messages.info(
                    request,
                    'There are no classes/workshops/events on the date '
                    'selected'
                )
                return TemplateResponse(
                    request, "studioadmin/register_day_form.html", ctx
                )

            if 'print' in request.POST:

                if 'select_events' in request.POST:
                    event_ids = form.cleaned_data['select_events']
                    events = Event.objects.filter(
                        id__in=event_ids
                    )
                else:
                    messages.info(
                        request, 'Please select at least one register to print'
                    )
                    form = RegisterDayForm(
                        initial={'register_date': register_date,
                                 'register_format': register_format,
                                 'select_events': []},
                        events=events
                    )
                    return TemplateResponse(
                        request, "studioadmin/register_day_form.html",
                        {
                            'form': form,
                            'sidenav_selection': 'registers_by_date'
                        }
                    )

                eventlist = []
                for event in events:
                    bookings = [
                        booking for booking in
                        Booking.objects.filter(event=event, status='OPEN')
                        ]

                    bookinglist = []
                    for i, booking in enumerate(bookings):
                        booking_ctx = {'booking': booking, 'index': i+1}
                        bookinglist.append(booking_ctx)
                    if event.max_participants:
                        extra_lines = event.spaces_left()
                    elif event.bookings.count() < 15:
                        open_bookings = [
                            event for event in event.bookings.all() if
                            event.status == 'OPEN'
                        ]
                        extra_lines = 15 - len(open_bookings)
                    else:
                        extra_lines = 2

                    event_ctx = {
                        'event': event,
                        'bookings': bookinglist,
                        'extra_lines': extra_lines,
                    }
                    eventlist.append(event_ctx)

                context = {
                    'date': register_date, 'events': eventlist,
                    'sidenav_selection': 'registers_by_date',
                    'register_format': register_format
                }
                template = 'studioadmin/print_multiple_registers.html'
                return TemplateResponse(request, template, context)

            else:
                return TemplateResponse(
                    request, "studioadmin/register_day_form.html", ctx
                )

        else:

            messages.error(
                request,
                mark_safe('Please correct the following errors: {}'.format(
                    form.errors
                ))
            )
            return TemplateResponse(
                    request, "studioadmin/register_day_form.html",
                    {'form': form, 'sidenav_selection': 'registers_by_date'}
                    )

    events = Event.objects.filter(
        date__gt=datetime.now().replace(hour=0, minute=0, tzinfo=timezone.utc),
        date__lt=datetime.now().replace(hour=23, minute=59, tzinfo=timezone.utc),
    )
    form = RegisterDayForm(events=events)

    return TemplateResponse(
        request, "studioadmin/register_day_form.html",
        {'form': form, 'sidenav_selection': 'registers_by_date'}
    )
