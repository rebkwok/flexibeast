from django.conf.urls import url
from gallery.views import CategoryListView, CategoryUpdateView, view_gallery

urlpatterns = [
    url(r'^$', view_gallery, name='gallery'),
    ##### VIEWS FOR STAFF USER ONLY #####
    # Category list view, show all categories in list, allow  for edit of
    # name and delete of entire category, add new category, links to category
    # detail views
    url(r'^categories/$', CategoryListView.as_view(), name='categories'),
    # Category detail view, show all images for edit/delete/add
    url(
        r'^categories/(?P<pk>\d+)$', CategoryUpdateView.as_view(),
        name='edit_category'
    ),
]
