from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from braces.views import LoginRequiredMixin

from reviews.models import Review
from reviews.utils import StaffUserMixin, staff_required


class ReviewListView(ListView):

    template_name = 'reviews/reviews.html'
    context_object_name = 'reviews'
    model = Review

    def get_queryset(self):
        return Review.objects.filter(published=True)

    def get_context_data(self, *args, **kwargs):
        context = super(ReviewListView, self).get_context_data()
        if not self.request.user.is_anonymous():
            user_reviews = Review.objects.filter(user=self.request.user)
            context['user_reviews'] = user_reviews
        return context


class ReviewCreateView(LoginRequiredMixin, CreateView):

    template_name = 'reviews/add_edit_review.html'
    context_object_name = 'review'
    model = Review
    fields = ('user_display_name', 'title', 'rating', 'review')


class ReviewUpdateView(LoginRequiredMixin, UpdateView):

    template_name = 'reviews/add_edit_review.html'
    context_object_name = 'review'
    model = Review
    fields = ('user_display_name', 'title', 'rating', 'review')
