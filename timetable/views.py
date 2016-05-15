from django.contrib.auth.decorators import login_required

from django.shortcuts import render_to_response
from django.views.generic import ListView

from timetable.models import WeeklySession
from timetable.utils import staff_required


class WeeklySessionListView(ListView):

    model = WeeklySession
    template_name = 'timetable/timetable.html'
    context_object_name = 'sessions'

    def get_context_data(self, **kwargs):
        context = super(WeeklySessionListView, self).get_context_data(**kwargs)
        spaces = WeeklySession.objects.filter(full=False).exists()
        context['classes_with_spaces'] = spaces
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
