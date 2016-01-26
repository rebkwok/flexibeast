from django.conf.urls import patterns, url
from django.views.generic import RedirectView
from studioadmin.views.misc import ConfirmRefundView
from studioadmin.views.activitylog import ActivityLogListView
from studioadmin.views.events import EventAdminCreateView, \
    EventAdminUpdateView, event_admin_list, registers_by_date
from studioadmin.views.blocks import BlockAdminCreateView, \
    BlockAdminUpdateView, admin_block_list, single_block_bookings_view
from studioadmin.views.email_users import choose_users_to_email, \
    email_users_view
from studioadmin.views.misc import confirm_user_booking_payment, \
    confirm_user_block_payment
from studioadmin.views.timetable import TimetableSessionUpdateView, \
    TimetableSessionCreateView, timetable_admin_list, upload_timetable_view
from studioadmin.views.users import UserListView, user_bookings_view, \
    block_bookings_view
from studioadmin.views.waitinglist import event_waiting_list_view
from studioadmin.views.website import PageListView, PageCreateView, \
    PageUpdateView


urlpatterns = [
    url(r'^confirm-payment/(?P<pk>\d+)/$', confirm_user_booking_payment,
        name='confirm-payment'),
    url(r'^confirm-payment/user/(?P<user_id>\d+)/block/(?P<block_id>\d+)/$',
        confirm_user_block_payment, name='confirm-block-payment'),
    url(r'^confirm-refunded/(?P<pk>\d+)/$', ConfirmRefundView.as_view(),
        name='confirm-refund'),
    url(r'^events/(?P<slug>[\w-]+)/edit$', EventAdminUpdateView.as_view(),
        {'ev_type': 'event'}, name='edit_event'),
    url(r'^events/$', event_admin_list, {'ev_type': 'events'}, name='events'),
    url(r'^events/new/$', EventAdminCreateView.as_view(),
        {'ev_type': 'event'}, name='add_event'),
    url(r'^classes/(?P<slug>[\w-]+)/edit$', EventAdminUpdateView.as_view(),
        {'ev_type': 'lesson'}, name='edit_lesson'),
    url(
        r'^classes/$', event_admin_list, {'ev_type': 'lessons'}, name='lessons'
    ),
    url(r'^classes/new/$', EventAdminCreateView.as_view(),
        {'ev_type': 'lesson'}, name='add_lesson'),
    url(r'^registers/by-date/$', registers_by_date, name='registers_by_date'),
    url(r'^blocks/$', admin_block_list, name='blocks'),
    url(r'^blocks/(?P<pk>\d+)/edit$', BlockAdminUpdateView.as_view(),
        name='edit_block'),
    url(r'^blocks/new/$', BlockAdminCreateView.as_view(),
        name='add_block'),
    url(r'^timetable/$', timetable_admin_list, name='timetable'),
    url(
        r'^timetable/session/(?P<pk>\d+)/edit$',
        TimetableSessionUpdateView.as_view(), name='edit_session'
    ),
    url(
        r'^timetable/session/new$',
        TimetableSessionCreateView.as_view(), name='add_session'
    ),
    url(r'^timetable/upload/$', upload_timetable_view, name='upload_timetable'),
    url(r'^users/$', UserListView.as_view(), name="users"),
    url(r'^users/email/$', choose_users_to_email, name="choose_email_users"),
    url(r'^users/email/emailform/$', email_users_view,
        name="email_users_view"),
    url(
        r'^users/(?P<user_id>\d+)/bookings/(?P<booking_status>[\w-]+)$',
        user_bookings_view, name='user_bookings_list'
    ),
    url(
        r'^users/blocks/$',
        block_bookings_view, name='block_bookings'
    ),
    url(
        r'activitylog/$', ActivityLogListView.as_view(), name='activitylog'
    ),
    url(
        r'^bookings-waitinglists/(?P<event_id>\d+)$', event_waiting_list_view,
        name='event_waiting_list'
    ),
    url(
        r'^blocks/(?P<block_id>\d+)/bookings/$', single_block_bookings_view,
        name='single_block_bookings'
    ),
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
]
