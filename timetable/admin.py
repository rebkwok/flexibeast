from django.contrib import admin
from timetable.models import Location, WeeklySession, Event


class WeeklySessionAdmin(admin.ModelAdmin):
    list_display = ('day', 'time', 'name', 'location', 'full')
    ordering = ('day', 'time')
    fields = ('name', 'day', 'time', 'description', 'location',
              'max_participants', 'contact_person', 'contact_email',
              'cost', 'block_info', 'full')
    model = WeeklySession


class EventAdmin(admin.ModelAdmin):
    list_display = (
        'event_type', 'date', 'location', 'max_spaces', 'spaces', 'show_on_site'
    )
    ordering = ('date',)
    fields = ('event_type', 'date', 'description', 'location',
              'max_spaces', 'contact_person', 'contact_email',
              'cost', 'spaces', 'show_on_site')
    model = Event


admin.site.register(WeeklySession, WeeklySessionAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Location)
