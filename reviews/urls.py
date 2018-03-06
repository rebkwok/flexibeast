from django.urls import path

from reviews.views import ReviewListView, ReviewCreateView, \
    ReviewUpdateView, StaffReviewListView


app_name = 'reviews'


urlpatterns = [
    path('', ReviewListView.as_view(), name='reviews'),
    ##### VIEWS FOR LOGGED IN USER ONLY #####
    # add a review
    path('add/', ReviewCreateView.as_view(), name='add_review'),
    # edit review (allow users to edit their own reviews)
    path(
      '<slug:slug>/edit/', ReviewUpdateView.as_view(), name='edit_review'
    ),
    ##### VIEWS FOR STAFF USER ONLY #####
    # listview for all reviews, button to publish/reject
    path('staff-review/', StaffReviewListView.as_view(), name='staff_reviews')
]
