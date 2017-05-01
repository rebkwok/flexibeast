# -*- coding: utf-8 -*-

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.forms.models import modelformset_factory, BaseModelFormSet, \
    inlineformset_factory, formset_factory, BaseFormSet, BaseInlineFormSet
from django.utils import timezone

# from flex_bookings.models import Block, Booking, Event
# from payments.models import PaypalBookingTransaction
#
#
# class BookingStatusFilter(forms.Form):
#
#     booking_status = forms.ChoiceField(
#         widget=forms.Select,
#         choices=(
#             ('future', 'Upcoming bookings'),
#             ('past', 'Past bookings'),
#             ('all', 'All bookings'),
#         ),
#     )
#
#
# class UserBlockForm(forms.Form):
#
#     user = forms.ModelChoiceField(
#         queryset=User.objects.all(),
#         widget=forms.Select(attrs={'class': 'form-control input-sm'}),
#     )
#
#
# class UserBlockBaseFormset(BaseFormSet):
#
#     def add_fields(self, form, index):
#         super(UserBlockBaseFormset, self).add_fields(form, index)
#         if form.initial:
#             form.user_instance = User.objects.get(id=form.initial['user'])
#             form.block_instance = Block.objects.get(id=form.initial['block'])
#
#             form.block_status = 'CANCELLED'
#             for booking in Booking.objects.filter(
#                     block=form.block_instance, user=form.user_instance):
#
#                 if booking.status == 'OPEN':
#                     form.block_status = 'OPEN'
#
#             form.fields['DELETE'] = forms.BooleanField(
#                 widget=forms.CheckboxInput(attrs={
#                     'class': 'delete-checkbox studioadmin-list',
#                     'id': 'DELETE_{}'.format(index)
#                 }),
#                 required=False
#             )
#             form.DELETE_id = 'DELETE_{}'.format(index)
#
#             form.fields['block'] = forms.ModelChoiceField(
#                 queryset=Block.objects.all()
#             )
#
#         else:
#             bookable_blocks = [
#                 block.id for block in Block.objects.all() if (
#                     not block.is_past and
#                     block.events.exists() and
#                     block.booking_open and
#                     not block.has_full_class and
#                     not block.has_started
#                 )
#             ]
#
#             form.fields['block'] = forms.ModelChoiceField(
#                 queryset=Block.objects.filter(id__in=bookable_blocks),
#                 widget=forms.Select(attrs={'class': 'form-control input-sm'}),
#             )
#
#         form.fields['send_confirmation'] = forms.BooleanField(
#             widget=forms.CheckboxInput(attrs={
#                 'class': "regular-checkbox",
#                 'id': 'send_confirmation_{}'.format(index)
#             }),
#             initial=False,
#             required=False
#         )
#         form.send_confirmation_id = 'send_confirmation_{}'.format(index)
#
#     def clean(self):
#         for form in self.forms:
#             if not form.initial and form.cleaned_data:
#                 user = form.cleaned_data['user']
#                 block = form.cleaned_data['block']
#
#                 bookable_blocks = [
#                     block for block in Block.objects.all() if not block.is_past and
#                     block.booking_open and not
#                     block.has_full_class and not
#                     block.has_started
#                     ]
#                 # add errors if:
#                 # - user already has bookings for this block
#                 # - block is not bookable
#
#                 if block not in bookable_blocks:
#                     # no need to be too descriptive since block drop down is
#                     # already filtered so should be unlikely to get there
#                     form.add_error('block', 'not bookable')
#                 user_booked_events = [
#                     booking.id for booking in user.bookings.all()
#                     if booking.event in block.events.all()
#                     ]
#                 if user_booked_events:
#                     form.add_error('block', 'user {} already has at least one '
#                                             'booking for a class in '
#                                             'block "{}"'.format(
#                         user.username, block.name
#                     ))
#
# UserBlockFormSet = formset_factory(
#     form=UserBlockForm,
#     formset=UserBlockBaseFormset,
#     extra=1,
#     can_delete=True,
# )
#
#
# class UserBookingInlineFormSet(BaseInlineFormSet):
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super(UserBookingInlineFormSet, self).__init__(*args, **kwargs)
#         for form in self.forms:
#             form.empty_permitted = True
#
#     def add_fields(self, form, index):
#         super(UserBookingInlineFormSet, self).add_fields(form, index)
#
#         if form.instance.id:
#             ppbs = PaypalBookingTransaction.objects.filter(
#                 booking_id=form.instance.id
#             )
#             ppbs_paypal =[True for ppb in ppbs if ppb.transaction_id]
#             form.paypal = True if ppbs_paypal else False
#
#             cancelled_class = 'expired' if \
#                 form.instance.status == 'CANCELLED' else 'none'
#
#         if form.instance.id is None:
#             already_booked = [
#                 booking.event.id for booking
#                 in Booking.objects.filter(user=self.user)
#             ]
#
#             form.fields['event'] = forms.ModelChoiceField(
#                 queryset=Event.objects.filter(
#                     date__gte=timezone.now()
#                 ).filter(booking_open=True).exclude(
#                     id__in=already_booked).order_by('date'),
#                 widget=forms.Select(attrs={'class': 'form-control input-sm'}),
#             )
#         else:
#             form.fields['event'] = (forms.ModelChoiceField(
#                 queryset=Event.objects.all(),
#             ))
#
#         form.fields['paid'] = forms.BooleanField(
#             widget=forms.CheckboxInput(attrs={
#                 'class': "regular-checkbox",
#                 'id': 'paid_{}'.format(index)
#             }),
#             required=False
#         )
#         form.fields['send_confirmation'] = forms.BooleanField(
#             widget=forms.CheckboxInput(attrs={
#                 'class': "regular-checkbox",
#                 'id': 'send_confirmation_{}'.format(index)
#             }),
#             initial=False,
#             required=False
#         )
#         form.send_confirmation_id = 'send_confirmation_{}'.format(index)
#         form.fields['status'] = forms.ChoiceField(
#             choices=(('OPEN', 'OPEN'), ('CANCELLED', 'CANCELLED')),
#             widget=forms.Select(attrs={'class': 'form-control input-sm'}),
#             initial='OPEN'
#         )
#         form.paid_id = 'paid_{}'.format(index)
#
#     def clean(self):
#
#         super(UserBookingInlineFormSet, self).clean()
#         if {
#             '__all__': ['Booking with this User and Event already exists.']
#         } in self.errors:
#             pass
#         elif any(self.errors):
#             return
#
#
# UserBookingFormSet = inlineformset_factory(
#     User,
#     Booking,
#     fields=('paid', 'event', 'status'),
#     can_delete=False,
#     formset=UserBookingInlineFormSet,
#     extra=1,
# )


class ChooseUsersBaseFormSet(BaseModelFormSet):

    def add_fields(self, form, index):
        super(ChooseUsersBaseFormSet, self).add_fields(form, index)

        form.fields['email_user'] = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={
                'class': "regular-checkbox studioadmin-list select-checkbox",
                'id': 'email_user_cbox_{}'.format(index)
            }),
            initial=True,
            required=False
        )
        form.email_user_cbox_id = 'email_user_cbox_{}'.format(index)

ChooseUsersFormSet = modelformset_factory(
    User,
    fields=('id',),
    formset=ChooseUsersBaseFormSet,
    extra=0,
    can_delete=False)


class EmailUsersForm(forms.Form):
    subject = forms.CharField(max_length=255, required=True,
                              widget=forms.TextInput(
                                  attrs={'class': 'form-control'}))
    from_address = forms.EmailField(max_length=255,
                                    initial=settings.DEFAULT_STUDIO_EMAIL,
                                    required=True,
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control'}),
                                    help_text='This will be the reply-to address')
    cc = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
                'class': "regular-checkbox studioadmin-list",
                'id': 'cc_id'
            }),
        label="cc. from address",
        initial=True,
        required=False
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control email-message',
                                     'rows': 10}),
        required=True)