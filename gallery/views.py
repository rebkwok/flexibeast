from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.shortcuts import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from gallery.forms import CategoriesFormset
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

            for form in categories_formset:
                if form.has_changed():
                    deleted_categories = []
                    updated_categories = {}

                    if 'DELETE' in form.changed_data:
                        category = Category.objects.get(id=form.instance.id)

                        # delete associated images
                        # loop to delete so we call delete() on each instance
                        [
                            image.delete() for image in
                            Image.objects.filter(category=category)
                        ]

                        deleted_categories.append(category.name)
                        # delete page
                        category.delete()
                    elif 'name' in form.changed_data:
                        old_cat = Category.objects.get(id=form.instance.id)
                        old_name = old_cat.name
                        new_cat = form.save(commit=False)
                        new_name = new_cat.name
                        updated_categories['category.id'] = [old_name, new_name]

                    if len(deleted_categories) == 1:
                        msg = "Category '{}' and all associated images have been " \
                              "deleted".format(deleted_categories[0])
                    elif len(deleted_categories) > 1:
                        msg = "Categories {} and all associated images have been " \
                              "deleted".format(
                            ', '.join(["'{}'".format(name) for name in deleted_categories])
                        )
                    elif updated_categories:
                        msg = "Category names changed: {}".format(
                            ', '.join(
                                ["'{}' changed to '{}'".format(val[0], val[1])
                                 for key, val in updated_categories.items()]
                            )
                        )
                form.save()
                messages.success(request, msg)
        else:
            messages.info(request, "No changes made")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('gallery:categories')