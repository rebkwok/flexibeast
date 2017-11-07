from django.contrib.auth.decorators import login_required

from django.shortcuts import render_to_response
from django.views.generic import ListView

from timetable.models import Event, WeeklySession
from timetable.utils import staff_required


class WeeklySessionListView(ListView):

    model = WeeklySession
    template_name = 'timetable/timetable_grid.html'
    context_object_name = 'sessions'

    def get_context_data(self, **kwargs):
        context = super(WeeklySessionListView, self).get_context_data(**kwargs)
        sessions_by_weekday = []
        for day in WeeklySession.DAY_CHOICES:
            sessions = WeeklySession.objects.filter(day=day[0])
            if sessions:
                sessions_by_weekday.append(
                    {'weekday': day[1], 'sessions': sessions}
                )
        context['sessions_by_weekday'] = sessions_by_weekday

        spaces = WeeklySession.objects.filter(full=False).exists()
        context['classes_with_spaces'] = spaces
        context['nav_section'] = 'timetable'
        return context


class EventListView(ListView):

    model = Event
    template_name = 'timetable/timetable_events.html'
    context_object_name = 'events'
    event_type = None

    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        events = Event.objects.filter(
            show_on_site=True, event_type=self.event_type
        ).order_by('-date')
        context['events'] = events
        context['event_title'] = dict(Event.EVENT_CHOICES)[self.event_type]
        context['event_type'] = self.event_type
        context['nav_section'] = 'services'
        return context


@login_required
@staff_required
def toggle_spaces(request, session_id):
    session = WeeklySession.objects.get(id=session_id)
    session.full = not session.full
    session.save()
    return render_to_response(
        'timetable/includes/spaces.txt', {'session': session}
    )
