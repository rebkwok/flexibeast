from django.test import TestCase

from model_mommy import mommy

from reviews.models import Review

class ReviewModelTests(TestCase):

    def setUp(self):
        self.user = mommy.make_recipe('flex_bookings.user', first_name='Fred')

    def test_new_review(self):
        """
        A new review is unpublished and has no previous values
        """
        review = mommy.make(Review, user=self.user)
        self.assertFalse(review.reviewed)
        self.assertFalse(review.published)
        self.assertEqual(review.rating, 5)
        self.assertFalse(review.previous_rating)
        self.assertFalse(review.previous_review)
        self.assertFalse(review.previous_title)
        self.assertFalse(review.previous_user_display_name)
        self.assertFalse(review.edited)
        self.assertFalse(review.update_published)
        self.assertIsNone(review.edited_date)

        # user_display_name is populated from user's first name if none given
        self.assertEqual(review.user_display_name, 'Fred')

        review1 = mommy.make(
            Review, user=self.user, user_display_name="Not Fred"
        )
        self.assertEqual(review1.user_display_name, 'Not Fred')

    def test_approve_new_review(self):
        """
        Approve sets an unpublished review to published and sets an edited
        review to update_published
        """
        review = mommy.make(Review, user=self.user)
        self.assertFalse(review.reviewed)
        self.assertFalse(review.published)

        review.approve()
        self.assertTrue(review.reviewed)
        self.assertTrue(review.published)

    def test_approve_edited_review(self):
        """
        Approve sets an unpublished review to published and sets an edited
        review to update_published
        """
        review = mommy.make(Review, user=self.user, published=True)
        self.assertFalse(review.update_published)

        review.approve()
        self.assertTrue(review.reviewed)
        self.assertTrue(review.update_published)

    def test_reject_new_review(self):
        """
        Reject sets reviewed to True and does not set published or
        update_published to True
        For an already published review but not edited review, set published to False
        For an already published edited review, set update_published to False
        """
        review = mommy.make(Review, user=self.user)
        self.assertFalse(review.reviewed)
        self.assertFalse(review.published)

        review.reject()
        self.assertTrue(review.reviewed)
        self.assertFalse(review.published)

    def test_reject_approved_review(self):
        """
        Reject sets reviewed to True and does not set published or
        update_published to True
        For an already published review but not edited review, set published to False
        For an already published edited review, set update_published to False
        """
        review = mommy.make(Review, user=self.user, published=True, edited=False)
        self.assertTrue(review.published)
        self.assertFalse(review.update_published)

        review.reject()
        self.assertTrue(review.reviewed)
        self.assertFalse(review.published)
        self.assertFalse(review.update_published)

    def test_reject_edited_review(self):
        """
        Reject sets reviewed to True and does not set published or
        update_published to True
        For an already published review but not edited review, set published to False
        For an already published edited review, set update_published to False
        """
        review = mommy.make(
            Review, user=self.user, published=True, edited=True
        )
        self.assertTrue(review.published)
        self.assertFalse(review.update_published)

        review.reject()
        self.assertTrue(review.reviewed)
        self.assertTrue(review.published)
        self.assertFalse(review.update_published)

    def test_reject_edited_published_review(self):
        """
        Reject sets reviewed to True and does not set published or
        update_published to True
        For an already published review but not edited review, set published to False
        For an already published edited review, set update_published to False
        """
        review = mommy.make(
            Review, user=self.user, published=True, edited=True,
            update_published=True
        )
        self.assertTrue(review.published)
        self.assertTrue(review.update_published)

        review.reject()
        self.assertTrue(review.reviewed)
        self.assertTrue(review.published)
        self.assertFalse(review.update_published)

    def test_updated_existing_review(self):
        """
        Updating user_display_name, review, rating or title sets the previous
        values for these fields and sets edited to True and reviewed to False
        """
        review = mommy.make(Review, reviewed=True, published=True)
        orig_rating = review.rating
        orig_title = review.title
        orig_review = review.review
        orig_user_display = review.user_display_name
        self.assertEqual(review.rating, 5)
        self.assertIsNone(review.previous_rating)
        self.assertIsNone(review.previous_review)
        self.assertIsNone(review.previous_title)
        self.assertIsNone(review.previous_user_display_name)
        self.assertFalse(review.edited)
        self.assertFalse(review.update_published)
        self.assertIsNone(review.edited_date)

        review.rating = 3
        review.save()

        self.assertEqual(review.previous_rating, orig_rating)
        self.assertEqual(review.previous_user_display_name, orig_user_display)
        self.assertEqual(review.previous_title, orig_title)
        self.assertEqual(review.previous_review, orig_review)
        self.assertIsNotNone(review.edited_date)
        self.assertTrue(review.edited)
        self.assertFalse(review.reviewed)

    def test_str(self):
        review = mommy.make(Review, user=self.user)
        self.assertEqual(
            str(review),
            "Fred - {}".format(review.submission_date.strftime('%d-%b-%y'))
        )
