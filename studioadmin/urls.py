from django.conf.urls import include, url
from django.views.generic import RedirectView

from gallery.views import CategoryListView, CategoryUpdateView
from studioadmin.views.activitylog import ActivityLogListView
from studioadmin.views.email_users import choose_users_to_email, \
    email_users_view
from studioadmin.views.timetable import WeeklySessionListView, \
    EventListView, WeeklySessionEditView, EventEditView, \
    CreateWeeklySessionView, CreateEventView
from studioadmin.views.users import UserListView
from studioadmin.views.website import PageListView, PageCreateView, \
    PageUpdateView


urlpatterns = [
    url(r'^users/$', UserListView.as_view(), name="users"),
    url(r'^users/email/$', choose_users_to_email, name="choose_email_users"),
    url(r'^users/email/emailform/$', email_users_view,
        name="email_users_view"),
    url(
        r'activitylog/$', ActivityLogListView.as_view(), name='activitylog'
    ),
    #### GALLERY #####
    url(
        r'^gallery/albums/$', CategoryListView.as_view(),
        name='gallery_categories'
    ),
    # Category detail view, show all images for edit/delete/add
    url(
        r'^gallery/albums/(?P<pk>\d+)$', CategoryUpdateView.as_view(),
        name='gallery_category_edit'
    ),
    #### WEBSITE PAGES #####
    url(
        r'^website-pages/$',
        PageListView.as_view(), name='website_pages_list'
    ),
    url(
        r'^website-pages/new/$', PageCreateView.as_view(), name='add_page'
    ),
    url(
        r'^website-pages/(?P<name>[\w\d//-]+)$',
        PageUpdateView.as_view(), name='edit_page'
    ),
    url(
        r'^$',
        RedirectView.as_view(url='/studioadmin/classes/', permanent=True)
    ),
    #### TIMETABLE #####
    url(
        r'^timetable/regular-classes/$',
        WeeklySessionListView.as_view(), name='timetable_sessions_list'
    ),
    url(
        r'^timetable/regular-classes/new$',
        CreateWeeklySessionView.as_view(), name='timetable_session_add'
    ),
    url(
        r'^timetable/stretch-clinics/$',
        EventListView.as_view(event_type='clinic'),
        name='timetable_clinics_list'
    ),
    url(
        r'^timetable/workshops/$', EventListView.as_view(event_type='workshop'),
        name='timetable_workshops_list'
    ),
    url(
        r'^timetable/(?P<event_type>\w+)/new$',
        CreateEventView.as_view(), name='timetable_event_add'
    ),
    url(
        r'^timetable/sessionedit/(?P<pk>\d+)/$',
        WeeklySessionEditView.as_view(), name='sessionedit'
    ),
    url(
        r'^timetable/edit/(?P<pk>\d+)/$',
        EventEditView.as_view(), name='eventedit'
    ),
]
