from django.conf import settings
from django.urls import path
from gallery.views import category_detail_view, CategoryListView, \
    CategoryUpdateView, gallery_menu_view, view_gallery, gallery_website_view

app_name = 'gallery'


urlpatterns = [
    # path('', gallery_menu_view, name='gallery'),
    path('', gallery_website_view, name='gallery'),
    path('album/<slug:slug>/', category_detail_view, name='category'),
    ##### VIEWS FOR STAFF USER ONLY #####
    # Category list view, show all categories in list, allow  for edit of
    # name and delete of entire category, add new category, links to category
    # detail views
    path('albums/', CategoryListView.as_view(), name='categories'),
    # Category detail view, show all images for edit/delete/add
    path(
        'albums/<int:pk>/', CategoryUpdateView.as_view(),
        name='edit_category'
    )
]


if settings.TESTING:
    urlpatterns.append(path('alternative_view/', view_gallery, name='alternative'))
