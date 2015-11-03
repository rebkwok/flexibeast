from django import forms

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
