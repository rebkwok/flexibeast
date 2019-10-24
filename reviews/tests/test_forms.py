from model_bakery import baker

from django.test import TestCase

from reviews.forms import ReviewForm, ReviewFormSet
from reviews.models import Review


class ReviewFormTests(TestCase):

    def test_form_valid(self):
        form_data = {
            'user_display_name': 'Me',
            'title': 'Test title',
            'rating': 3,
            'review': 'Not bad'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_data(self):
        # missing title and user_display_name is allowed
        form_data = {
            'rating': 3,
            'review': 'Not bad'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

        form_data = {
            'review': 'Not bad'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'rating': ['This field is required.']}
        )

        form_data = {
            'rating': 2
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'review': ['This field is required.']}
        )

    def test_invalid_rating(self):
        form_data = {
            'rating': 0,
            'review': 'Not bad'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'rating': ['Rating must be between 1 and 5.']}
        )

class ReviewFormSetTests(TestCase):

    def setUp(self):
        self.review = baker.make(Review)

    def test_formset_valid(self):

        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': str(self.review.id),
            }

        formset = ReviewFormSet(data)
        self.assertTrue(formset.is_valid())

        form = formset.forms[0]
        self.assertEqual(form.fields['decision'].initial, 'undecided')


    def test_decision_initial_value(self):

        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': str(self.review.id),
            }

        formset = ReviewFormSet(data, previous='approved')
        self.assertTrue(formset.is_valid())

        form = formset.forms[0]
        self.assertEqual(form.fields['decision'].initial, 'approve')

        formset = ReviewFormSet(data, previous='rejected')
        self.assertTrue(formset.is_valid())

        form = formset.forms[0]
        self.assertEqual(form.fields['decision'].initial, 'reject')

    def test_undecided_choice_not_available_for_previous_reviews(self):
        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': str(self.review.id),
            }

        formset = ReviewFormSet(data)
        form = formset.forms[0]
        decision = form.fields['decision']
        self.assertEqual(len(decision.choices), 3)
        decision_choices = dict(decision.choices)
        self.assertEqual(
            sorted(decision_choices.keys()),
            ['approve', 'reject', 'undecided']
        )

        formset = ReviewFormSet(data, previous='approved')
        form = formset.forms[0]
        decision = form.fields['decision']
        self.assertEqual(len(decision.choices), 2)
        decision_choices = dict(decision.choices)
        self.assertEqual(
            sorted(decision_choices.keys()), ['approve', 'reject']
        )

        formset = ReviewFormSet(data, previous='rejected')
        form = formset.forms[0]
        decision = form.fields['decision']
        self.assertEqual(len(decision.choices), 2)
        decision_choices = dict(decision.choices)
        self.assertEqual(
            sorted(decision_choices.keys()), ['approve', 'reject']
        )
