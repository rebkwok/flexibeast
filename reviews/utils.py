from functools import wraps

from django.conf import settings
from django.urls import reverse
from django.shortcuts import HttpResponseRedirect


class StaffUserMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return HttpResponseRedirect(
                reverse(settings.PERMISSION_DENIED_URL)
            )
        return super(StaffUserMixin, self).dispatch(request, *args, **kwargs)
