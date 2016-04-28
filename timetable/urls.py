from django.conf.urls import url
from timetable.views import toggle_spaces, WeeklySessionListView


urlpatterns = [
    url(r'^$', WeeklySessionListView.as_view(), name='timetable'),
    url(
        r'^(?P<session_id>\d+)/spaces/$', toggle_spaces, name='spaces_text'
    ),

]
