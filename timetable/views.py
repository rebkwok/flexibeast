from django.contrib.auth.decorators import login_required

from django.shortcuts import render_to_response
from django.views.generic import ListView

from timetable.models import StretchClinic, WeeklySession
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


class StretchClinicListView(ListView):

    model = StretchClinic
    template_name = 'timetable/timetable_clinics.html'
    context_object_name = 'clinics'

    def get_context_data(self, **kwargs):
        context = super(StretchClinicListView, self).get_context_data(**kwargs)
        clinics = StretchClinic.objects.filter(
            show_on_site=True
        ).order_by('-date')
        context['clinics'] = clinics
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
