from django.conf.urls import url
from timetable.views import toggle_spaces, StretchClinicListView, \
    WeeklySessionListView


urlpatterns = [
    url(r'^regular-classes/$', WeeklySessionListView.as_view(), name='timetable'),
    url(r'^stretch-clinics/$', StretchClinicListView.as_view(), name='timetable_clinics'),
    url(
        r'^(?P<session_id>\d+)/spaces/$', toggle_spaces, name='toggle_spaces'
    ),

]
