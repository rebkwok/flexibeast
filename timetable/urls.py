from django.urls import path
from timetable.views import toggle_spaces, EventListView, \
    WeeklySessionListView


app_name = 'timetable'


urlpatterns = [
    path('regular-classes/', WeeklySessionListView.as_view(), name='timetable'),
    path(
        'stretch-clinics/', EventListView.as_view(event_type='clinic'),
        name='timetable_clinics'),
    path(
        'workshops/', EventListView.as_view(event_type='workshop'),
        name='timetable_workshops'),
    path(
        '<int:session_id>/spaces/', toggle_spaces, name='toggle_spaces'
    ),

]
