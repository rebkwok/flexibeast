from django.conf.urls import include, patterns, url
from flex_bookings.views import EventListView, EventDetailView, \
    BookingListView, BookingHistoryListView, BookingCreateView, \
    BookingDeleteView


urlpatterns = patterns('',
    url(r'^bookings/$', BookingListView.as_view(), name='bookings'),
    url(
        r'^bookings/payments-pending/$',
        'flex_bookings.views.payments_pending', name='payments_pending'
    ),
    url(r'^booking-history/$', BookingHistoryListView.as_view(),
        name='booking_history'),
    url(r'^block/(?P<pk>\d+)/update/$', 'flex_bookings.views.update_block',
        name='update_block'),
   url(r'^booking/(?P<pk>\d+)/update/$', 'flex_bookings.views.update_booking',
        name='update_booking'),
    # url(r'^booking/update/(?P<pk>\d+)/cancelled/$',
    #     'flex_bookings.views.update_booking_cancelled',
    #     name='update_booking_cancelled'),
    url(r'^booking/cancel/(?P<pk>\d+)/$', BookingDeleteView.as_view(),
        name='delete_booking'),
    url(r'^events/(?P<event_slug>[\w-]+)/cancellation-period-past/$',
        'flex_bookings.views.cancellation_period_past', name='cancellation_period_past'),
    url(r'^booking/(?P<event_slug>[\w-]+)/duplicate/$',
        'flex_bookings.views.duplicate_booking', name='duplicate_booking'),
    url(r'^booking/(?P<event_slug>[\w-]+)/full/$', 'flex_bookings.views.fully_booked',
        name='fully_booked'),
    url(r'^booking/(?P<event_slug>[\w-]+)/new/$', BookingCreateView.as_view(),
        name='book_event'),
    url(
        r'^workshops/(?P<slug>[\w-]+)/$', EventDetailView.as_view(),
        {'ev_type': 'event'}, name='event_detail'
    ),
    url(
        r'^workshops/$', EventListView.as_view(), {'ev_type': 'events'},
        name='events'
    ),
    url(
        r'^classes/(?P<slug>[\w-]+)/$',  EventDetailView.as_view(),
        {'ev_type': 'lesson'}, name='lesson_detail'),
    url(
        r'^classes/$', EventListView.as_view(), {'ev_type': 'lessons'},
        name='lessons'
    ),
    url(r'^booking/(?P<event_slug>[\w-]+)/not-open/$',
        'flex_bookings.views.booking_not_open', name='not_open'),
    )
