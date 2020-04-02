

from django import forms
from django.core.validators import RegexValidator
from django.forms.models import modelformset_factory, BaseModelFormSet, \
    inlineformset_factory, formset_factory, BaseFormSet, BaseInlineFormSet
from django.forms.widgets import ClearableFileInput

from ckeditor.widgets import CKEditorWidget
from website.models import Page, Picture



class ImageThumbnailFileInput(ClearableFileInput):
    template_name = 'gallery/image_thumbnail.html'


class PagesBaseFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(PagesBaseFormSet, self).add_fields(form, index)

        if form.instance:
            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': 'delete-checkbox studioadmin-list',
                    'id': 'DELETE_{}'.format(index)
                }),
                required=False
            )
            form.DELETE_id = 'DELETE_{}'.format(index)


PagesFormset = modelformset_factory(
    Page,
    fields=('id',),
    formset=PagesBaseFormSet,
    extra=0,
    can_delete=True
)


class PageForm(forms.ModelForm):

    restricted = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'regular-checkbox studioadmin-list',
            'id': 'id_restricted'
        }),
        label="Restricted",
        required=False,
        help_text='Make this page visible only if user is logged in and has '
                  'been given permission'
        )

    active = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'regular-checkbox studioadmin-list',
            'id': 'id_active'
        }),
        label="Active",
        required=False,
        initial=False,
        help_text="Tick this box if you want this page to be visible "
                  "on the site.  If unchecked, it will only be displayed for"
                  "staff users"
        )

    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[
            RegexValidator(
                regex=r'^([a-zA-Z0-9\/-])+\s*$',
                message="This field must contain only letters, numbers, / or -",
                code='invalid_name'
            )
        ],
        help_text="A unique identifier for this page. Use lowercase, no "
                  "spaces.  Forward slash (/) and hyphens (-) are allowed."
    )

    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)
        if not self.instance.id or self.instance.menu_location == 'dropdown':
            new_menu_choices = list(self.fields['menu_location'].choices)
            new_menu_choices.remove(('main', 'Separate link in main menu'))
            self.fields['menu_location'].choices = tuple(new_menu_choices)
            self.fields['menu_location'].help_text = None

    class Meta:
        model = Page
        fields = (
            'name', 'menu_name', 'menu_location', 'layout', 'heading',
            'content', 'restricted', 'active'
        )
        widgets = {
            'heading': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),
            'menu_name': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),
            'menu_location': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
            'layout': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
            'content': CKEditorWidget(
                attrs={'class': 'form-control'},
                config_name='studioadmin_extended',
            ),
        }


class PictureBaseFormset(BaseInlineFormSet):

    def add_fields(self, form, index):
        super(PictureBaseFormset, self).add_fields(form, index)

        if form.instance.id:

            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': 'delete-checkbox studioadmin-list',
                    'id': 'DELETE_PIC_{}'.format(index)
                }),
                required=False,
                help_text="Tick box and click Save to delete this image"
            )
            form.DELETE_PIC_id = 'DELETE_PIC_{}'.format(index)

        form.fields['main'] = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={
                'class': 'regular-checkbox studioadmin-list',
                'id': 'main_{}'.format(index)
            }),
            label="Main image",
            required=False,
            help_text="Show this image in single-image page layouts"
            )
        form.main_id = 'main_{}'.format(index)

        form.fields['image'] = forms.ImageField(
            label='',
            error_messages={'invalid':"Image files only"},
            widget=ImageThumbnailFileInput,
            required=False
        )

    def clean(self):
        super(PictureBaseFormset, self).clean()

        # only check for main images if there are pictures attached
        # if only 1 form, then it's either an empty blank one, or a single new
        # pic
        if len(self.forms) > 1 or \
                (len(self.forms) == 1 and self.forms[0].instance.image):
            main_pics = [
                form.instance for form in self.forms if form.instance.main == True
            ]
            # raise error if > 1 pic selected as main. Set first pic to main if
            # none selected
            if len(main_pics) > 1:
                self.errors.append(
                    {'main image': 'More than one image is selected as the '
                                   '"main" image to be displayed in single '
                                   'image layouts.  Please select one only.'})
                raise forms.ValidationError(
                    'Only one "main" image can be selected'
                )
            elif len(main_pics) == 0:
                first_form = self.forms[0]
                first_form.instance.main = True
                first_form.instance.save()

PictureFormset = inlineformset_factory(
    Page,
    Picture,
    fields=('image', 'main'),
    formset=PictureBaseFormset,
    can_delete=True,
    extra=1,
)
