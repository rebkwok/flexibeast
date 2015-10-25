from functools import wraps

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponseRedirect


def staff_required(func):
    def decorator(request, *args, **kwargs):
        if request.user.is_staff:
            return func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(
                reverse(settings.PERMISSION_DENIED_URL)
            )
    return wraps(func)(decorator)


class StaffUserMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponseRedirect(
                reverse(settings.PERMISSION_DENIED_URL)
            )
        return super(StaffUserMixin, self).dispatch(request, *args, **kwargs)
