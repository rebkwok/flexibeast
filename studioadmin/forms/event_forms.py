# -*- coding: utf-8 -*-

import pytz
from datetime import datetime, timedelta

from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet, \
    inlineformset_factory, formset_factory, BaseFormSet, BaseInlineFormSet

from ckeditor.widgets import CKEditorWidget

from flex_bookings.models import Event, EventType

from studioadmin.forms.utils import cancel_choices


class EventBaseFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(EventBaseFormSet, self).add_fields(form, index)

        if form.instance:
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

            if form.instance.bookings.count() > 0:
                delete_class = 'delete-checkbox-disabled studioadmin-list'
            else:
                delete_class = 'delete-checkbox studioadmin-list'
            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': delete_class,
                    'id': 'DELETE_{}'.format(index)
                }),
                required=False
            )
            form.DELETE_id = 'DELETE_{}'.format(index)

EventFormSet = modelformset_factory(
    Event,
    fields=(
        'booking_open', 'advance_payment_required'
    ),
    formset=EventBaseFormSet,
    extra=0,
    can_delete=True
)


class EventAdminForm(forms.ModelForm):

    required_css_class = 'form-error'

    cost = forms.DecimalField(
        widget=forms.TextInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'aria-describedby': 'sizing-addon2',
        }),
        required=False,
        initial=7,
    )

    def __init__(self, *args, **kwargs):
        ev_type = kwargs.pop('ev_type')
        super(EventAdminForm, self).__init__(*args, **kwargs)
        self.fields['event_type'] = forms.ModelChoiceField(
            widget=forms.Select(attrs={'class': "form-control"}),
            queryset=EventType.objects.filter(event_type=ev_type),
            label='{} type'.format('Class' if ev_type == 'CL' else 'Workshop')
        )
        ph_type = "class" if ev_type == 'CL' else 'event'
        ex_name = "Flexibility for Splits" if ev_type == 'CL' \
            else "Splits Workshop"
        self.fields['name'] = forms.CharField(
            widget=forms.TextInput(
                attrs={
                    'class': "form-control",
                    'placeholder': 'Name of {} e.g. {}'.format(ph_type, ex_name)
                }
            )
        )

    def clean(self):
        super(EventAdminForm, self).clean()
        cleaned_data = self.cleaned_data
        is_new = False if self.instance else True

        date = self.data.get('date')
        if date:
            if self.errors.get('date'):
                del self.errors['date']
            try:
                date = datetime.strptime(self.data['date'], '%d %b %Y %H:%M')
                uk = pytz.timezone('Europe/London')
                cleaned_data['date'] = uk.localize(date).astimezone(pytz.utc)
            except ValueError:
                self.add_error('date', 'Invalid date format.  Select from the '
                                       'date picker or enter date and time in the '
                                       'format dd Mmm YYYY HH:MM')

        payment_due_date = self.data.get('payment_due_date')
        if payment_due_date:
            if self.errors.get('payment_due_date'):
                del self.errors['payment_due_date']
            try:
                payment_due_date = datetime.strptime(payment_due_date, '%d %b %Y')
                if payment_due_date < datetime.strptime(
                    self.data['date'],
                    '%d %b %Y %H:%M') - timedelta(
                        hours=cleaned_data.get('cancellation_period')
                    ):

                    cleaned_data['payment_due_date'] = payment_due_date
                else:
                    self.add_error('payment_due_date', 'Payment due date must '
                                                       'be before cancellation'
                                                       ' period starts')
                cleaned_data['payment_due_date'] = payment_due_date
            except ValueError:
                self.add_error(
                    'payment_due_date', 'Invalid date format.  Select from '
                                        'the date picker or enter date in the '
                                        'format dd Mmm YYYY')

        return cleaned_data

    class Meta:
        model = Event
        fields = (
            'name', 'event_type', 'date', 'description', 'location',
            'max_participants', 'contact_person', 'contact_email', 'cost',
            'booking_open', 'advance_payment_required', 'payment_info',
            'payment_due_date', 'cancellation_period',
            'email_studio_when_booked',
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
            'payment_due_date': forms.DateInput(
                attrs={
                    'class': "form-control",
                    'id': "datepicker",
                },
                format='%d %b %Y'
            ),
            'date': forms.DateTimeInput(
                attrs={
                    'class': "form-control",
                    'id': "datetimepicker",
                },
                format='%d %b %Y %H:%M'
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
                    },
            ),
            'email_studio_when_booked': forms.CheckboxInput(
                attrs={
                    'class': "form-control regular-checkbox",
                    'id': 'email_studio_id',
                    },
            ),
            }
        help_texts = {
            'payment_due_date': 'Only use this field if the cost is greater '
                                  'than 0.  If a payment due date is set, '
                                  'advance payment will always be required',
            'email_studio_when_booked': 'Tick if you want the studio to '
                                          'receive email notifications when a '
                                          'booking is made',
            'advance_payment_required': 'If this checkbox is not ticked, '
                                          'unpaid bookings will remain '
                                          'active after the cancellation period '
                                          'and will not be '
                                          'automatically cancelled'
        }
