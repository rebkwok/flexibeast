import pytz

from django import template
from django.conf import settings
from django.utils import timezone

from website.models import RestrictedAccessTracker

register = template.Library()


@register.filter
def format_field_name(field):
    return field.replace('_', ' ').title()


@register.filter
def formatted_uk_date(date):
    """
    return UTC date in uk time
    """
    uk=pytz.timezone('Europe/London')
    return date.astimezone(uk).strftime("%d %b %Y %H:%M")


@register.assignment_tag
def check_debug():
    return settings.DEBUG


@register.filter
def viewable(page, user):
    return not page.restricted or user.has_perm('website.can_view_restricted')


@register.filter
def can_view_restricted(user):
    return user.has_perm('website.can_view_restricted')


@register.filter
def time_since_access(user):
    try:
        tracker = RestrictedAccessTracker.objects.get(user=user)
        time_since = timezone.now() - tracker.start_date
        return '{} days, {}h:{}m:{}s'.format(
            time_since.days, time_since.seconds//3600,
            (time_since.seconds//60) % 60, time_since.seconds % 60
        )
    except RestrictedAccessTracker.DoesNotExist:
        return ''
