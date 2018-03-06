from functools import wraps

from django.urls import reverse
from django.shortcuts import HttpResponseRedirect


def staff_required(func):
    def decorator(request, *args, **kwargs):
        if request.user.is_staff:
            return func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('permission_denied'))
    return wraps(func)(decorator)


class StaffUserMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponseRedirect(reverse('permission_denied'))
        return super(StaffUserMixin, self).dispatch(request, *args, **kwargs)
