from django.contrib.auth.decorators import login_required

from django.shortcuts import render_to_response
from django.views.generic import ListView

from timetable.models import WeeklySession
from timetable.utils import staff_required


class WeeklySessionListView(ListView):

    model = WeeklySession
    template_name = 'timetable/timetable.html'
    context_object_name = 'sessions'


@login_required
@staff_required
def toggle_spaces(request, session_id):
    session = WeeklySession.objects.get(id=session_id)
    session.full = not session.full
    session.save()
    return render_to_response(
        'timetable/includes/spaces.txt', {'session': session}
    )
