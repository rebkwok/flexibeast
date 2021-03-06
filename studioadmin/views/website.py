import logging

from django.contrib import messages
from django.urls import reverse
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404
from django.views.generic import CreateView, ListView, UpdateView
from django.utils.safestring import mark_safe

from braces.views import LoginRequiredMixin

from activitylog.models import ActivityLog

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
            deleted_page_ids = []
            for form in pages_forms:
                if form.has_changed() and 'DELETE' in form.changed_data:
                    page = Page.objects.get(id=form.instance.id)

                    # delete associated pictures
                    # loop to delete pics so we call delete() on each instance
                    [pic.delete() for pic in Picture.objects.filter(page=page)]

                    deleted_page_names.append(page.name)
                    deleted_page_ids.append(page.id)
                    # delete page
                    page.delete()

            if len(deleted_page_names) == 1:
                msg = "Page '{}' has been deleted".format(deleted_page_names[0])
                ActivityLog.objects.create(
                    log="Page {} (id {}) has been deleted by admin "
                        "user {}".format(
                        deleted_page_names[0], deleted_page_ids[0],
                        request.user.username
                    )
                )
            elif len(deleted_page_names) > 1:
                msg = "Pages {} have been deleted".format(
                    ', '.join(["'{}'".format(name) for name in deleted_page_names]),
                )
                ActivityLog.objects.create(
                    log= "Pages {} (ids {}) have been deleted by admin "
                         "user {}".format(
                        ', '.join(
                            ["{}".format(name) for name in deleted_page_names]
                        ),
                        ', '.join(
                            ['{}'.format(pageid for pageid in deleted_page_ids)]
                        ),
                        request.user.username
                    )
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
                                    page.name
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
                ActivityLog.objects.create(
                    log="Page {} (id {}) has been updated by admin user "
                        "{}: {}".format(
                        page.name, page.id, request.user.username,
                        ', '.join(change_messages)
                    )
                )

            else:
                messages.info(request, "No changes made")
        else:
            messages.error(request, "Please correct the errors below")
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
                    "Page {} has been created".format(page.name)
                    )
                )
                ActivityLog.objects.create(
                    log="Page {} (id {}) has been created by admin "
                        "user {}".format(
                        page.name, page.id, request.user.username
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
            messages.error(request, "Please correct the errors below")
            picture_formset = PictureFormset(request.POST, request.FILES)
            return TemplateResponse(
                    request, self.template_name,
                    {'form': form, 'picture_formset': picture_formset,
                     'sidenav_selection': 'add_page'}
                    )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:website_pages_list')
