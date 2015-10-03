from django.conf.urls import include, patterns, url

urlpatterns = patterns('',
    url(r'^$', 'gallery.views.view_gallery', name='view'),
    ##### VIEWS FOR STAFF USER ONLY #####
    # images list, allow editing of image name and category, delete image, filter by category
    # url(r'^images/', ImageListView.as_view(), name='images'),
    # add single image
    # url(r'^images/add$', ImageCreateView.as_view(), name='add_image'),
    # Category list view, show all categories in list, allow  for edit of
    # name and delete of entire category, add new category, links to category detail views
    # url(r'^categories/$', CategoryListView.as_view(), name='categories'),
    # Category detail view, show all images for edit/delete/add
    # url(r'^categories/(?P<pk>\d+)$', CategoryDetailView.as_view(), name='edit_category'),
)
