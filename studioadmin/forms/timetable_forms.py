# -*- coding: utf-8 -*-
import pytz

from datetime import datetime, date

from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet, \
    inlineformset_factory, formset_factory, BaseFormSet, BaseInlineFormSet
from django.utils import timezone

from ckeditor.widgets import CKEditorWidget

from timetable.models import DAY_CHOICES, WeeklySession, StretchClinic


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


class StretchClinicBaseFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(StretchClinicBaseFormSet, self).add_fields(form, index)

        if form.instance:
            form.fields['show_on_site'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': "regular-checkbox studioadmin-list",
                    'id': 'show_on_site_{}'.format(index)
                }),
                required=False
            )
            form.show_on_site_id = 'show_on_site_{}'.format(index)

            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': 'delete-checkbox studioadmin-list',
                    'id': 'DELETE_{}'.format(index)
                }),
                required=False
            )
            form.DELETE_id = 'DELETE_{}'.format(index)

StretchClinicFormSet = modelformset_factory(
    StretchClinic,
    fields=('show_on_site', ),
    formset=StretchClinicBaseFormSet,
    extra=0,
    can_delete=True)


class EditSessionForm(forms.ModelForm):

    class Meta:
        model = WeeklySession

        fields = (
            'name', 'day', 'time', 'description', 'location',
            'max_participants', 'cost', 'block_info'
        )

        widgets = {
            'name': forms.TextInput(
                attrs={'class': "form-control input-sm"}
            ),
            'day': forms.Select(
                attrs={'class': "form-control input-sm"}
            ),
            'time': forms.TimeInput(
                attrs={'class': 'form-control',
                       'id': 'timepicker'},
                format="%H:%M"
            ),
            'description': forms.Textarea(
                attrs={'class': "form-control input-sm", 'rows': 4}
            ),
            'location': forms.Select(
                attrs={'class': "form-control input-sm"}
            ),
            'max_participants': forms.TextInput(
                attrs={'class': "form-control input-sm"}
            ),
            'cost': forms.TextInput(
                attrs={'class': "form-control input-sm"}
            ),
            'block_info': forms.Textarea(
                attrs={'class': "form-control input-sm", 'rows': 2}
            ),
        }

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
        return super(EditSessionForm, self).clean()


class EditStretchClinicForm(forms.ModelForm):

    class Meta:
        model = StretchClinic

        fields = (
            'date', 'description', 'location',
            'max_spaces', 'cost', 'spaces', 'show_on_site'
        )

        widgets = {
            'date': forms.DateInput(
                attrs={
                    'class': "form-control",
                    'id': "datepicker",
                },
                format='%d %b %Y'
            ),
            'description': forms.Textarea(
                attrs={'class': "form-control input-sm", 'rows': 4}
            ),
            'location': forms.Select(
                attrs={'class': "form-control input-sm"}
            ),
            'max_spaces': forms.TextInput(
                attrs={'class': "form-control input-sm"}
            ),
            'cost': forms.TextInput(
                attrs={'class': "form-control input-sm"}
            ),
            'spaces': forms.TextInput(
                attrs={'class': "form-control input-sm"}
            ),
            'show_on_site': forms.CheckboxInput,
        }

    def __init__(self, *args, **kwargs):
        super(EditStretchClinicForm, self).__init__(*args, **kwargs)
        self.fields['max_spaces'].label = 'Max clinic slots'
        self.fields['spaces'].label = 'Spaces left'

    def clean(self):
        if self.cleaned_data['spaces'] > self.cleaned_data['max_spaces']:
            self.add_error('spaces', 'Spaces left cannot exceed max clinic slots')

        date = self.data.get('date')
        if date:
            if self.errors.get('date'):
                del self.errors['date']
            try:
                date = datetime.strptime(self.data['date'], '%d %b %Y')
                uk = pytz.timezone('Europe/London')
                self.cleaned_data['date'] = uk.localize(date).astimezone(pytz.utc)
                if self.instance.id:
                    old_clinic = StretchClinic.objects.get(id=self.instance.id)
                    if old_clinic.date == self.cleaned_data['date']:
                        self.changed_data.remove('date')
            except ValueError:
                self.add_error('date', 'Invalid date format.  Select from the '
                                       'date picker or enter date in the '
                                       'format dd Mmm YYYY')

        return super(EditStretchClinicForm, self).clean()

