# -*- coding: utf-8 -*-

from datetime import datetime, date

from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet, \
    inlineformset_factory, formset_factory, BaseFormSet, BaseInlineFormSet
from django.utils import timezone

from ckeditor.widgets import CKEditorWidget

from flex_bookings.models import EventType
from timetable.models import Session, WeeklySession

from studioadmin.forms.utils import cancel_choices


DAY_CHOICES = dict(Session.DAY_CHOICES)


class SessionBaseFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(SessionBaseFormSet, self).add_fields(form, index)

        if form.instance:
            form.formatted_day = DAY_CHOICES[form.instance.day]

            form.fields['booking_open'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': "regular-checkbox studioadmin-list",
                    'id': 'booking_open_{}'.format(index)
                }),
                required=False
            )
            form.booking_open_id = 'booking_open_{}'.format(index)

            form.fields['advance_payment_required'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': "regular-checkbox studioadmin-list",
                    'id': 'advance_payment_required_{}'.format(index)
                }),
                required=False
            )
            form.advance_payment_required_id = 'advance_payment_required_{}'.format(index)

            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': 'delete-checkbox studioadmin-list',
                    'id': 'DELETE_{}'.format(index)
                }),
                required=False
            )
            form.DELETE_id = 'DELETE_{}'.format(index)

TimetableSessionFormSet = modelformset_factory(
    Session,
    fields=(
        'booking_open',
        'advance_payment_required'
    ),
    formset=SessionBaseFormSet,
    extra=0,
    can_delete=True)


class SessionAdminForm(forms.ModelForm):

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
        super(SessionAdminForm, self).__init__(*args, **kwargs)
        self.fields['event_type'] = forms.ModelChoiceField(
            widget=forms.Select(attrs={'class': "form-control"}),
            queryset=EventType.objects.filter(event_type="CL"),
        )

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
        super(SessionAdminForm, self).clean()
        return cleaned_data

    class Meta:
        model = Session
        fields = (
            'name', 'event_type', 'day', 'time', 'description', 'location',
            'max_participants', 'contact_person', 'contact_email', 'cost',
            'booking_open', 'advance_payment_required',
            'payment_info', 'cancellation_period'
        )
        widgets = {
            'description': CKEditorWidget(
                attrs={'class': 'form-control container-fluid'},
                config_name='studioadmin',
            ),
            'payment_info': CKEditorWidget(
                attrs={'class': 'form-control container-fluid'},
                config_name='studioadmin_min',
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
                choices=Session.DAY_CHOICES,
                attrs={'class': "form-control"}
            ),
            'time': forms.TimeInput(
                attrs={'class': 'form-control',
                       'id': 'timepicker'},
                format="%H:%M"
            ),
            'cancellation_period': forms.Select(
                choices=cancel_choices,
                attrs={
                    'class': "form-control",
                    }
            ),
            'booking_open': forms.CheckboxInput(
                attrs={
                    'class': "form-control regular-checkbox",
                    'id': 'booking_open_id',
                    }
            ),
            'advance_payment_required': forms.CheckboxInput(
                attrs={
                    'class': "form-control regular-checkbox",
                    'id': 'advance_payment_required_id',
                    }
            ),
            }

        help_texts = {
            'advance_payment_required': 'If this checkbox is not ticked, '
                                          'unpaid bookings will remain '
                                          'active after the cancellation period '
                                          'and will not be '
                                          'automatically cancelled'
        }


class UploadTimetableForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(UploadTimetableForm, self).__init__(*args, **kwargs)
        self.fields['sessions'] = forms.ModelMultipleChoiceField(
            widget=forms.CheckboxSelectMultiple(),
            label="Choose sessions to upload",
            queryset=Session.objects.all(),
            initial=[session.pk for session in Session.objects.all()],
            required=True
        )

    start_date = forms.DateField(
        label="Start Date",
        widget=forms.DateInput(
            attrs={
                'class': "form-control",
                'id': 'datepicker_startdate'},
            format='%a %d %b %Y'
        ),
        required=True,
        initial=date.today()
    )

    end_date = forms.DateField(
        label="End Date",
        widget=forms.DateInput(
            attrs={
                'class': "form-control",
                'id': 'datepicker_enddate'},
            format='%a %d %b %Y'
        ),
        required=True,
    )

    def clean(self):
        super(UploadTimetableForm, self).clean()
        cleaned_data = self.cleaned_data

        start_date = self.data.get('start_date')
        if start_date:
            if self.errors.get('start_date'):
                del self.errors['start_date']
            try:
                start_date = datetime.strptime(start_date, '%a %d %b %Y').date()
                if start_date >= timezone.now().date():
                    cleaned_data['start_date'] = start_date
                else:
                    self.add_error('start_date',
                                   'Must be in the future')
            except ValueError:
                self.add_error(
                    'start_date', 'Invalid date format.  Select from '
                                        'the date picker or enter date in the '
                                        'format e.g. Mon 08 Jun 2015')

        end_date = self.data.get('end_date')
        if end_date:
            if self.errors.get('end_date'):
                del self.errors['end_date']
            try:
                end_date = datetime.strptime(end_date, '%a %d %b %Y').date()
            except ValueError:
                self.add_error(
                    'end_date', 'Invalid date format.  Select from '
                                        'the date picker or enter date in the '
                                        'format ddd DD Mmm YYYY (e.g. Mon 15 Jun 2015)')

        if not self.errors.get('end_date') and not self.errors.get('start_date'):
            if end_date >= start_date:
                cleaned_data['end_date'] = end_date
            else:
                self.add_error('end_date',
                                   'Cannot be before start date')
        return cleaned_data


class WeeklySessionBaseFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(WeeklySessionBaseFormSet, self).add_fields(form, index)

        if form.instance:
            form.formatted_day = DAY_CHOICES[form.instance.day]

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
        ev = EventType.objects.get_or_create(
            event_type='CL', subtype='Yoga class'
        )
        self.fields['event_type'] = forms.ModelChoiceField(
            widget=forms.Select(attrs={'class': "form-control"}),
            queryset=EventType.objects.filter(event_type="CL",),
            initial=ev
        )

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
            'name', 'event_type', 'day', 'time', 'description', 'location',
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
                choices=Session.DAY_CHOICES,
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
