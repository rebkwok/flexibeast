import logging

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, \
    get_object_or_404, render_to_response
from django.views.generic import CreateView, ListView, UpdateView
from braces.views import LoginRequiredMixin

from activitylog.models import ActivityLog

from studioadmin.forms import CreateEventForm, TimetableWeeklySessionFormSet, \
    EditSessionForm, EditEventForm, EventsFormSet
from studioadmin.views.utils import StaffUserMixin

from timetable.models import Event, WeeklySession

logger = logging.getLogger(__name__)

EVENT_CHOICES_DICT = dict(Event.EVENT_CHOICES)


class WeeklySessionListView(LoginRequiredMixin, StaffUserMixin, ListView):

    model = WeeklySession
    template_name = 'studioadmin/timetable_sessions_list.html'
    context_object_name = 'sessions'

    def get_context_data(self):
        context = super(WeeklySessionListView, self).get_context_data()
        context['sessions_formset'] = TimetableWeeklySessionFormSet()
        context['sidenav_selection'] = 'timetable'
        return context

    def post(self, request, *args, **kwargs):
        session_forms = TimetableWeeklySessionFormSet(request.POST)

        if session_forms.has_changed():
            deleted_session_ids = []
            for form in session_forms:
                if form.has_changed() and 'DELETE' in form.changed_data:
                    session = WeeklySession.objects.get(id=form.instance.id)
                    deleted_session_ids.append(session.id)
                    # delete session
                    session.delete()

                msg = "Session{} {} {} been deleted".format(
                    's' if len(deleted_session_ids) > 1 else '',
                    ', '.join(["{}".format(id) for id in deleted_session_ids]),
                    'have' if len(deleted_session_ids) > 1 else 'has',
                )
            ActivityLog.objects.create(
                log="Session{plural} (id{plural} {ids}) {pluralhas} "
                    "been deleted by admin user {user}".format(
                        plural='s' if len(deleted_session_ids) > 1 else '',
                        pluralhas = 'have' if len(deleted_session_ids) > 1
                        else 'has',
                        ids=', '.join(
                            ["{}".format(id) for id in deleted_session_ids]
                        ),
                        user=request.user.username
                    )
            )
            messages.success(request, msg)
        else:
            messages.info(request, "No changes made")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:timetable_sessions_list')


class EventListView(LoginRequiredMixin, StaffUserMixin, ListView):

    model = Event
    template_name = 'studioadmin/timetable_events_list.html'
    context_object_name = 'events'
    event_type = None

    def get_queryset(self):
        return Event.objects.filter(event_type=self.event_type)

    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        context['events_formset'] = EventsFormSet(queryset=self.object_list)
        context['event_type'] = self.event_type
        context['event_type_title'] = EVENT_CHOICES_DICT[self.event_type]
        context['sidenav_selection'] = 'timetable'
        return context

    def post(self, request, *args, **kwargs):
        events_forms = EventsFormSet(request.POST)

        if events_forms.has_changed():
            deleted_event_ids = []
            updated_event_ids = []
            for form in events_forms:
                if form.has_changed():
                    if 'DELETE' in form.changed_data:
                        event = Event.objects.get(id=form.instance.id)
                        deleted_event_ids.append(event.id)
                        # delete event
                        event.delete()
                    else:
                        updated_event_ids.append(form.instance.id)
                        form.save()

            if deleted_event_ids:
                msg = "{}{} {} {} been deleted".format(
                    EVENT_CHOICES_DICT[self.event_type],
                    's' if len(deleted_event_ids) > 1 else '',
                    ', '.join(["{}".format(name) for name in deleted_event_ids]),
                    'have' if len(deleted_event_ids) > 1 else 'has',
                )
                ActivityLog.objects.create(
                    log="{event_type}{plural} (id{plural} {ids}) "
                        "{pluralhas} been deleted by admin user {user}".format(
                            event_type=EVENT_CHOICES_DICT[self.event_type],
                            plural='s' if len(deleted_event_ids) > 1 else '',
                            pluralhas = 'have' if len(deleted_event_ids) > 1
                            else 'has',
                            ids=', '.join(
                                ["{}".format(id) for id in deleted_event_ids]
                            ),
                            user=request.user.username
                        )
                )
            if updated_event_ids:
                msg = "{}{} {} {} been updated".format(
                    EVENT_CHOICES_DICT[self.event_type],
                    's' if len(updated_event_ids) > 1 else '',
                    ', '.join(["{}".format(id) for id in updated_event_ids]),
                    'have' if len(updated_event_ids) > 1 else 'has',
                )
                ActivityLog.objects.create(
                    log="{event_type}{plural} (id{plural} {ids}) "
                        "{pluralhas} been deleted by admin user {user}".format(
                            event_type=EVENT_CHOICES_DICT[self.event_type],
                            plural='s' if len(updated_event_ids) > 1 else '',
                            pluralhas = 'have' if len(updated_event_ids) > 1
                            else 'has',
                            ids=', '.join(
                                ["{}".format(id) for id in updated_event_ids]
                            ),
                            user=request.user.username
                        )
                )

            messages.success(request, msg)
        else:
            messages.info(request, "No changes made")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:timetable_{}s_list'.format(self.event_type))


class CreateWeeklySessionView(LoginRequiredMixin, StaffUserMixin, CreateView):
    model = WeeklySession
    form_class = EditSessionForm
    template_name = 'studioadmin/add_weekly_session.html'

    def get_success_url(self):
        return reverse('studioadmin:timetable_sessions_list')


class CreateEventView(LoginRequiredMixin, StaffUserMixin, CreateView):
    model = Event
    form_class = CreateEventForm
    template_name = 'studioadmin/add_event.html'

    def get_context_data(self, **kwargs):
        event_type = self.kwargs['event_type']
        context = super(CreateEventView, self).get_context_data(**kwargs)
        context['event_type'] = event_type
        context['event_type_title'] = EVENT_CHOICES_DICT[event_type]
        return context

    def get_form_kwargs(self):
        kwargs = super(CreateEventView, self).get_form_kwargs()
        kwargs['event_type'] = self.kwargs['event_type']
        return kwargs

    def form_valid(self, form):
        event = form.save(commit=False)
        event.event_type = self.kwargs['event_type']
        event.save()
        return super(CreateEventView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'studioadmin:timetable_{}s_list'.format(self.kwargs['event_type'])
        )


class WeeklySessionEditView(LoginRequiredMixin, StaffUserMixin, UpdateView):

    model = WeeklySession
    template_name = 'studioadmin/includes/weekly-session-modal.html'
    form_class = EditSessionForm

    def form_valid(self, form):
        form.save()
        if form.has_changed():
            messages.success(self.request, 'Saved!')
            form.save()
        else:
            messages.success(self.request, 'No changes made')
        return render_to_response(
                'studioadmin/includes/weekly-session-edit-success.html'
            )


class EventEditView(LoginRequiredMixin, StaffUserMixin, UpdateView):

    model = Event
    template_name = 'studioadmin/includes/event-modal.html'
    form_class = EditEventForm
    # event_type = None

    def get_context_data(self, **kwargs):
        context = super(EventEditView, self).get_context_data(**kwargs)
        event_type = self.get_object().event_type
        context['event_type'] = event_type
        context['event_type_title'] = EVENT_CHOICES_DICT[event_type]
        return context

    def form_valid(self, form):
        form.save()
        if form.has_changed():
            messages.success(self.request, 'Saved!')
            form.save()
        else:
            messages.success(self.request, 'No changes made')
        return render_to_response(
                'studioadmin/includes/event-edit-success.html'
            )
