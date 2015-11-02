from django.conf.urls import include, patterns, url

from reviews.views import ReviewListView, ReviewCreateView, ReviewUpdateView


urlpatterns = patterns('',
    url(r'^$', ReviewListView.as_view(), name='reviews'),
    ##### VIEWS FOR LOGGED IN USER ONLY #####
    # add a review
    url(r'^add$', ReviewCreateView.as_view(), name='add_review'),
    # edit review (allow users to edit their own reviews)
    url(
      r'^(?P<slug>[\w-]+)/edit$', ReviewUpdateView.as_view(), name='edit_review'
    ),
    ##### VIEWS FOR STAFF USER ONLY #####
    # listview for all reviews, button to publish/reject
)
