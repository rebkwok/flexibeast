from django.conf.urls import url
from timetable.views import toggle_spaces, EventListView, \
    WeeklySessionListView


urlpatterns = [
    url(r'^regular-classes/$', WeeklySessionListView.as_view(), name='timetable'),
    url(
        r'^stretch-clinics/$', EventListView.as_view(event_type='clinic'),
        name='timetable_clinics'),
    url(
        r'^workshops/$', EventListView.as_view(event_type='workshop'),
        name='timetable_workshops'),
    url(
        r'^(?P<session_id>\d+)/spaces/$', toggle_spaces, name='toggle_spaces'
    ),

]
