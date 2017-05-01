from model_mommy import mommy

from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.test.client import Client

from reviews.models import Review
from reviews.tests.helpers import set_up_fb, _create_session
from reviews.views import ReviewListView, ReviewCreateView, ReviewUpdateView, \
        StaffReviewListView


class ReviewTestMixin(object):
    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('common.user')
        self.staff_user = mommy.make_recipe('common.user')
        self.staff_user.is_staff = True
        self.staff_user.save()


class ReviewListViewTests(ReviewTestMixin, TestCase):

    def setUp(self):
        super(ReviewListViewTests, self).setUp()
        self.user_review = mommy.make(Review, user=self.user, published=True)
        mommy.make(Review, published=True, _quantity=4)
        mommy.make(Review, published=False, _quantity=2)

    def _get_response(self, user, data={}):
        url = reverse('reviews:reviews')
        request = self.factory.get(url, data)
        request.user = user
        view = ReviewListView.as_view()
        return view(request)

    def test_all_published_reviews_shown(self):
        resp = self.client.get(reverse('reviews:reviews'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Review.objects.count(), 7)
        # only published reviews shown
        self.assertEqual(len(resp.context_data['reviews']), 5)

    def test_no_add_or_edit_buttons_if_not_logged_in(self):
        resp = self.client.get(reverse('reviews:reviews'))
        self.assertNotIn('Add a testimonial', resp.rendered_content)
        self.assertNotIn('Edit', resp.rendered_content)

        resp = self._get_response(self.user)
        self.assertIn('Add a testimonial', resp.rendered_content)
        self.assertIn('Edit', resp.rendered_content)

    def test_edit_buttons_for_current_users_reviews_only(self):
        resp = self._get_response(self.user)
        self.assertEqual(resp.rendered_content.count('Edit'), 1)

        mommy.make(Review, user=self.user, published=True)
        resp = self._get_response(self.user)
        self.assertEqual(resp.rendered_content.count('Edit'), 2)

    def test_admin_link_if_staff_user(self):
        resp = self._get_response(self.user)
        self.assertNotIn(
                'ADMIN USE: Review and approve submitted testimonials',
                resp.rendered_content
        )
        resp = self._get_response(self.staff_user)
        self.assertIn(
                'ADMIN USE: Review and approve submitted testimonials',
                resp.rendered_content
        )

    def test_sorting_reviews(self):
        # default shows reviews ordered by most recent submission date
        resp = self.client.get(reverse('reviews:reviews'))
        self.assertEqual(
            [review.id for review in resp.context_data['reviews']],
            [
                review.id for review in Review.objects.filter(
                    published=True
                ).order_by('-submission_date')
            ]
        )

        resp = self.client.get(
                reverse('reviews:reviews'), {'order': 'submission_date'}
        )
        self.assertEqual(
            [review.id for review in resp.context_data['reviews']],
            [
                review.id for review in Review.objects.filter(
                    published=True
                ).order_by('submission_date')
            ]
        )

        resp = self.client.get(
                reverse('reviews:reviews'), {'order': '-rating'}
        )
        self.assertEqual(
            [review.id for review in resp.context_data['reviews']],
            [
                review.id for review in Review.objects.filter(
                    published=True
                ).order_by('-rating')
            ]
        )

        resp = self.client.get(
                reverse('reviews:reviews'), {'order': 'rating'}
        )
        self.assertEqual(
            [review.id for review in resp.context_data['reviews']],
            [
                review.id for review in Review.objects.filter(
                    published=True
                ).order_by('rating')
            ]
        )

        resp = self.client.get(
                reverse('reviews:reviews'), {'order': 'user'}
        )
        self.assertEqual(
            [review.id for review in resp.context_data['reviews']],
            [
                review.id for review in Review.objects.filter(
                    published=True
                ).order_by('user')
            ]
        )

    def test_latest_published_edit_shown(self):
        review = mommy.make(Review, review='first review', published=True)
        resp = self.client.get(reverse('reviews:reviews'))
        self.assertIn('first review', resp.rendered_content)

        review.review = 'second review'
        review.save()
        self.assertTrue(review.edited)
        self.assertFalse(review.update_published)

        # edited version not published yet, still shows first review
        resp = self.client.get(reverse('reviews:reviews'))
        self.assertIn('first review', resp.rendered_content)
        self.assertNotIn('second review', resp.rendered_content)

        review.approve()
        # after approval the second version is shown
        self.assertTrue(review.update_published)
        self.assertTrue(review.edited)

        resp = self.client.get(reverse('reviews:reviews'))
        self.assertNotIn('first review', resp.rendered_content)
        self.assertIn('second review', resp.rendered_content)


class ReviewCreateViewTests(ReviewTestMixin, TestCase):

    def _get_response(self, user):
        url = reverse('reviews:add_review')
        request = self.factory.get(url)
        request.user = user
        view = ReviewCreateView.as_view()
        return view(request)

    def _post_response(self, user, data):
        url = reverse('reviews:add_review')
        request = self.factory.post(url, data)
        store = _create_session()
        request.session = store
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = ReviewCreateView.as_view()
        return view(request)

    def test_login_required(self):
        resp = self.client.get(reverse('reviews:add_review'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(
            resp.url,
            reverse('login') + '?next={}'.format(reverse('reviews:add_review'))
        )

        resp = self._get_response(self.user)
        self.assertEqual(resp.status_code, 200)

    def test_create_review(self):
        self.assertFalse(Review.objects.exists())
        data = {'review': 'OK', 'rating': 2}
        resp = self._post_response(self.user, data)

        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.first().user, self.user)

    def test_review_created_as_unapproved(self):
        self.assertFalse(Review.objects.exists())
        data = {'review': 'OK', 'rating': 2}
        resp = self._post_response(self.user, data)

        self.assertFalse(Review.objects.first().reviewed)
        self.assertFalse(Review.objects.first().published)
        self.assertFalse(Review.objects.first().update_published)


class ReviewUpdateViewTests(ReviewTestMixin, TestCase):

    def _get_response(self, user, review_slug):
        url = reverse('reviews:edit_review', kwargs={'slug': review_slug})
        request = self.factory.get(url)
        request.user = user
        view = ReviewUpdateView.as_view()
        return view(request, slug=review_slug)

    def _post_response(self, user, review_slug, data):
        url = reverse('reviews:edit_review', kwargs={'slug': review_slug})
        request = self.factory.post(url, data)
        store = _create_session()
        request.session = store
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = ReviewUpdateView.as_view()
        return view(request, slug=review_slug)

    def test_login_required(self):
        review = mommy.make(Review, user=self.user)
        resp = self.client.get(
                reverse('reviews:edit_review', kwargs={'slug': review.slug})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(
            resp.url,
            reverse('login') + '?next={}'.format(
                reverse('reviews:edit_review', kwargs={'slug': review.slug})
            )
        )

        resp = self._get_response(self.user, review.slug)
        self.assertEqual(resp.status_code, 200)

    def test_cannot_get_another_users_review(self):
        review = mommy.make(Review)
        self.assertNotEqual(review.user, self.user)
        resp = self._get_response(self.user, review.slug)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, settings.PERMISSION_DENIED_URL)

    def test_can_update_review(self):
        review = mommy.make(Review, user=self.user)
        resp = self._post_response(
                self.user, review.slug,
                {
                    'title': 'new title',
                    'review': review.review,
                    'rating': review.rating
                }
        )

        review.refresh_from_db()
        self.assertEqual(review.title, 'new title')

    def test_updated_review_marked_not_reviewed_or_published(self):
        review = mommy.make(Review, user=self.user)
        review.approve()
        resp = self._post_response(
                self.user, review.slug,
                {
                    'title': 'new title',
                    'review': review.review,
                    'rating': review.rating
                }
        )

        review.refresh_from_db()
        self.assertEqual(review.title, 'new title')
        self.assertTrue(review.published)
        self.assertTrue(review.edited)
        self.assertFalse(review.reviewed)
        self.assertFalse(review.update_published)


class StaffReviewListViewTests(ReviewTestMixin, TestCase):

    def setUp(self):
        super(StaffReviewListViewTests, self).setUp()
        # reviews:
        # 1 pending first review
        # 1 pending update review
        # 1 reviewed and approved/published
        # 1 reviewed and rejected
        # 1 updated and reviewed and accepted/published
        # 1 updated and reviewed and rejected

        self.review_pending = mommy.make(Review)
        self.review_published = mommy.make(Review)
        self.review_published.approve()
        self.review_rejected = mommy.make(Review)
        self.review_rejected.reject()
        self.review_update_pending = mommy.make(Review)
        self.review_update_pending.approve()
        self.review_update_pending.title = "updated title"
        self.review_update_pending.save()
        self.review_update_published = mommy.make(Review)
        self.review_update_published.approve()
        self.review_update_published.title = "updated title"
        self.review_update_published.save()
        self.review_update_published.approve()
        self.review_update_rejected = mommy.make(Review)
        self.review_update_rejected.approve()
        self.review_update_rejected.title = "updated title"
        self.review_update_rejected.save()
        self.review_update_rejected.reject()

    def _get_response(self, user, data={}):
        url = reverse('reviews:staff_reviews')
        request = self.factory.get(url, data)
        request.user = user
        view = StaffReviewListView.as_view()
        return view(request)

    def _post_response(self, user, data):
        url = reverse('reviews:staff_reviews')
        request = self.factory.post(url, data)
        store = _create_session()
        request.session = store
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages
        view = StaffReviewListView.as_view()
        return view(request)

    def test_staff_user_required(self):
        resp = self._get_response(self.user)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, reverse(settings.PERMISSION_DENIED_URL))

        resp = self._get_response(self.staff_user)
        self.assertEqual(resp.status_code, 200)

    def test_view_default_pending_list(self):
        """
        Show reviews that are pending either initial review or
        edited review.  Review is pending if reviewed == False
        """
        resp = self._get_response(self.staff_user)
        self.assertEqual(Review.objects.count(), 6)
        self.assertEqual(len(resp.context_data['reviews']), 2)
        self.assertEqual(
            sorted(review.id for review in resp.context_data['reviews']),
            sorted([self.review_pending.id, self.review_update_pending.id])
        )

    def test_view_approved_list(self):
        """
        Review is approved if:
        it's been reviewed AND
           is published AND hasn't been edited
           OR
           has been edited and update_published is true
        """
        resp = self._get_response(self.staff_user, {'view': 'approved'})
        self.assertEqual(Review.objects.count(), 6)
        self.assertEqual(len(resp.context_data['reviews']), 2)
        self.assertEqual(
            sorted(review.id for review in resp.context_data['reviews']),
            sorted([self.review_published.id, self.review_update_published.id])
        )

    def test_view_rejected_list(self):
        """
        Review is rejected if
        it's been reviewed AND
          is not published
          OR
          has been edited and update_published is false
         """
        resp = self._get_response(self.staff_user, {'view': 'rejected'})
        self.assertEqual(Review.objects.count(), 6)
        self.assertEqual(len(resp.context_data['reviews']), 2)
        self.assertEqual(
            sorted(review.id for review in resp.context_data['reviews']),
            sorted([self.review_rejected.id, self.review_update_rejected.id])
        )

    def test_approve_review_first_submission(self):
        form_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-id': str(self.review_pending.id),
            'form-0-decision': 'approve',
            'form-1-id': str(self.review_update_pending.id),
        }
        self._post_response(self.staff_user, form_data)
        self.review_pending.refresh_from_db()
        self.review_update_pending.refresh_from_db()

        self.assertTrue(self.review_pending.reviewed)
        self.assertTrue(self.review_pending.published)
        self.assertFalse(self.review_update_pending.reviewed)
        self.assertFalse(self.review_update_pending.update_published)

    def test_approve_review_updated_submission(self):
        form_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-id': str(self.review_pending.id),
            'form-1-id': str(self.review_update_pending.id),
            'form-1-decision': 'approve',
        }
        self._post_response(self.staff_user, form_data)
        self.review_pending.refresh_from_db()
        self.review_update_pending.refresh_from_db()

        self.assertFalse(self.review_pending.reviewed)
        self.assertFalse(self.review_pending.published)
        self.assertTrue(self.review_update_pending.reviewed)
        self.assertTrue(self.review_update_pending.update_published)

    def test_reject_review_first_submission(self):
        form_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-id': str(self.review_pending.id),
            'form-0-decision': 'reject',
            'form-1-id': str(self.review_update_pending.id),
        }
        self._post_response(self.staff_user, form_data)
        self.review_pending.refresh_from_db()
        self.review_update_pending.refresh_from_db()

        self.assertTrue(self.review_pending.reviewed)
        self.assertFalse(self.review_pending.published)
        self.assertFalse(self.review_update_pending.reviewed)
        self.assertFalse(self.review_update_pending.update_published)

    def test_reject_review_updated_submission(self):
        form_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-id': str(self.review_pending.id),
            'form-1-id': str(self.review_update_pending.id),
            'form-1-decision': 'reject',
        }
        self._post_response(self.staff_user, form_data)
        self.review_pending.refresh_from_db()
        self.review_update_pending.refresh_from_db()

        self.assertFalse(self.review_pending.reviewed)
        self.assertFalse(self.review_pending.published)
        self.assertTrue(self.review_update_pending.reviewed)
        self.assertFalse(self.review_update_pending.update_published)
