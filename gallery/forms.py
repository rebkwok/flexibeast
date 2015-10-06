from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet

from floppyforms import ClearableFileInput

from gallery.models import Category


class CategoriesBaseFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(CategoriesBaseFormSet, self).add_fields(form, index)

        if form.instance:
            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': 'delete-checkbox',
                    'id': 'DELETE_{}'.format(index)
                }),
                required=False
            )
            form.DELETE_id = 'DELETE_{}'.format(index)

            form.image_count = form.instance.images.count()

        form.fields['name'] = forms.CharField(
            widget=forms.TextInput(
                attrs={'class': 'form-control'}
            )
        )

CategoriesFormset = modelformset_factory(
    Category,
    fields=('id', 'name'),
    formset=CategoriesBaseFormSet,
    extra=0,
    can_delete=True
)