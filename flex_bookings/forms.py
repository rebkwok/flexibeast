from datetime import date
from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


from flex_bookings.models import Booking, Event


def get_event_names(event_type):

    def callable():
        event_names = set([event.name for event in Event.objects.filter(
            event_type__event_type=event_type, date__gte=timezone.now()
        ).order_by('name')])
        NAME_CHOICES = [(item, item) for i, item in enumerate(event_names)]
        NAME_CHOICES.insert(0, ('', 'All'))
        return tuple(sorted(NAME_CHOICES))

    return callable


class EventFilter(forms.Form):
    name = forms.ChoiceField(
        choices=get_event_names('EV'),
        widget=forms.Select(attrs={
            "onchange": "form.submit()"
        })
    )

class LessonFilter(forms.Form):
    name = forms.ChoiceField(
        choices=get_event_names('CL'),
        widget=forms.Select(attrs={
            "onchange": "form.submit()"
        })
    )


class BookingCreateForm(forms.ModelForm):

    class Meta:
        model = Booking
        fields = ['event', ]