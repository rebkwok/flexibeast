from django.urls import include, path
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


app_name = 'studioadmin'


urlpatterns = [
    path('users/', UserListView.as_view(), name="users"),
    path('users/email/', choose_users_to_email, name="choose_email_users"),
    path('users/email/emailform/', email_users_view,
        name="email_users_view"),
    path(
        'activitylog/', ActivityLogListView.as_view(), name='activitylog'
    ),
    #### GALLERY #####
    path(
        'gallery/albums/', CategoryListView.as_view(),
        name='gallery_categories'
    ),
    # Category detail view, show all images for edit/delete/add
    path(
        'gallery/albums/<int:pk>', CategoryUpdateView.as_view(),
        name='gallery_category_edit'
    ),
    #### WEBSITE PAGES #####
    path(
        'website-pages/',
        PageListView.as_view(), name='website_pages_list'
    ),
    path(
        'website-pages/new/', PageCreateView.as_view(), name='add_page'
    ),
    path(
        'website-pages/(<str:name>/',
        PageUpdateView.as_view(), name='edit_page'
    ),
    path(
        '',
        RedirectView.as_view(url='/studioadmin/classes/', permanent=True)
    ),
    #### TIMETABLE #####
    path(
        'timetable/regular-classes/',
        WeeklySessionListView.as_view(), name='timetable_sessions_list'
    ),
    path(
        'timetable/regular-classes/new',
        CreateWeeklySessionView.as_view(), name='timetable_session_add'
    ),
    path(
        'timetable/stretch-clinics/',
        EventListView.as_view(event_type='clinic'),
        name='timetable_clinics_list'
    ),
    path(
        'timetable/workshops/', EventListView.as_view(event_type='workshop'),
        name='timetable_workshops_list'
    ),
    path(
        'timetable/(<str:event_type>/new',
        CreateEventView.as_view(), name='timetable_event_add'
    ),
    path(
        'timetable/sessionedit/<int:pk>/',
        WeeklySessionEditView.as_view(), name='sessionedit'
    ),
    path(
        'timetable/edit/<int:pk>/',
        EventEditView.as_view(), name='eventedit'
    ),
]
