from django.conf.urls import patterns, url
from django.views.generic import RedirectView
from studioadmin.views.misc import ConfirmRefundView
from studioadmin.views.activitylog import ActivityLogListView
from studioadmin.views.events import EventAdminCreateView, EventAdminUpdateView
from studioadmin.views.blocks import BlockAdminCreateView, BlockAdminUpdateView
from studioadmin.views.timetable import (
                               TimetableSessionUpdateView,
                               TimetableSessionCreateView,
                               )
from studioadmin.views.users import UserListView
from studioadmin.views.website import PageListView, PageCreateView, PageUpdateView


urlpatterns = patterns('',
    url(r'^confirm-payment/(?P<pk>\d+)/$',
        'studioadmin.views.misc.confirm_user_booking_payment',
        name='confirm-payment'),
    url(r'^confirm-payment/user/(?P<user_id>\d+)/block/(?P<block_id>\d+)/$',
        'studioadmin.views.misc.confirm_user_block_payment',
        name='confirm-block-payment'),
    url(r'^confirm-refunded/(?P<pk>\d+)/$', ConfirmRefundView.as_view(),
        name='confirm-refund'),
    url(r'^events/(?P<slug>[\w-]+)/edit$', EventAdminUpdateView.as_view(),
        {'ev_type': 'event'}, name='edit_event'),
    url(r'^events/$', 'studioadmin.views.events.event_admin_list',
        {'ev_type': 'events'}, name='events'),
    url(r'^events/new/$', EventAdminCreateView.as_view(),
        {'ev_type': 'event'}, name='add_event'),
    url(r'^classes/(?P<slug>[\w-]+)/edit$', EventAdminUpdateView.as_view(),
        {'ev_type': 'lesson'}, name='edit_lesson'),
    url(r'^classes/$', 'studioadmin.views.events.event_admin_list',
        {'ev_type': 'lessons'}, name='lessons'),
    url(r'^classes/new/$', EventAdminCreateView.as_view(),
        {'ev_type': 'lesson'}, name='add_lesson'),
    url(r'^registers/by-date/$', 'studioadmin.views.events.registers_by_date',
        name='registers_by_date'),
    url(r'^blocks/$', 'studioadmin.views.blocks.admin_block_list',
        name='blocks'),
    url(r'^blocks/(?P<pk>\d+)/edit$', BlockAdminUpdateView.as_view(),
        name='edit_block'),
    url(r'^blocks/new/$', BlockAdminCreateView.as_view(),
        name='add_block'),
    url(
        r'^timetable/$', 'studioadmin.views.timetable.timetable_admin_list',
        name='timetable'
    ),
    url(
        r'^timetable/session/(?P<pk>\d+)/edit$',
        TimetableSessionUpdateView.as_view(), name='edit_session'
    ),
    url(
        r'^timetable/session/new$',
        TimetableSessionCreateView.as_view(), name='add_session'
    ),
    url(r'^timetable/upload/$', 'studioadmin.views.timetable.upload_timetable_view',
        name='upload_timetable'),
    url(r'^users/$', UserListView.as_view(), name="users"),
    # url(r'^users/email/$', 'studioadmin.views.choose_users_to_email',
    #     name="choose_email_users"),
    # url(r'^users/email/emailform/$', 'studioadmin.views.email_users_view',
    #     name="email_users_view"),
    url(
        r'^users/(?P<user_id>\d+)/bookings/(?P<booking_status>[\w-]+)$',
        'studioadmin.views.users.user_bookings_view', name='user_bookings_list'
    ),
    url(
        r'^users/blocks/$',
        'studioadmin.views.users.block_bookings_view', name='block_bookings'
    ),
    url(
        r'activitylog/$', ActivityLogListView.as_view(), name='activitylog'
    ),
    url(
        r'^bookings-waitinglists/(?P<event_id>\d+)$',
        'studioadmin.views.waitinglist.event_waiting_list_view', name='event_waiting_list'
    ),
    url(
        r'^blocks/(?P<block_id>\d+)/bookings/$',
        'studioadmin.views.blocks.single_block_bookings_view',
        name='single_block_bookings'
    ),
    url(
        r'^website-pages/$',
        PageListView.as_view(), name='website_pages_list'
    ),
    url(
        r'^website-pages/(?P<name>[\w-]+)$',
        PageUpdateView.as_view(), name='edit_page'
    ),
   url(
        r'^website-pages/new/$', PageCreateView.as_view(), name='add_page'
    ),
    url(r'^$', RedirectView.as_view(url='/studioadmin/classes/', permanent=True)),
    )
