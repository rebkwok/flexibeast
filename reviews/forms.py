from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet

from reviews.models import Review


class ReviewForm(forms.ModelForm):

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
            'rating': forms.Select(
                choices=((i, i) for i in range(1, 6)),
                attrs={'class': 'form-control'}
            ),
            'review': forms.Textarea(
                attrs={'class': 'form-control'}
            ),
        }


class BaseReviewFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(BaseReviewFormSet, self).add_fields(form, index)
        form.fields['decision'] = forms.ChoiceField(
            widget=forms.RadioSelect(),
            choices=(('approve', 'Approve'), ('reject', 'Reject')),
            required=False
        )

ReviewFormSet = modelformset_factory(
    Review,
    fields=('id',),
    extra=0,
    formset=BaseReviewFormSet,
    can_delete=False
)
