from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.conf import settings

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
            widget=forms.RadioSelect(renderer=HorizontalRadioRenderer),
            choices=REVIEW_CHOICES,
            initial='undecided',
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
  ('approve', mark_safe(_('<span class="fa fa-thumbs-up fa-lg" alt="approve" title="approve">'))),
  ('reject', mark_safe(_('<span class="fa fa-thumbs-down fa-lg" alt="approve" title="approve">'))),
  ('undecided',mark_safe(_('<span class="fa fa-question-circle fa-lg" alt="approve" title="approve">'))),
)


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    """renders horizontal radio buttons.
    found here:
    https://wikis.utexas.edu/display/~bm6432/Django-Modifying+RadioSelect+Widget+to+have+horizontal+buttons
    """

    def render(self):
        return mark_safe(u' &nbsp;&nbsp;&nbsp;'.join([u'%s\n' % w for w in self]))
