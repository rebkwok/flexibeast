from django.contrib import admin
from timetable.models import Location, WeeklySession, StretchClinic


class WeeklySessionAdmin(admin.ModelAdmin):
    list_display = ('day', 'time', 'name', 'location', 'full')
    ordering = ('day', 'time')
    fields = ('name', 'day', 'time', 'description', 'location',
              'max_participants', 'contact_person', 'contact_email',
              'cost', 'block_info', 'full')
    model = WeeklySession


class StretchClinicAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'location', 'max_spaces', 'spaces', 'show_on_site'
    )
    ordering = ('date',)
    fields = ('date', 'description', 'location',
              'max_spaces', 'contact_person', 'contact_email',
              'cost', 'spaces', 'show_on_site')
    model = StretchClinic


admin.site.register(WeeklySession, WeeklySessionAdmin)
admin.site.register(StretchClinic, StretchClinicAdmin)
admin.site.register(Location)
