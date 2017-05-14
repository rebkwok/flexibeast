from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet
from django.utils.safestring import mark_safe


from django.core.exceptions import ValidationError

from reviews.models import Review


def validate_rating(value):
    if value < 1 or value > 5:
        raise ValidationError(
            'Rating must be between 1 and 5.'
        )


class ReviewForm(forms.ModelForm):

    rating = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                'class': 'rating fa-lg',
                'data-max': '5',
                'data-min': '1',
                'data-icon-lib': 'fa',
                'data-active-icon': 'fa-star fa-lg',
                'data-inactive-icon': 'fa-star-o fa-lg',
                'name': 'rating'
            }
        ),
        initial=5,
        validators=[validate_rating],
        help_text="Click on a star to select rating"
    )

    class Meta:
        model = Review
        fields = ('user_display_name', 'title', 'rating', 'review')
        widgets = {
            'user_display_name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'title': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'review': forms.Textarea(
                attrs={'class': 'form-control'}
            ),
        }


class ReviewSortForm(forms.Form):

    order_choices = (
        ('-submission_date', 'Date submitted (most recent first)'),
        ('submission_date', 'Date submitted (earliest first)'),
        ('-rating', 'Rating (high to low)'),
        ('rating', 'Rating (low to high)'),
        ('user', 'Author name')
    )
    order = forms.ChoiceField(
        widget=forms.Select(attrs={'onchange': 'form.submit()'}),
        choices=order_choices,
        required=False
    )


class BaseReviewFormSet(BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        self.previous = kwargs.pop('previous', '')
        super(BaseReviewFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = True

    def add_fields(self, form, index):
        super(BaseReviewFormSet, self).add_fields(form, index)

        if self.previous:
            # don't show option to reset to undecided if already approved or
            # rejected
            review_choices = REVIEW_CHOICES[0:2]
        else:
            review_choices = REVIEW_CHOICES

        if self.previous == 'approved':
            initial = 'approve'
        elif self.previous == 'rejected':
            initial = 'reject'
        else:
            initial = 'undecided'

        form.fields['decision'] = forms.ChoiceField(
            widget=forms.RadioSelect(attrs={'class': 'inline'}),
            choices=review_choices,
            initial=initial,
            required=False
        )

ReviewFormSet = modelformset_factory(
    Review,
    fields=('id',),
    extra=0,
    formset=BaseReviewFormSet,
    can_delete=False
)


REVIEW_CHOICES = (
  ('approve', mark_safe('<span class="fa fa-thumbs-up fa-lg" alt="approve" title="approve">')),
  ('reject', mark_safe('<span class="fa fa-thumbs-down fa-lg" alt="reject" title="reject">')),
  ('undecided', mark_safe('<span class="fa fa-question-circle fa-lg" alt="undecided" title="undecided">')),
)
