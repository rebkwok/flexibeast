import json
from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone
from django.utils.safestring import mark_safe
from django import forms
from suit.widgets import EnclosedInput
from ckeditor.widgets import CKEditorWidget

from flex_bookings.models import Event, Booking, Block, \
    EventType, WaitingListUser
from flex_bookings.widgets import DurationSelectorWidget


class BookingDateListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'date'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'event__date'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('past', ('past events only')),
            ('upcoming', ('upcoming events only')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value
        # to decide how to filter the queryset.
        if self.value() == 'past':
            return queryset.filter(event__date__lte=timezone.now())
        if self.value() == 'upcoming':
            return queryset.filter(event__date__gte=timezone.now())


class EventDateListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'date'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('past', 'past events only'),
            ('upcoming', 'upcoming events only'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value
        # to decide how to filter the queryset.
        if self.value() == 'past':
            return queryset.filter(date__lte=timezone.now())
        if self.value() == 'upcoming':
            return queryset.filter(date__gte=timezone.now())


class EventTypeListFilter(admin.SimpleListFilter):
    """
    Filter by class or event
    """
    title = 'Type'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('class', 'Classes'),
            ('event', 'Workshops'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value
        # to decide how to filter the queryset.
        if self.value() == 'class':
            return queryset.filter(event_type__event_type='CL')
        if self.value() == 'event':
            return queryset.filter(event_type__event_type='EV')


class EventForm(forms.ModelForm):

    description = forms.CharField(
        widget=CKEditorWidget(attrs={'class':'container-fluid'}),
        required=False
    )

    class Meta:
        widgets = {
            # You can also use prepended and appended together
            'cost': EnclosedInput(prepend=u'\u00A3'),
            'cancellation_period': DurationSelectorWidget(),
            }


# TODO validation on event fields - e.g. payment due date can't be after event
# TODO date, event date can't be in past, cost must be >= 0
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location', 'get_spaces_left', 'booking_open')
    list_filter = (EventDateListFilter, 'name', EventTypeListFilter)
    actions_on_top = True
    form = EventForm

    CANCELLATION_TEXT = ' '.join(['<p>Enter cancellation period in',
                                  'weeks, days and/or hours.</br>',
                                  'Note that 1 day will be displayed to users ',
                                  'as "24 hours" for clarity.</p>',
                                  ])

    fieldsets = [
        ('Event details', {
            'fields': (
                'name', 'date', 'location', 'event_type', 'max_participants',
                'description')
        }),
        ('Contacts', {
            'fields': ('contact_person', 'contact_email', 'email_studio_when_booked')
        }),
        ('Payment Information', {
            'fields': ('cost', 'advance_payment_required', 'booking_open',
            'payment_info',  'payment_due_date')
        }),
        ('Cancellation Period', {
            'fields': ('cancellation_period',),
            'description': '<div class="help">%s</div>' % CANCELLATION_TEXT,
        }),
    ]

    def get_spaces_left(self, obj):
        return obj.spaces_left()
    get_spaces_left.short_description = '# Spaces left'


class BookingAdmin(admin.ModelAdmin):

    list_display = ('event_name', 'get_date', 'user', 'get_user_first_name',
                    'get_user_last_name', 'cost', 'paid',
                    'space_confirmed', 'status')

    list_filter = (BookingDateListFilter, 'user', 'event')

    readonly_fields = ('date_payment_confirmed',)

    actions_on_top = True
    actions_on_bottom = False

    def get_date(self, obj):
        return obj.event.date
    get_date.short_description = 'Date'

    def event_name(self, obj):
        return obj.event.name
    event_name.short_description = 'Event or Workshop'
    event_name.admin_order_field = 'event'

    def get_user_first_name(self, obj):
        return obj.user.first_name
    get_user_first_name.short_description = 'First name'

    def get_user_last_name(self, obj):
        return obj.user.last_name
    get_user_last_name.short_description = 'Last name'


class WaitingListUserAdmin(admin.ModelAdmin):
    fields = ('user', 'event')
    list_display = ('user', 'event')




admin.site.register(Event, EventAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(EventType)
admin.site.register(WaitingListUser, WaitingListUserAdmin)
admin.site.register(Block)
