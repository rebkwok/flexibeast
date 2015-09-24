import pytz
from datetime import datetime, timedelta, date
import time

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.forms.models import modelformset_factory, BaseModelFormSet, \
    inlineformset_factory, formset_factory, BaseFormSet, BaseInlineFormSet
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from ckeditor.widgets import CKEditorWidget

from flex_bookings.models import Block, Booking, Event, EventType
from timetable.models import Session
from payments.models import PaypalBookingTransaction
from website.models import Page, SubSection, Picture

from floppyforms import ClearableFileInput


class ImageThumbnailFileInput(ClearableFileInput):
    template_name = 'floppyforms/image_thumbnail.html'


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


day = 24
week = day * 7

cancel_choices = (
    (day, '24 hours'),
    (day * 2, '2 days'),
    (day * 3, '3 days'),
    (day * 4, '4 days'),
    (day * 5, '5 days'),
    (day * 6, '6 days'),
    (week, '1 week'),
    (week * 2, '2 weeks'),
    (week * 3, '3 weeks'),
    (week * 4, '4 weeks'),
    (week * 5, '5 weeks'),
    (week * 6, '6 weeks'),
)

dateoptions = {
        'format': 'dd/mm/yyyy hh:ii',
        'autoclose': True,
    }


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
            'payment_due_date': _('Only use this field if the cost is greater '
                                  'than 0.  If a payment due date is set, '
                                  'advance payment will always be required'),
            'email_studio_when_booked': _('Tick if you want the studio to '
                                          'receive email notifications when a '
                                          'booking is made'),
            'advance_payment_required': _('If this checkbox is not ticked, '
                                          'unpaid bookings will remain '
                                          'active after the cancellation period '
                                          'and will not be '
                                          'automatically cancelled')
        }


class BlockBaseForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(BlockBaseForm, self).__init__(*args, **kwargs)

        if self.instance:
            self.fields['booking_open'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': "regular-checkbox studioadmin-list",
                    'id': 'booking_open_{}'.format(self.instance.id)
                }),
                required=False
            )
            self.booking_open_id = 'booking_open_{}'.format(self.instance.id)

            bookings = Booking.objects.filter(
                status='OPEN', block=self.instance
            )
            if bookings.count() > 0:
                self.fields['DELETE'] = forms.BooleanField(
                    widget=forms.CheckboxInput(attrs={
                        'class': 'delete-checkbox-disabled disabled studioadmin-list',
                        'disabled': 'disabled',
                        'id': 'DELETE_{}'.format(self.instance.id)
                    }),
                    required=False
                )
            else:
                self.fields['DELETE'] = forms.BooleanField(
                    widget=forms.CheckboxInput(attrs={
                        'class': 'delete-checkbox studioadmin-list',
                        'id': 'DELETE_{}'.format(self.instance.id)
                    }),
                    required=False
                )
            self.DELETE_id = 'DELETE_{}'.format(self.instance.id)

        self.fields['individual_booking_date'] = forms.CharField(
            widget=(
                forms.DateInput(
                    attrs={
                        'class': "form-control datepicker",
                    },
                    format='%d %b %Y'
                )
            )
        )

    def clean_individual_booking_date(self):

        raw_date = self.cleaned_data['individual_booking_date']
        if raw_date:
            if self.errors.get('individual_booking_date'):
                del self.errors['individual_booking_date']
            if self.instance:
                original_date = self.instance.individual_booking_date
                original_date_fmt = original_date.strftime('%d %b %Y')
                if original_date_fmt == raw_date:
                    self.changed_data.remove('individual_booking_date')
            try:
                # we need to give the date an hour otherwise it will be set to
                # 0 and incorrectly changed to the previous day when we
                # localise for the uk; time will be set back to 0 when the
                # model saves
                individual_booking_date = datetime.strptime(
                    raw_date, '%d %b %Y'
                ).replace(hour=12)
            except ValueError:
                self.add_error(
                    'individual_booking_date',
                    'Invalid date format.  Select from the date picker or '
                    'enter date and time in the format dd Mmm YYYY HH:MM')

            uk = pytz.timezone('Europe/London')
            return uk.localize(individual_booking_date).\
                astimezone(pytz.utc)


BlockFormSet = modelformset_factory(
    Block,
    fields=(
        'booking_open', 'individual_booking_date'
    ),
    form=BlockBaseForm,
    extra=0,
)


class BlockAdminForm(forms.ModelForm):

    required_css_class = 'form-error'

    item_cost = forms.DecimalField(
        widget=forms.TextInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'aria-describedby': 'sizing-addon2',
        }),
        help_text="The (discounted) cost of each individual class when booked "
                  "as part of the block"
    )

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': "form-control",
                'placeholder': 'Name of block e.g. "Splits Block - October"'
            }
        )
    )

    individual_booking_date = forms.CharField(
        widget=(
            forms.DateInput(
                attrs={
                    'class': "form-control datepicker",
                },
                format='%d %b %Y'
            )
        ),
        initial=timezone.now().strftime('%d %b %Y')
    )

    booking_open = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                'class': "form-control regular-checkbox",
                'id': 'booking_open_id',
                }
            ),
        help_text=mark_safe(
            "Controls whether the block is visible on the site and can be "
            "booked.</br>If this box is checked, all classes in the block "
            "will automatically be opened.  Single class booking will only be "
            "available from the date you have selected.  Note that unchecking "
            "the box does NOT close booking for individual classes."
        ),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(BlockAdminForm, self).__init__(*args, **kwargs)

        event_choices = [(event.id, event) for event in
             Event.objects.filter(date__gt=timezone.now())]

        if self.instance.id and self.instance.events.exists():
            past_events = [
                event for event in self.instance.events.all().order_by('-date')
                if event.date <= timezone.now()
                ]
            for event in past_events:
                event_choices.insert(0, (event.id, event))

        self.fields['events'] = forms.MultipleChoiceField(
            label="Select classes",
            widget=forms.CheckboxSelectMultiple,
            choices=event_choices,
        )

    def clean_individual_booking_date(self):

        raw_date = self.cleaned_data['individual_booking_date']
        if raw_date:
            if self.errors.get('individual_booking_date'):
                del self.errors['individual_booking_date']
            if self.instance:
                original_date = self.instance.individual_booking_date
                original_date_fmt = original_date.strftime('%d %b %Y')
                if original_date_fmt == raw_date \
                        and 'individual_booking_date' in self.changed_data:
                    self.changed_data.remove('individual_booking_date')
            try:
                # we need to give the date an hour otherwise it will be set to
                # 0 and incorrectly changed to the previous day when we
                # localise for the uk; time will be set back to 0 when the
                # model saves
                individual_booking_date = datetime.strptime(
                    raw_date, '%d %b %Y'
                ).replace(hour=12)
            except ValueError:
                self.add_error(
                    'individual_booking_date',
                    'Invalid date format.  Select from the date picker or '
                    'enter date and time in the format dd Mmm YYYY HH:MM')

            uk = pytz.timezone('Europe/London')
            return uk.localize(individual_booking_date).\
                astimezone(pytz.utc)

    class Meta:
        model = Block
        fields = (
            'name', 'item_cost', 'events', 'booking_open',
            'individual_booking_date'
        )
        widgets = {
            'name': forms.TextInput(
                attrs={'class': "form-control"}
            ),
        }


class RegisterDayForm(forms.Form):

    def __init__(self, *args, **kwargs):
        if 'events' in kwargs:
            self.events = kwargs.pop('events')
        else:
            self.events = None
        super(RegisterDayForm, self).__init__(*args, **kwargs)

        self.fields['register_date'] = forms.DateField(
            label="Date",
            widget=forms.DateInput(
                attrs={
                    'class': "form-control",
                    'id': 'datepicker_registerdate',
                    'onchange': "this.form.submit()"},
                format='%a %d %b %Y'
            ),
            required=True,
            initial=date.today()
        )

        self.fields['register_format'] = forms.ChoiceField(
            label="Register format",
            choices=[('full', 'Full register'), ('namesonly', 'Names only')],
            widget=forms.RadioSelect,
            initial='full',
            required=False
        )

        if self.events:
            initial = [event.id for event in self.events]
            event_choices = tuple([(event.id, event) for event in self.events])
            self.fields['select_events'] = forms.MultipleChoiceField(
                label="Select registers to print:",
                widget=forms.CheckboxSelectMultiple,
                choices=event_choices,
                initial=initial
            )
        else:
            self.fields['no_events'] = forms.CharField(
                label="",
                widget=forms.TextInput(
                    attrs={
                           'placeholder': "No classes/workshops on this date",
                           'style': 'width: 200px; border: none; '
                                    'background-color: transparent;',
                           'class': 'disabled studioadmin-help'
                    }
                ),
                required=False
            )

    def clean(self):
        super(RegisterDayForm, self).clean()
        cleaned_data = self.cleaned_data

        if self.data.get('select_events'):
            selected_events = self.data.getlist('select_events')
            if selected_events:
                cleaned_data['select_events'] = [int(ev) for ev in selected_events]

        register_date = self.data.get('register_date')
        if register_date:
            if self.errors.get('register_date'):
                del self.errors['register_date']
            try:
                register_date = datetime.strptime(register_date, '%a %d %b %Y').date()
                cleaned_data['register_date'] = register_date
            except ValueError:
                self.add_error(
                    'register_date', 'Invalid date format.  Select from '
                                        'the date picker or enter date in the '
                                        'format e.g. Mon 08 Jun 2015')

        return cleaned_data



#
# class StatusFilter(forms.Form):
#
#     status_choice = forms.ChoiceField(
#         widget=forms.Select,
#         choices=(('OPEN', 'Open bookings only'),
#                  ('CANCELLED', 'Cancelled Bookings only'),
#                  ('ALL', 'All'),),
#     )
#

class BookingStatusFilter(forms.Form):

    booking_status = forms.ChoiceField(
        widget=forms.Select,
        choices=(
            ('future', 'Upcoming bookings'),
            ('past', 'Past bookings'),
            ('all', 'All bookings'),
        ),
    )


class ConfirmPaymentForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('paid', 'payment_confirmed')
        widgets = {
            'paid': forms.CheckboxInput(),
            'payment_confirmed': forms.CheckboxInput()
        }


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
                                      '"Flexibility for splits'},
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
            'advance_payment_required': _('If this checkbox is not ticked, '
                                          'unpaid bookings will remain '
                                          'active after the cancellation period '
                                          'and will not be '
                                          'automatically cancelled')
        }


class UploadTimetableForm(forms.Form):
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

    sessions = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        label="Choose sessions to upload",
        choices=[(session.id, session) for session in Session.objects.all()],
        initial=[session.id for session in Session.objects.all()],
        required=True
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


class UserBlockForm(forms.Form):

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control input-sm'}),
    )


class UserBlockBaseFormset(BaseFormSet):

    def add_fields(self, form, index):
        super(UserBlockBaseFormset, self).add_fields(form, index)

        if form.initial:
            form.user_instance = User.objects.get(id=form.initial['user'])
            form.block_instance = Block.objects.get(id=form.initial['block'])

            form.block_status = 'CANCELLED'
            for booking in Booking.objects.filter(
                    block=form.block_instance, user=form.user_instance):
                if booking.status == 'OPEN':
                    form.block_status = 'OPEN'

            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': 'delete-checkbox studioadmin-list',
                    'id': 'DELETE_{}'.format(index)
                }),
                required=False
            )
            form.DELETE_id = 'DELETE_{}'.format(index)

            form.fields['block'] = forms.ModelChoiceField(
                queryset=Block.objects.all()
            )

        else:
            bookable_blocks = [
                block.id for block in Block.objects.all() if (not block.is_past and
                block.booking_open and not
                block.has_full_class and not
                block.has_started)
            ]

            form.fields['block'] = forms.ModelChoiceField(
                queryset=Block.objects.filter(id__in=bookable_blocks),
                widget=forms.Select(attrs={'class': 'form-control input-sm'}),
            )

        form.fields['send_confirmation'] = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={
                'class': "regular-checkbox",
                'id': 'send_confirmation_{}'.format(index)
            }),
            initial=False,
            required=False
        )
        form.send_confirmation_id = 'send_confirmation_{}'.format(index)

    def clean(self):
        for form in self.forms:
            if not form.initial and form.cleaned_data:
                user = form.cleaned_data['user']
                block = form.cleaned_data['block']

                bookable_blocks = [
                    block for block in Block.objects.all() if not block.is_past and
                    block.booking_open and not
                    block.has_full_class and not
                    block.has_started
                    ]
                # add errors if:
                # - user already has bookings for this block
                # - block is not bookable

                if block not in bookable_blocks:
                    # no need to be too descriptive since block drop down is
                    # already filtered so should be unlikely to get there
                    form.add_error('block', 'not bookable')
                user_booked_events = [
                    booking.id for booking in user.bookings.all()
                    if booking.event in block.events.all()
                    ]
                if user_booked_events:
                    form.add_error('block', 'user {} already has at least one '
                                            'booking for a class in '
                                            'block "{}"'.format(
                        user.username, block.name
                    ))

UserBlockFormSet = formset_factory(
    form=UserBlockForm,
    formset=UserBlockBaseFormset,
    extra=1,
    can_delete=True,
)

# class ChooseUsersBaseFormSet(BaseModelFormSet):
#
#     def add_fields(self, form, index):
#         super(ChooseUsersBaseFormSet, self).add_fields(form, index)
#
#         form.fields['email_user'] = forms.BooleanField(
#             widget=forms.CheckboxInput(attrs={
#                 'class': "regular-checkbox studioadmin-list select-checkbox",
#                 'id': 'email_user_cbox_{}'.format(index)
#             }),
#             initial=True,
#             required=False
#         )
#         form.email_user_cbox_id = 'email_user_cbox_{}'.format(index)
#
# ChooseUsersFormSet = modelformset_factory(
#     User,
#     fields=('id',),
#     formset=ChooseUsersBaseFormSet,
#     extra=0,
#     can_delete=False)
#
#
# class EmailUsersForm(forms.Form):
#     subject = forms.CharField(max_length=255, required=True,
#                               widget=forms.TextInput(
#                                   attrs={'class': 'form-control'}))
#     from_address = forms.EmailField(max_length=255,
#                                     initial=settings.DEFAULT_FROM_EMAIL,
#                                     required=True,
#                                     widget=forms.TextInput(
#                                         attrs={'class': 'form-control'}))
#     cc = forms.BooleanField(
#         widget=forms.CheckboxInput(attrs={
#                 'class': "regular-checkbox studioadmin-list",
#                 'id': 'cc_id'
#             }),
#         label="cc. from address",
#         initial=True,
#         required=False
#     )
#     message = forms.CharField(
#         widget=forms.Textarea(attrs={'class': 'form-control email-message',
#                                      'rows': 10}),
#         required=True)
#
#
# def get_event_names(event_type):
#
#     def callable():
#         EVENT_CHOICES = [(event.id, str(event)) for event in Event.objects.filter(
#             event_type__event_type=event_type, date__gte=timezone.now()
#         ).order_by('date')]
#         EVENT_CHOICES.insert(0, ('', '--None selected--'))
#         return tuple(EVENT_CHOICES)
#
#     return callable
#
#
# class UserFilterForm(forms.Form):
#
#     events = forms.MultipleChoiceField(
#         choices=get_event_names('EV'),
#         widget=forms.SelectMultiple(
#             attrs={'class': 'form-control'}
#         ),
#     )
#
#     lessons = forms.MultipleChoiceField(
#         choices=get_event_names('CL'),
#         widget=forms.SelectMultiple(
#             attrs={'class': 'form-control'}
#         ),
#     )
#
#

class UserBookingInlineFormSet(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserBookingInlineFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = True

    def add_fields(self, form, index):
        super(UserBookingInlineFormSet, self).add_fields(form, index)

        if form.instance.id:
            ppbs = PaypalBookingTransaction.objects.filter(
                booking_id=form.instance.id
            )
            ppbs_paypal =[True for ppb in ppbs if ppb.transaction_id]
            form.paypal = True if ppbs_paypal else False

            cancelled_class = 'expired' if \
                form.instance.status == 'CANCELLED' else 'none'

        if form.instance.id is None:
            already_booked = [
                booking.event.id for booking
                in Booking.objects.filter(user=self.user)
            ]

            form.fields['event'] = forms.ModelChoiceField(
                queryset=Event.objects.filter(
                    date__gte=timezone.now()
                ).filter(booking_open=True).exclude(
                    id__in=already_booked).order_by('date'),
                widget=forms.Select(attrs={'class': 'form-control input-sm'}),
            )
        else:
            form.fields['event'] = (forms.ModelChoiceField(
                queryset=Event.objects.all(),
            ))

        form.fields['paid'] = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={
                'class': "regular-checkbox",
                'id': 'paid_{}'.format(index)
            }),
            required=False
        )
        form.fields['send_confirmation'] = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={
                'class': "regular-checkbox",
                'id': 'send_confirmation_{}'.format(index)
            }),
            initial=False,
            required=False
        )
        form.send_confirmation_id = 'send_confirmation_{}'.format(index)
        form.fields['status'] = forms.ChoiceField(
            choices=(('OPEN', 'OPEN'), ('CANCELLED', 'CANCELLED')),
            widget=forms.Select(attrs={'class': 'form-control input-sm'}),
            initial='OPEN'
        )
        form.paid_id = 'paid_{}'.format(index)

    def clean(self):

        super(UserBookingInlineFormSet, self).clean()
        if {
            '__all__': ['Booking with this User and Event already exists.']
        } in self.errors:
            pass
        elif any(self.errors):
            return


UserBookingFormSet = inlineformset_factory(
    User,
    Booking,
    fields=('paid', 'event', 'status'),
    can_delete=False,
    formset=UserBookingInlineFormSet,
    extra=1,
)


class ActivityLogSearchForm(forms.Form):
    search = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Search log text'
            }
        )
    )
    search_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'id': "logdatepicker",
                'placeholder': "Search by log date",
                'style': 'text-align: center'
            },
            format='%d-%m-%y',
        ),
    )
    hide_empty_cronjobs = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': "regular-checkbox",
            'id': 'hide_empty_cronjobs_id'
        }),
        initial='on'
    )


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = ('name', 'menu_name', 'menu_location', 'layout', 'heading')
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),
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
            )
        }

class SubsectionBaseFormset(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super(SubsectionBaseFormset, self).__init__(*args, **kwargs)
        self.empty_permitted = True

    def add_fields(self, form, index):
        super(SubsectionBaseFormset, self).add_fields(form, index)

        if form.instance.id:

            form.fields['DELETE'] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={
                    'class': 'delete-checkbox studioadmin-list',
                    'id': 'DELETE_{}'.format(index)
                }),
                help_text="Tick box and click Save to delete this subsection",
                required=False
            )
            form.DELETE_id = 'DELETE_{}'.format(index)

        form.fields['content'] = forms.CharField(
            widget=forms.Textarea(
                attrs={'class': 'form-control'}
            ),
            required=True
        )

        form.fields['subheading'] = forms.CharField(
            widget=forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            required=False
        )

        form.fields['index'] = forms.IntegerField(
            widget=forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            help_text="Use this to change the order subsections "
                      "are displayed on the page",
            required=True
        )

SubsectionFormset = inlineformset_factory(
    Page,
    SubSection,
    fields=('subheading', 'content', 'index'),
    formset=SubsectionBaseFormset,
    can_delete=True,
    extra=1,
)

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
            label=_(''),
            error_messages={'invalid':_("Image files only")},
            widget=ImageThumbnailFileInput,
            required=False
        )

    def clean(self):
        super(PictureBaseFormset, self).clean()

        main_pics = [
            form.instance for form in self.forms if form.instance.main == True
        ]
        if len(main_pics) != 1:
            self.errors.append({'main image': 'Please select a single "main" image '
                                              'to be displayed in single '
                                              'image layouts'})
            raise forms.ValidationError('Only one "main" image can be selected')

PictureFormset = inlineformset_factory(
    Page,
    Picture,
    fields=('image', 'main'),
    formset=PictureBaseFormset,
    can_delete=True,
    extra=1,
)