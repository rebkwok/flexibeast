# -*- coding: utf-8 -*-

from datetime import datetime, date

from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet, \
    inlineformset_factory, formset_factory, BaseFormSet, BaseInlineFormSet
from django.utils import timezone

from ckeditor.widgets import CKEditorWidget

from timetable.models import DAY_CHOICES, WeeklySession


DAY_CHOICES_DICT = dict(DAY_CHOICES)


class WeeklySessionBaseFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(WeeklySessionBaseFormSet, self).add_fields(form, index)

        if form.instance:
            form.formatted_day = DAY_CHOICES_DICT[form.instance.day]

            form.fields['full'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': "regular-checkbox studioadmin-list",
                    'id': 'full_{}'.format(index)
                }),
                required=False
            )
            form.full_id = 'full_{}'.format(index)


            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': 'delete-checkbox studioadmin-list',
                    'id': 'DELETE_{}'.format(index)
                }),
                required=False
            )
            form.DELETE_id = 'DELETE_{}'.format(index)

TimetableWeeklySessionFormSet = modelformset_factory(
    WeeklySession,
    fields=('full', ),
    formset=WeeklySessionBaseFormSet,
    extra=0,
    can_delete=True)


class WeeklySessionAdminForm(forms.ModelForm):

    cost = forms.DecimalField(
        widget=forms.TextInput(
            attrs={
                'type': 'text',
                'class': 'form-control',
                'aria-describedby': 'sizing-addon2',
            },
        ),
        initial=7,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(WeeklySessionAdminForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data

        time = self.data.get('time')
        if time:
            if self.errors.get('time'):
                del self.errors['time']
            try:
                time = datetime.strptime(self.data['time'], '%H:%M').time()
                cleaned_data['time'] = time
                if 'time' in self.changed_data and self.instance.id \
                        and self.instance.time.strftime('%H:%M') \
                        == self.data['time']:
                    self.changed_data.remove('time')
            except ValueError:
                self.add_error('time', 'Invalid time format.  Select from the '
                                       'time picker or enter date and time in the '
                                       '24-hour format HH:MM')
        super(WeeklySessionAdminForm, self).clean()
        return cleaned_data

    class Meta:
        model = WeeklySession
        fields = (
            'name', 'day', 'time', 'description', 'location',
            'max_participants', 'contact_person', 'contact_email', 'cost',
            'block_info', 'full'
        )
        widgets = {
            'description': CKEditorWidget(
                attrs={'class': 'form-control container-fluid'},
                config_name='studioadmin',
            ),
            'block_info': CKEditorWidget(
                attrs={'class': 'form-control container-fluid'},
                config_name='studioadmin',
            ),
            'name': forms.TextInput(
                attrs={'class': "form-control",
                       'placeholder': 'Name of session e.g. '
                                      'Flexibility for Splits'},
            ),
            'location': forms.TextInput(
                attrs={'class': "form-control"}
            ),
            'max_participants': forms.TextInput(
                attrs={'class': "form-control"}
            ),
            'contact_person': forms.TextInput(
                attrs={'class': "form-control"}
            ),
            'contact_email': forms.EmailInput(
                attrs={'class': "form-control"}
            ),
            'day': forms.Select(
                choices=DAY_CHOICES,
                attrs={'class': "form-control"}
            ),
            'time': forms.TimeInput(
                attrs={'class': 'form-control',
                       'id': 'timepicker'},
                format="%H:%M"
            ),
            'booking_open': forms.CheckboxInput(
                attrs={
                    'class': "form-control regular-checkbox",
                    'id': 'booking_open_id',
                    }
            ),
            'full': forms.CheckboxInput(
                attrs={
                    'class': "form-control regular-checkbox",
                    'id': 'full_id',
                    }
            ),
        }
