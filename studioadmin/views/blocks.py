import logging

from datetime import datetime, time

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template.loader import get_template
from django.template import Context
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponseRedirect, HttpResponse, redirect, \
    render, get_object_or_404
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import send_mail

from flex_bookings.models import Block

# from flex_bookings import utils
from flex_bookings.email_helpers import send_support_email, send_waiting_list_email

# from timetable.models import Session
from studioadmin.forms import BlockAdminForm, BlockFormSet
from studioadmin.views.utils import StaffUserMixin, staff_required
from activitylog.models import ActivityLog


@login_required
@staff_required
def admin_block_list(request):

    block_list = [bl.id for bl in Block.objects.all() if not bl.is_past]
    queryset = Block.objects.filter(id__in=block_list)
    blocks = True if len(queryset) > 0 else False
    show_past = False

    if request.method == 'POST':
        if "past" in request.POST:
            queryset = [
                block for block in Block.objects.all() if block.is_past
                ]
            blocks = True if len(queryset) > 0 else False
            show_past = True
            blockformset = BlockFormSet(queryset=queryset)
        elif "upcoming" in request.POST:
            queryset = queryset
            show_past = False
            blockformset = BlockFormSet(queryset=queryset)
        else:
            blockformset = BlockFormSet(request.POST)

            if blockformset.is_valid():
                if not blockformset.has_changed():
                    messages.info(request, "No changes were made")
                else:
                    for form in blockformset:
                        if form.has_changed():
                            block = form.save(commit=False)
                            if 'DELETE' in form.changed_data:
                                messages.success(
                                    request, mark_safe(
                                        'Block {} <strong>{}</strong> has been deleted!'.format(
                                            block.name,
                                        )
                                    )
                                )
                                ActivityLog.objects.create(
                                    log='Block {} (id {}) deleted by admin user {}'.format(
                                        block.name,
                                        block.id, request.user.username
                                    )
                                )
                            else:
                                for field in form.changed_data:
                                    messages.success(
                                        request, mark_safe(
                                            "<strong>{}</strong> updated for "
                                            "<strong>{}</strong>".format(
                                                field.title().replace("_", " "),
                                                block.name))
                                    )

                                    ActivityLog.objects.create(
                                        log='Block {} (id {}) updated by admin user {}: {} changed from {} to {}'.format(
                                            block.name, block.id,
                                            request.user.username,
                                            field.title().replace("_", " "),
                                            form.initial[field],
                                            form.cleaned_data[field]
                                        )
                                    )
                            form.save()

                        for error in form.errors:
                            messages.error(request, mark_safe("{}".format(error)))
                    blockformset.save()
                return HttpResponseRedirect(
                    reverse('studioadmin:blocks')
                )
            else:
                messages.error(
                    request,
                    mark_safe(
                        "There were errors in the following fields:\n{}".format(
                            '\n'.join(
                                ["{}".format(error) for error in blockformset.errors]
                            )
                        )
                    )
                )

    else:
        blockformset = BlockFormSet(queryset=queryset)

    return render(
        request, 'studioadmin/admin_blocks.html', {
            'blockformset': blockformset,
            'blocks': blocks,
            'sidenav_selection': 'blocks',
            'show_past': show_past,
            }
    )