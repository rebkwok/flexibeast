import urllib.parse
import ast
import logging

from datetime import datetime
from functools import wraps


from django.db.utils import IntegrityError
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

from braces.views import LoginRequiredMixin

from studioadmin.forms import PageForm, SubsectionFormset, PictureFormset
from studioadmin.views.utils import StaffUserMixin

from website.models import Page


logger = logging.getLogger(__name__)


class PageListView(LoginRequiredMixin, StaffUserMixin, ListView):

    model = Page
    template_name = 'studioadmin/website_page_list.html'
    context_object_name = 'pages'

    def get_context_data(self):
        context = super(PageListView, self).get_context_data()
        context['sidenav_selection'] = 'page_list'
        return context


class PageUpdateView(LoginRequiredMixin, StaffUserMixin, UpdateView):

    model = Page
    template_name = 'studioadmin/page_create_update.html'
    context_object_name = 'page'
    form_class = PageForm

    def get_object(self):
        queryset = Page.objects.all()
        return get_object_or_404(queryset, name=self.kwargs['name'])

    def get_context_data(self, **kwargs):
        context = super(PageUpdateView, self).get_context_data(**kwargs)
        context['sidenav_selection'] = 'page_list'

        subsection_formset = SubsectionFormset(instance=self.object)
        context['subsection_formset'] = subsection_formset

        picture_formset = PictureFormset(instance=self.object)
        context['picture_formset'] = picture_formset
        return context

    def post(self,request, *args, **kwargs):
        name = self.kwargs['name']
        page = Page.objects.get(name=name)
        form = PageForm(request.POST, instance=page)
        subsection_formset = SubsectionFormset(request.POST, instance=page)
        picture_formset = PictureFormset(request.POST, request.FILES, instance=page)

        if form.is_valid() and subsection_formset.is_valid() and \
                picture_formset.is_valid():

            if (form.has_changed() or subsection_formset.has_changed() or
                    picture_formset.has_changed()):

                if form.has_changed():
                    messages.success(
                        request,
                        "{} has been updated".format(
                            ', '.join(form.changed_data)
                        )
                    )
                page = form.save()

                for form in subsection_formset.forms:
                    if form.is_valid():
                        subsection = form.save(commit=False)
                        if 'DELETE' in form.changed_data:
                            subsection.delete()
                            messages.success(
                                request,
                                'Subsection deleted from "{}" page'.format(
                                    page.name.title()
                                )
                            )
                        elif form.has_changed():
                            subsection.save()
                            messages.success(
                                request,
                                'Subsection successfully edited for "{}" '
                                'page'.format(
                                    page.name.title()
                                )
                            )
                    else:
                        for error in form.errors:
                            messages.error(request, mark_safe(error))

                for form in picture_formset.forms:
                    if form.is_valid():
                        picture = form.save(commit=False)
                        if 'DELETE' in form.changed_data:
                            name = picture.image.name
                            picture.delete()
                            messages.success(
                                request,
                                'Picture {} deleted from "{}" page'.format(
                                    name.split('/')[-1],
                                    page.name.title()
                                )
                            )
                        elif form.has_changed():
                            action = 'edited' if picture.id else 'added'
                            picture.save()
                            messages.success(
                                request,
                                'Picture {} has been {}'.format(
                                    picture.image.name.split('/')[-1],
                                    action
                                )
                            )
                    else:
                        for error in form.errors:
                            messages.error(request, mark_safe(error))
            else:
                messages.info(request, "No changes made")

        if not form.is_valid():
            for error in form.errors:
                messages.error(request, mark_safe(error))

        if not subsection_formset.is_valid():
            for error in picture_formset.errors:
                for k, v in error.items():
                    messages.error(
                        request, mark_safe("{}: {}".format(k.title(), v))
                    )

        if not picture_formset.is_valid():
            for error in picture_formset.errors:
                for k, v in error.items():
                    messages.error(
                        request, mark_safe("{}: {}".format(k.title(), v))
                    )

        return HttpResponseRedirect(self.get_success_url(name=page.name))

    def get_success_url(self, name):
        return reverse(
            'studioadmin:edit_page', kwargs={'name': name}
        )