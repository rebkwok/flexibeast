from django import template

from timetable.models import WeeklySession

register = template.Library()


@register.filter
def format_session_day(value):
    return dict(WeeklySession.DAY_CHOICES)[value][0:3]
