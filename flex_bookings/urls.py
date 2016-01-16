from django.conf.urls import url
from flex_bookings.views import EventListView, EventDetailView, \
    BookingListView, BookingHistoryListView, BookingCreateView, \
    BookingDeleteView, payments_pending, update_block, update_booking, \
    cancellation_period_past, duplicate_booking, fully_booked, booking_not_open


urlpatterns = [
    url(r'^bookings/$', BookingListView.as_view(), name='bookings'),
    url(
        r'^bookings/payments-pending/$', payments_pending,
        name='payments_pending'
    ),
    url(r'^booking-history/$', BookingHistoryListView.as_view(),
        name='booking_history'),
    url(r'^block/(?P<pk>\d+)/update/$', update_block, name='update_block'),
    url(
       r'^booking/(?P<pk>\d+)/update/$', update_booking, name='update_booking'
    ),
    # url(r'^booking/update/(?P<pk>\d+)/cancelled/$',
    #     'flex_bookings.views.update_booking_cancelled',
    #     name='update_booking_cancelled'),
    url(r'^booking/cancel/(?P<pk>\d+)/$', BookingDeleteView.as_view(),
        name='delete_booking'),
    url(r'^events/(?P<event_slug>[\w-]+)/cancellation-period-past/$',
        cancellation_period_past, name='cancellation_period_past'),
    url(r'^booking/(?P<event_slug>[\w-]+)/duplicate/$',
        duplicate_booking, name='duplicate_booking'),
    url(r'^booking/(?P<event_slug>[\w-]+)/full/$', fully_booked,
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
    url(r'^booking/(?P<event_slug>[\w-]+)/not-open/$', booking_not_open,
        name='not_open'),
    ]
