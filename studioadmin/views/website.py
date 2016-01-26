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

from studioadmin.forms import PageForm, PagesFormset, PictureFormset
from studioadmin.views.utils import StaffUserMixin

from website.models import Page, Picture


logger = logging.getLogger(__name__)


class PageListView(LoginRequiredMixin, StaffUserMixin, ListView):

    model = Page
    template_name = 'studioadmin/website_page_list.html'
    context_object_name = 'pages'

    def get_context_data(self):
        context = super(PageListView, self).get_context_data()
        context['pages_formset'] = PagesFormset()
        context['sidenav_selection'] = 'page_list'
        return context

    def post(self, request, *args, **kwargs):
        pages_forms = PagesFormset(request.POST)

        if pages_forms.has_changed():
            deleted_page_names = []
            for form in pages_forms:
                if form.has_changed() and 'DELETE' in form.changed_data:
                    page = Page.objects.get(id=form.instance.id)

                    # delete associated pictures
                    # loop to delete pics so we call delete() on each instance
                    [pic.delete() for pic in Picture.objects.filter(page=page)]

                    deleted_page_names.append(page.name)
                    # delete page
                    page.delete()

            if len(deleted_page_names) == 1:
                msg = "Page '{}' has been deleted".format(deleted_page_names[0])
            elif len(deleted_page_names) > 1:
                msg = "Pages {} have been deleted".format(
                    ', '.join(["'{}'".format(name) for name in deleted_page_names])
                )
            else:
                msg = "No changes made"
            messages.success(request, msg)
        else:
            messages.info(request, "No changes made")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:website_pages_list')


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

        picture_formset = PictureFormset(instance=self.get_object())
        context['picture_formset'] = picture_formset
        return context

    def post(self, request, *args, **kwargs):
        name = self.kwargs['name']
        page = Page.objects.get(name=name)
        form = PageForm(request.POST, instance=page)
        picture_formset = PictureFormset(request.POST, request.FILES, instance=page)

        if form.is_valid() and picture_formset.is_valid():

            if (form.has_changed() or picture_formset.has_changed()):

                change_messages = []

                if form.has_changed():
                    change_messages.append("{} has been updated".format(
                        ', '.join(form.changed_data)
                        )
                    )

                page = form.save()

                for form in picture_formset.forms:
                    if form.is_valid():
                        picture = form.save(commit=False)
                        if 'DELETE' in form.changed_data:
                            name = picture.image.name
                            picture.delete()
                            change_messages.append(
                                'Picture {} deleted from "{}" page'.format(
                                    name.split('/')[-1],
                                    page.name.title()
                                )
                            )
                        elif form.has_changed():
                            action = 'edited' if picture.id else 'added'
                            picture.save()
                            change_messages.append(
                                'Picture {} has been {}'.format(
                                    picture.image.name.split('/')[-1],
                                    action
                                )
                            )
                    else:
                        for error in form.errors:
                            messages.error(request, mark_safe(error))

                messages.success(
                    request,
                    mark_safe(
                         "<ul>{}</ul>".format(
                             ''.join(['<li>{}</li>'.format(msg)
                              for msg in change_messages])
                         )
                    )
                )

            else:
                messages.info(request, "No changes made")
        else:
            if not picture_formset.is_valid():
                for error in picture_formset.errors:
                    for k, v in error.items():
                        messages.error(
                            request, mark_safe("{}: {}".format(k.title(), v))
                        )
            context = {
                'form': form,
                'picture_formset': picture_formset,
                'sidenav_selection': 'page_list'
            }

            return TemplateResponse(request, self.template_name, context)

        return HttpResponseRedirect(self.get_success_url(name=page.name))

    def get_success_url(self, name):
        return reverse(
            'studioadmin:edit_page', kwargs={'name': name}
        )


class PageCreateView(LoginRequiredMixin, StaffUserMixin, CreateView):

    model = Page
    template_name = 'studioadmin/page_create_update.html'
    context_object_name = 'page'
    form_class = PageForm

    def get_context_data(self, **kwargs):
        context = super(PageCreateView, self).get_context_data(**kwargs)
        context['sidenav_selection'] = 'page_list'

        picture_formset = PictureFormset()
        context['picture_formset'] = picture_formset
        return context

    def post(self, request, *args, **kwargs):
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save()
            picture_formset = PictureFormset(
                request.POST, request.FILES, instance=page
            )

            if form.is_valid() and picture_formset.is_valid():
                form.save()
                picture_formset.save()

                messages.success(request, mark_safe(
                    "Page {} has been created".format(page.name.title())
                    )
                )
            else:
                if not picture_formset.is_valid():
                    for error in picture_formset.errors:
                        for k, v in error.items():
                            messages.error(
                                request, mark_safe("{}: {}".format(k.title(), v))
                            )

                context = {
                    'form': form,
                    'picture_formset': picture_formset,
                    'sidenav_selection': 'page_list'
                }

                return TemplateResponse(request, self.template_name, context)
        else:
            picture_formset = PictureFormset(request.POST, request.FILES)
            return TemplateResponse(
                    request, self.template_name,
                    {'form': form, 'picture_formset': picture_formset,
                     'sidenav_selection': 'add_page'}
                    )

            return TemplateResponse(request, self.template_name, context)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:website_pages_list')
