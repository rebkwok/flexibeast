from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.shortcuts import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe

from gallery.forms import CategoryForm, CategoriesFormset, ImageFormset
from gallery.models import Category, Image
from gallery.utils import StaffUserMixin, staff_required

def view_gallery(request):
    categories = Category.objects.all().order_by('name')
    category_choice = request.GET.getlist('category', ['All'])[0]
    if category_choice == 'All':
        images = Image.objects.all()
        cat_selection = 'All'
    else:
        images = Image.objects.filter(category__id=int(category_choice))
        cat_selection = int(category_choice)

    return render(
        request,
        'gallery/gallery.html',
        {
            'cat_selection': cat_selection,
            'categories': categories,
            'images': images,
            'total_image_count': Image.objects.all().count()
        }
    )


class CategoryListView(StaffUserMixin, ListView):

    model = Category
    template_name = 'gallery/categories.html'
    context_object_name = 'categories'

    def get_context_data(self):
        context = super(CategoryListView, self).get_context_data()
        context['categories_formset'] = CategoriesFormset()
        return context

    def post(self, request, *args, **kwargs):
        categories_formset = CategoriesFormset(request.POST)

        if categories_formset.has_changed():

            deleted_categories = []
            updated_categories = {}
            new_categories = []

            for form in categories_formset:
                if form.has_changed():
                    if 'DELETE' in form.changed_data:
                        category = Category.objects.get(id=form.instance.id)
                        deleted_categories.append(category.name)
                        category.delete()
                    else:
                        if 'name' in form.changed_data:
                            try:
                                old_cat = Category.objects.get(id=form.instance.id)
                                old_name = old_cat.name
                                new_cat = form.save(commit=False)
                                new_name = new_cat.name
                                updated_categories['category.id'] = [old_name, new_name]
                            except Category.DoesNotExist:  # creating a new category
                                cat = form.save(commit=False)
                                new_categories.append(cat.name)
                        form.save()

            del_msg = ""
            upd_msg = ""
            new_msg = ""

            if len(deleted_categories) == 1:
                del_msg = "Category '{}' and all associated images have been " \
                      "deleted".format(deleted_categories[0])
            elif len(deleted_categories) > 1:
                del_msg = "Categories {} and all associated images have been " \
                      "deleted".format(
                    ', '.join(["'{}'".format(name) for name in deleted_categories])
                )
            if updated_categories:
                upd_msg = "Category names changed: {}".format(
                    ', '.join(
                        ["'{}' changed to '{}'".format(val[0], val[1])
                         for key, val in updated_categories.items()]
                    )
                )
            if len(new_categories) == 1:
                new_msg = "Category '{}' has been created".format(new_categories[0])
            elif len(new_categories) > 1:
                del_msg = "Categories {} have been created".format(
                    ', '.join(["'{}'".format(name) for name in new_categories])
                )

            messages.success(
                request,
                mark_safe(
                    "{}{}{}".format(
                        "{}</br>".format(del_msg) if del_msg else "",
                        "{}</br>".format(upd_msg) if del_msg else "",
                        "{}".format(new_msg)
                    )
                )
            )

        else:
            messages.info(request, "No changes made")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('gallery:categories')


class CategoryUpdateView(UpdateView):

    model = Category
    template_name = 'gallery/category_update.html'
    context_object_name = 'category'
    form_class = CategoryForm

    def get_object(self):
        queryset = Category.objects.all()
        return get_object_or_404(queryset, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(CategoryUpdateView, self).get_context_data(**kwargs)

        picture_formset = ImageFormset(instance=self.get_object())
        context['image_formset'] = picture_formset
        return context

    def post(self, request, *args, **kwargs):
        category = Category.objects.get(id=self.kwargs['pk'])
        form = CategoryForm(request.POST, instance=category)
        image_formset = ImageFormset(
            request.POST, request.FILES, instance=category
        )

        if form.is_valid() and image_formset.is_valid():

            change_messages = []

            if image_formset.has_changed():
                for form in image_formset.forms:
                    if form.is_valid():
                        image = form.save(commit=False)
                        if 'DELETE' in form.changed_data:
                            name = image.photo.name
                            image.delete()
                            change_messages.append(
                                'Picture {} deleted from "{}" category'.format(
                                    name.split('/')[-1],
                                    category.name.title()
                                )
                            )
                        elif form.has_changed():
                            action = 'edited' if image.id else 'added'
                            image.save()
                            change_messages.append(
                                'Picture {} has been {}'.format(
                                    image.photo.name.split('/')[-1],
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
            if not image_formset.is_valid():
                for error in image_formset.errors:
                    for k, v in error.items():
                        messages.error(
                            request, mark_safe("{}: {}".format(k.title(), v))
                        )
            context = {
                'form': form,
                'image_formset': image_formset,
            }

            return TemplateResponse(request, self.template_name, context)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('gallery:categories')
