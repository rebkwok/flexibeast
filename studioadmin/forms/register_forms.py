# -*- coding: utf-8 -*-

from datetime import datetime, date

from django import forms


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
