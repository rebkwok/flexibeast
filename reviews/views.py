from django.shortcuts import render, HttpResponseRedirect
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q

from braces.views import LoginRequiredMixin

from reviews.forms import ReviewForm, ReviewFormSet, ReviewSortForm
from reviews.models import Review
from reviews.utils import StaffUserMixin, staff_required


class ReviewListView(ListView):

    template_name = 'reviews/reviews.html'
    context_object_name = 'reviews'
    model = Review

    def get_queryset(self):
        return Review.objects.filter(published=True).order_by('-submission_date')

    def get_context_data(self, *args, **kwargs):
        context = super(ReviewListView, self).get_context_data()
        if not self.request.user.is_anonymous():
            user_reviews = Review.objects.filter(user=self.request.user)
            context['user_reviews'] = user_reviews

        order = self.request.GET.get('order', '')
        form = ReviewSortForm(initial={'order': order})
        context['order_sort_form'] = form
        if order:
            context['reviews'] = self.get_queryset().order_by(order)
        return context


class ReviewCreateView(LoginRequiredMixin, CreateView):

    template_name = 'reviews/add_edit_review.html'
    context_object_name = 'review'
    model = Review
    form_class = ReviewForm

    def form_valid(self, form):
        review = form.save(commit=False)
        review.user = self.request.user
        review.save()
        messages.success(self.request, 'Your testimonial has been submitted and will be '
                              'displayed on the site shortly')
        return HttpResponseRedirect(reverse('reviews:reviews'))


class ReviewUpdateView(LoginRequiredMixin, UpdateView):

    template_name = 'reviews/add_edit_review.html'
    context_object_name = 'review'
    model = Review
    form_class = ReviewForm

    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()
        if request.user.is_authenticated() and review.user != request.user:
            return HttpResponseRedirect(settings.PERMISSION_DENIED_URL)
        return super(ReviewUpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your testimonial has been updated and '
                                        'will be displayed on the site shortly')

        return HttpResponseRedirect(reverse('reviews:reviews'))


class StaffReviewListView(StaffUserMixin, ListView):

    template_name = 'reviews/staff_reviews.html'
    context_object_name = 'reviews'
    model = Review

    def dispatch(self, request, *args, **kwargs):
        self.previous = request.GET.getlist('view', [''])[0]
        return super(StaffReviewListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.previous == 'approved':
            # review is approved if it's been reviewed AND is published and
            # hasn't been edited OR has been edited and update_published is true
            queryset = Review.objects.filter(
                Q(reviewed=True),
                Q(published=True, edited=False) |
                Q(update_published=True, edited=True)
            )
        elif self.previous == 'rejected':
            # review is rejected if it's been reviewed AND is not published OR
            # has been edited and update_published is false
            queryset = Review.objects.filter(
                Q(reviewed=True),
                Q(published=False) |
                Q(update_published=False, edited=True)
            )
        else:
            queryset = Review.objects.filter(reviewed=False)
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(StaffReviewListView, self).get_context_data()
        context['review_formset'] = ReviewFormSet(
            queryset=self.get_queryset(), previous=self.previous
        )
        context['showing_previous'] = self.previous
        return context

    def post(self, request):

        review_formset = ReviewFormSet(request.POST)

        if review_formset.has_changed():
            for form in review_formset:
                if form.is_valid():
                    if form.has_changed() and 'decision' in form.changed_data:
                        review = form.save(commit=False)
                        decision = form.cleaned_data.get('decision')
                        if decision == 'approve':
                            review.approve()
                            messages.success(
                                request, 'Review from user {} {} has been '
                                         'approved'.format(
                                    review.user.first_name,
                                    review.user.last_name
                                )
                            )
                        elif decision == 'reject':
                            review.reject()
                            messages.success(
                                request, 'Review from user {} {} has been '
                                         'rejected'.format(
                                    review.user.first_name,
                                    review.user.last_name
                                )
                            )
                        review.save()
            review_formset.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('reviews:staff_reviews')