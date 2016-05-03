import pytz
from datetime import datetime

from django import forms
from django.forms.models import modelformset_factory, BaseModelFormSet, \
    inlineformset_factory, formset_factory, BaseFormSet, BaseInlineFormSet
from django.utils import timezone
from django.utils.safestring import mark_safe


from flex_bookings.models import Block, Booking, Event


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

            block_users = set([booking.user for booking in bookings])
            self.booked_user_count = len(block_users)

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

        if self.instance.id and self.instance.events.exists():
            past_events = [
                event for event in self.instance.events.all().order_by('-date')
                if event.date <= timezone.now()
                ]
            for event in past_events:
                event_choices.insert(0, (event.id, event))

        self.fields['events'] = forms.ModelMultipleChoiceField(
            label="Select classes",
            widget=forms.CheckboxSelectMultiple,
            queryset=Event.objects.filter(date__gt=timezone.now()),
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
