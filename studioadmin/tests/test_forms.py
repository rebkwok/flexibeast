from datetime import datetime, timedelta
from mock import patch
from model_mommy import mommy

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from flex_bookings.models import Event, EventType, Block
from studioadmin.forms import (
    # ChooseUsersFormSet,
    DAY_CHOICES,
    # EmailUsersForm,
    EventFormSet,
    EventAdminForm,
    PageForm,
    PagesFormset,
    PictureFormset,
    TimetableSessionFormSet,
    SessionAdminForm,
    SubsectionFormset,
    UploadTimetableForm,
    # UserFilterForm,
    UserBookingFormSet,
    UserBlockFormSet
)
from timetable.models import Session
from website.models import Page, SubSection, Picture

class EventFormSetTests(TestCase):

    def setUp(self):
        self.event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True
        )
        self.event1 = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True
        )
        mommy.make_recipe('flex_bookings.booking', event=self.event1)

    def formset_data(self, extra_data={}):

        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': str(self.event.id),
            'form-0-max-participants': '10',
            'form-0-booking_open': 'on',
            'form-0-advance_payment_required': 'on',
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_event_formset_valid(self):
        formset = EventFormSet(data=self.formset_data())
        self.assertTrue(formset.is_valid())

    def test_event_formset_delete(self):
        extra_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-DELETE': 'on',
            'form-1-id': self.event1.id,
            'form-1-cost': '7',
            'form-1-max-participants': '10',
            'form-1-booking_open': 'on',
            }
        formset = EventFormSet(data=self.formset_data(extra_data))
        self.assertEqual(len(formset.deleted_forms), 1)
        deleted_form = formset.deleted_forms[0]
        self.assertEqual(deleted_form.cleaned_data['id'], self.event)

    def test_event_formset_delete_with_bookings(self):
        """
        Test delete widget is disabled if bookings made against event
        """
        extra_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-DELETE': 'on',
            'form-1-id': str(self.event1.id),
            'form-1-cost': '7',
            'form-1-max-participants': '10',
            'form-1-booking_open': 'on',
            'form-1-DELETE': 'on',
            }
        formset = EventFormSet(data=self.formset_data(extra_data))
        deleted_form_no_bookings = formset.deleted_forms[0]
        deleted_form_with_bookings = formset.deleted_forms[1]
        self.assertEqual(deleted_form_no_bookings.cleaned_data['id'], self.event)
        self.assertEqual(deleted_form_with_bookings.cleaned_data['id'], self.event1)

        delete_no_bookings_widget = deleted_form_no_bookings.fields['DELETE'].widget
        delete_with_bookings_widget = deleted_form_with_bookings.fields['DELETE'].widget
        self.assertEqual(
            delete_no_bookings_widget.attrs['class'],
            'delete-checkbox studioadmin-list'
        )
        self.assertEqual(
            delete_with_bookings_widget.attrs['class'],
            'delete-checkbox-disabled studioadmin-list'
        )


class EventAdminFormTests(TestCase):

    def setUp(self):
        self.event_type = mommy.make_recipe('flex_bookings.event_type_YC')
        self.event_type_ev = mommy.make_recipe('flex_bookings.event_type_WS')

    def form_data(self, extra_data={}):
        data = {
            'name': 'test_event',
            'event_type': self.event_type.id,
            'date': '15 Jun 2015 18:00',
            'contact_email': 'test@test.com',
            'contact_person': 'test',
            'cancellation_period': 24,
            'location': 'Watermelon Studio'
        }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_form_valid(self):

        form = EventAdminForm(data=self.form_data(), ev_type='CL')
        self.assertTrue(form.is_valid())

    def test_form_with_invalid_contact_person(self):
        form = EventAdminForm(
            data=self.form_data({'contact_person': ''}), ev_type='CL')
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('contact_person', form.errors.keys())
        self.assertIn(['This field is required.'], form.errors.values())

    def test_form_with_invalid_contact_email(self):
        form = EventAdminForm(
            data=self.form_data({'contact_email': ''}), ev_type='CL')
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('contact_email', form.errors.keys())
        self.assertIn(['This field is required.'], form.errors.values())

        form = EventAdminForm(
            data=self.form_data({'contact_email': 'test_email'}), ev_type='CL')
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('contact_email', form.errors.keys())
        self.assertIn(['Enter a valid email address.'], form.errors.values())

    def test_event_type_queryset(self):
        form = EventAdminForm(
            data=self.form_data(), ev_type='EV')
        ev_type_field = form.fields['event_type']
        self.assertEqual(
            set(EventType.objects.filter(id=self.event_type_ev.id)),
            set(ev_type_field.queryset)
        )
        self.assertEquals(len(ev_type_field.queryset), 1)

        form = EventAdminForm(
            data=self.form_data(), ev_type='CL')
        ev_type_field = form.fields['event_type']
        self.assertEqual(
            set(EventType.objects.filter(id=self.event_type.id)),
            set(ev_type_field.queryset)
        )
        self.assertEquals(len(ev_type_field.queryset), 1)

    def test_invalid_date(self):
        form = EventAdminForm(
            data=self.form_data(
                {'date': '15 Jun 2015 25:00'}), ev_type='CL')
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid date format', str(form.errors['date']))

    def test_invalid_payment_due_date(self):
        form = EventAdminForm(
            data=self.form_data(
                {'payment_due_date': '31 Jun 2015'}), ev_type='CL')
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid date format', str(form.errors['payment_due_date']))

    def test_payment_due_date_after_cancellation_period(self):
        form = EventAdminForm(
            data=self.form_data(
                {'date': '15 Jun 2015 20:00',
                 'payment_due_date': '16 Jun 2015'},
            ), ev_type='CL')
        self.assertFalse(form.is_valid())
        self.assertIn('Payment due date must be before cancellation period '
                      'starts', str(form.errors['payment_due_date']))

    def test_valid_payment_due_date(self):
        form = EventAdminForm(
            data=self.form_data(
                {'date': '15 Jun 2015 20:00',
                 'payment_due_date': '10 Jun 2015'},
            ), ev_type='CL')
        self.assertTrue(form.is_valid())

    def test_name_placeholder(self):
        form = EventAdminForm(data=self.form_data(), ev_type='EV')
        name_field = form.fields['name']
        self.assertEquals(
            name_field.widget.attrs['placeholder'],
            'Name of event e.g. Splits Workshop')

        form = EventAdminForm(data=self.form_data(), ev_type='CL')
        name_field = form.fields['name']
        self.assertEquals(
            name_field.widget.attrs['placeholder'],
            'Name of class e.g. Flexibility for Splits')


class TimetableSessionFormSetTests(TestCase):

    def setUp(self):
        self.session = mommy.make(Session)

    def formset_data(self, extra_data={}):

        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': str(self.session.id),
            'form-0-cost': '7',
            'form-0-max-participants': '10',
            'form-0-booking_open': 'on',
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_event_formset_valid(self):
        formset = TimetableSessionFormSet(data=self.formset_data())
        self.assertTrue(formset.is_valid())

    def test_additional_form_data(self):
        formset = TimetableSessionFormSet(
            data=self.formset_data(), queryset=Session.objects.all())
        form =formset.forms[0]
        self.assertEquals(form.formatted_day, DAY_CHOICES[self.session.day])
        self.assertEquals(form.booking_open_id, 'booking_open_0')

    def test_can_delete(self):
        session_to_delete = mommy.make(Session)
        extra_data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-1-DELETE': 'on',
            'form-1-id': session_to_delete.id,
            'form-1-cost': '7',
            'form-1-max-participants': '10',
            'form-1-booking_open': 'on',
            }
        formset = TimetableSessionFormSet(data=self.formset_data(extra_data),
                               queryset=Session.objects.all())
        self.assertEqual(len(formset.deleted_forms), 1)
        deleted_form = formset.deleted_forms[0]
        self.assertEqual(deleted_form.cleaned_data['id'], session_to_delete)


class SessionAdminFormTests(TestCase):

    def setUp(self):
        self.event_type = mommy.make_recipe('flex_bookings.event_type_YC')
        self.event_type_ev = mommy.make_recipe('flex_bookings.event_type_WS')
        self.event_type_yc = mommy.make_recipe('flex_bookings.event_type_YC')

    def form_data(self, extra_data={}):
        data = {
            'name': 'test_event',
            'event_type': self.event_type.id,
            'day': '01MON',
            'time': '12:00',
            'contact_email': 'test@test.com',
            'contact_person': 'test',
            'cancellation_period': 24,
            'location': 'Watermelon Studio'
        }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_form_valid(self):

        form = SessionAdminForm(data=self.form_data())
        self.assertTrue(form.is_valid())

    def test_form_with_invalid_contact_person(self):
        form = SessionAdminForm(
            data=self.form_data({'contact_person': ''}))
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('contact_person', form.errors.keys())
        self.assertIn(['This field is required.'], form.errors.values())

    def test_form_with_invalid_contact_email(self):
        form = SessionAdminForm(
            data=self.form_data({'contact_email': ''}))
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('contact_email', form.errors.keys())
        self.assertIn(['This field is required.'], form.errors.values())

        form = SessionAdminForm(
            data=self.form_data({'contact_email': 'test_email'}))
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('contact_email', form.errors.keys())
        self.assertIn(['Enter a valid email address.'], form.errors.values())

    def test_event_type_queryset(self):
        form = SessionAdminForm(
            data=self.form_data())
        ev_type_field = form.fields['event_type']
        self.assertEqual(
            set(EventType.objects.filter(event_type='CL')),
            set(ev_type_field.queryset)
        )
        self.assertEquals(len(ev_type_field.queryset), 2)

        form = SessionAdminForm(
            data=self.form_data())
        ev_type_field = form.fields['event_type']
        self.assertEqual(
            set(EventType.objects.filter(
                id__in=[self.event_type.id, self.event_type_yc.id]
            )),
            set(ev_type_field.queryset)
        )
        self.assertEquals(len(ev_type_field.queryset), 2)

    def test_invalid_time(self):
        form = SessionAdminForm(
            data=self.form_data(
                {'time': '25:00'}))
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid time format', str(form.errors['time']))

    def test_name_placeholder(self):
        form = SessionAdminForm(data=self.form_data())
        name_field = form.fields['name']
        self.assertEquals(
            name_field.widget.attrs['placeholder'],
            'Name of session e.g. Flexibility for Splits')


class UploadTimetableFormTests(TestCase):

    def setUp(self):

        self.session = mommy.make_recipe('flex_bookings.mon_session')

    def form_data(self, extra_data={}):
        data = {
            'start_date': 'Mon 08 Jun 2015',
            'end_date': 'Mon 15 Jun 2015',
            'sessions': [self.session.id]
        }

        for key, value in extra_data.items():
            data[key] = value

        return data

    @patch('studioadmin.forms.timezone')
    def test_form_valid(self, mock_tz):
        mock_tz.now.return_value = datetime(
            2015, 6, 6, 12, 0, tzinfo=timezone.utc
            )
        form = UploadTimetableForm(data=self.form_data())

        self.assertTrue(form.is_valid())

    @patch('studioadmin.forms.timezone')
    def test_start_and_end_date_required(self, mock_tz):
        mock_tz.now.return_value = datetime(
            2015, 6, 6, 12, 0, tzinfo=timezone.utc
            )
        form = UploadTimetableForm(
            data={'sessions': [self.session.id]}
        )
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 2)
        self.assertEquals(
            form.errors.get('start_date'), ['This field is required.']
        )
        self.assertEquals(
            form.errors.get('end_date'), ['This field is required.']
        )

    @patch('studioadmin.forms.timezone')
    def test_invalid_start_date_format(self, mock_tz):
        mock_tz.now.return_value = datetime(
            2015, 6, 6, 12, 0, tzinfo=timezone.utc
            )
        form = UploadTimetableForm(
            data=self.form_data({'start_date': 'Monday 08 June 2015'})
        )
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('Invalid date format', str(form.errors['start_date']))

    @patch('studioadmin.forms.timezone')
    def test_start_date_in_past(self, mock_tz):
        mock_tz.now.return_value = datetime(
            2015, 6, 6, 12, 0, tzinfo=timezone.utc
            )
        form = UploadTimetableForm(
            data=self.form_data({'start_date': 'Mon 08 Jun 2000'})
        )
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('Must be in the future', str(form.errors['start_date']))

    @patch('studioadmin.forms.timezone')
    def test_invalid_end_date_format(self, mock_tz):
        mock_tz.now.return_value = datetime(
            2015, 6, 6, 12, 0, tzinfo=timezone.utc
            )
        form = UploadTimetableForm(
            data=self.form_data({'end_date': 'Monday 15 June 2015'})
        )
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('Invalid date format', str(form.errors['end_date']))

    @patch('studioadmin.forms.timezone')
    def test_end_date_before_start_date(self, mock_tz):
        mock_tz.now.return_value = datetime(
            2015, 6, 6, 12, 0, tzinfo=timezone.utc
            )
        form = UploadTimetableForm(
            data=self.form_data({
                'start_date': 'Tue 16 Jun 2015',
                'end_date': 'Mon 15 Jun 2015'
            })
        )
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertEquals(
            form.errors['end_date'],
            ['Cannot be before start date']
        )


# class ChooseUsersFormSetTests(TestCase):
#
#     def setUp(self):
#         self.user = mommy.make_recipe('flex_bookings.user')
#
#     def formset_data(self, extra_data={}):
#
#         data = {
#             'form-TOTAL_FORMS': 1,
#             'form-INITIAL_FORMS': 1,
#             'form-0-id': str(self.user.id),
#             }
#
#         for key, value in extra_data.items():
#             data[key] = value
#
#         return data
#
#     def test_choose_users_formset_valid(self):
#         formset = ChooseUsersFormSet(data=self.formset_data())
#         self.assertTrue(formset.is_valid())
#
#
# class EmailUsersFormTests(TestCase):
#
#     def setUp(self):
#         pass
#
#     def form_data(self, extra_data={}):
#         data = {
#             'subject': 'Test subject',
#             'from_address': settings.DEFAULT_FROM_EMAIL,
#             'message': 'Test message'
#         }
#
#         for key, value in extra_data.items():
#             data[key] = value
#
#         return data
#
#     def test_form_valid(self):
#         form = EmailUsersForm(data=self.form_data())
#         self.assertTrue(form.is_valid())
#
#     def test_missing_from_address(self):
#         form = EmailUsersForm(
#             data=self.form_data({'from_address': ''})
#         )
#         self.assertFalse(form.is_valid())
#         self.assertEquals(
#             form.errors['from_address'],
#             ['This field is required.']
#         )
#
#     def test_missing_message(self):
#         form = EmailUsersForm(
#             data=self.form_data({'message': ''})
#         )
#         self.assertFalse(form.is_valid())
#         self.assertEquals(
#             form.errors['message'],
#             ['This field is required.']
#         )
#
#
# class UserFilterFormTests(TestCase):
#
#     def setUp(self):
#         events = mommy.make_recipe(
#             'flex_bookings.future_EV',
#             _quantity=3
#             )
#         classes = mommy.make_recipe(
#             'flex_bookings.future_PC',
#             _quantity=4)
#
#     def test_events_dropdown(self):
#         form = UserFilterForm()
#         event_field = form.fields['events']
#         event_choices = [
#             choice for choice in event_field.widget.choices
#             ]
#         # number of choices is one more than number of events, to account
#         # for the placeholder for None Selected
#         self.assertEquals(len(event_choices), 4)
#         # first id will be ('', '---None selected---')
#         event_ids = [id for (id, name) in event_choices][1:]
#         event_type = set([
#             event.event_type.event_type
#             for event in Event.objects.filter(id__in=event_ids)
#             ])
#         self.assertEquals(event_type, set(['EV']))
#
#     def test_lessons_dropdown(self):
#         form = UserFilterForm()
#         lesson_field = form.fields['lessons']
#         lesson_choices = [
#             choice for choice in lesson_field.widget.choices
#             ]
#         # number of choices is one more than number of events, to account
#         # for the placeholder for None Selected
#         self.assertEquals(len(lesson_choices), 5)
#         # first id will be ('', '---None selected---')
#         lesson_ids = [id for (id, name) in lesson_choices][1:]
#         event_type = set([
#             event.event_type.event_type
#             for event in Event.objects.filter(id__in=lesson_ids)
#             ])
#         self.assertEquals(event_type, set(['CL']))
#
#
class UserBookingFormSetTests(TestCase):

    def setUp(self):
        self.event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True
        )
        self.user = mommy.make_recipe('flex_bookings.user')

        self.booking = mommy.make_recipe(
            'flex_bookings.booking', event=self.event, user=self.user
        )

    def formset_data(self, extra_data={}):

        data = {
            'bookings-TOTAL_FORMS': 1,
            'bookings-INITIAL_FORMS': 1,
            'bookings-0-id': self.booking.id,
            'bookings-0-event': self.event.id,
            'bookings-0-status': self.booking.status,
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_form_valid(self):
        formset = UserBookingFormSet(data=self.formset_data(),
                                     instance=self.user,
                                     user=self.user)

    def test_event_choices_with_new_form(self):
        """
        New form should show all events the user is not booked for
        """
        events = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True,  _quantity=5
        )
        formset = UserBookingFormSet(instance=self.user,
                                     user=self.user)
        # get the last form, which will be the new empty one
        form = formset.forms[-1]
        event = form.fields['event']
        self.assertEquals(6, Event.objects.count())
        self.assertEquals(5, event.queryset.count())
        self.assertFalse(self.event in event.queryset)

    def test_event_choices_with_existing_booking(self):
        """
        Existing booking should show all events in event choices
        ).
        """
        events = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True, _quantity=5
        )
        formset = UserBookingFormSet(data=self.formset_data(),
                                     instance=self.user,
                                     user=self.user)
        # get the first form
        form = formset.forms[0]
        event = form.fields['event']
        # queryset shows all events (will be hidden in the template)
        self.assertEquals(6, event.queryset.count())


class UserBlockFormSetTests(TestCase):

    def setUp(self):
        self.user = mommy.make_recipe('flex_bookings.user')
        self.block = mommy.make_recipe(
            'flex_bookings.block', booking_open=True
        )
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True
        )
        self.block.events.add(event)
        mommy.make_recipe(
            'flex_bookings.booking', block=self.block, event=event,
            user=self.user
        )
    def formset_data(self, extra_data={}):

        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-user': self.user.id,
            'form-0-block': self.block.id,
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_form_valid(self):
        formset = UserBlockFormSet(
            data=self.formset_data(),
            initial=[{'user': self.user.id, 'block': self.block.id}]
        )
        self.assertTrue(formset.is_valid(), formset.errors)

    def test_additional_data_in_form(self):
        formset = UserBlockFormSet(
            data=self.formset_data(),
            initial=[{'user': self.user.id, 'block': self.block.id}]
        )
        form = formset.forms[0]
        self.assertEqual(form.block_status, 'OPEN')
        self.assertEqual(form.user_instance, self.user)
        self.assertEqual(form.block_instance, self.block)

    def test_bookable_blocks_block_booking_open(self):
        """
        blocks appear in the choice dropdown in an empty form if they are:
         - open
         - have events
         - not past (i.e. all events in the past)
         - no event on the block is full
         - block hasn't started yet
        :return:
        """

        block = mommy.make_recipe(
            'flex_bookings.block', booking_open=False
        )
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True
        )
        block.events.add(event)

        self.assertFalse(block.booking_open)
        self.assertTrue(block.events.exists())
        self.assertFalse(block.is_past)
        self.assertFalse(block.has_full_class)
        self.assertFalse(block.has_started)

        formset = UserBlockFormSet(
            # data=self.formset_data({'form-TOTAL-FORMS': 2}),
            initial=[{'user': self.user.id, 'block': self.block.id}]
        )
        form = formset.forms[1] # get the second (empty) form
        block_qset = form.fields['block'].queryset
        # block dropdown only has self.block
        self.assertEqual(block_qset.count(), 1)
        self.assertEqual(block_qset[0].id, self.block.id)

    def test_bookable_blocks_block_no_events(self):
        """
        blocks appear in the choice dropdown in an empty form if they are:
         - open
         - have events
         - not past (i.e. all events in the past)
         - no event on the block is full
         - block hasn't started yet
        :return:
        """

        block = mommy.make_recipe(
            'flex_bookings.block', booking_open=True
        )

        self.assertTrue(block.booking_open)
        self.assertFalse(block.events.exists())
        self.assertFalse(block.is_past)
        self.assertFalse(block.has_full_class)
        self.assertFalse(block.has_started)

        formset = UserBlockFormSet(
            # data=self.formset_data({'form-TOTAL-FORMS': 2}),
            initial=[{'user': self.user.id, 'block': self.block.id}]
        )
        form = formset.forms[1] # get the second (empty) form
        block_qset = form.fields['block'].queryset
        # block dropdown only has self.block
        self.assertEqual(block_qset.count(), 1)
        self.assertEqual(block_qset[0].id, self.block.id)

    def test_bookable_blocks_past(self):
        """
        blocks appear in the choice dropdown in an empty form if they are:
         - open
         - have events
         - not past (i.e. all events in the past)
         - no event on the block is full
         - block hasn't started yet
        :return:
        """

        block = mommy.make_recipe(
            'flex_bookings.block', booking_open=True
        )
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True,
            date=timezone.now() - timedelta(5)
        )
        block.events.add(event)

        self.assertTrue(block.booking_open)
        self.assertTrue(block.events.exists())
        self.assertTrue(block.is_past)
        self.assertFalse(block.has_full_class)
        self.assertTrue(block.has_started)

        formset = UserBlockFormSet(
            # data=self.formset_data({'form-TOTAL-FORMS': 2}),
            initial=[{'user': self.user.id, 'block': self.block.id}]
        )
        form = formset.forms[1] # get the second (empty) form
        block_qset = form.fields['block'].queryset
        # block dropdown only has self.block
        self.assertEqual(block_qset.count(), 1)
        self.assertEqual(block_qset[0].id, self.block.id)

    def test_bookable_blocks_event_full(self):
        """
        blocks appear in the choice dropdown in an empty form if they are:
         - open
         - have events
         - not past (i.e. all events in the past)
         - no event on the block is full
         - block hasn't started yet
        :return:
        """

        block = mommy.make_recipe(
            'flex_bookings.block', booking_open=True
        )
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True, max_participants=1
        )
        event1 = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True,
        )
        block.events.add(event)
        block.events.add(event1)
        mommy.make_recipe('flex_bookings.booking', event=event)

        self.assertTrue(block.booking_open)
        self.assertTrue(block.events.exists())
        self.assertFalse(block.is_past)
        self.assertTrue(block.has_full_class)
        self.assertFalse(block.has_started)

        formset = UserBlockFormSet(
            # data=self.formset_data({'form-TOTAL-FORMS': 2}),
            initial=[{'user': self.user.id, 'block': self.block.id}]
        )
        form = formset.forms[1] # get the second (empty) form
        block_qset = form.fields['block'].queryset
        # block dropdown only has self.block
        self.assertEqual(block_qset.count(), 1)
        self.assertEqual(block_qset[0].id, self.block.id)

    def test_bookable_blocks_has_started(self):
        """
        blocks appear in the choice dropdown in an empty form if they are:
         - open
         - have events
         - not past (i.e. all events in the past)
         - no event on the block is full
         - block hasn't started yet
        :return:
        """
        block = mommy.make_recipe(
            'flex_bookings.block', booking_open=True
        )
        event = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True,
            date=timezone.now() - timedelta(1)
        )
        event1 = mommy.make_recipe(
            'flex_bookings.future_EV', booking_open=True,
        )
        block.events.add(event)
        block.events.add(event1)

        self.assertTrue(block.booking_open)
        self.assertTrue(block.events.exists())
        self.assertFalse(block.is_past)
        self.assertFalse(block.has_full_class)
        self.assertTrue(block.has_started)

        formset = UserBlockFormSet(
            # data=self.formset_data({'form-TOTAL-FORMS': 2}),
            initial=[{'user': self.user.id, 'block': self.block.id}]
        )
        form = formset.forms[1] # get the second (empty) form
        block_qset = form.fields['block'].queryset
        # block dropdown only has self.block
        self.assertEqual(block_qset.count(), 1)
        self.assertEqual(block_qset[0].id, self.block.id)


class PagesFormSetTests(TestCase):

    def setUp(self):
        self.page = mommy.make(Page)

    def formset_data(self, extra_data={}):
        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': self.page.id,
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_formset_valid(self):
        formset = PagesFormset(data=self.formset_data())
        self.assertTrue(formset.is_valid())


class PageFormTests(TestCase):

    def setUp(self):
        self.page = mommy.make(Page)

    def form_data(self, extra_data={}):
        data = {
            'id': self.page.id,
            'name': self.page.name,
            'heading': self.page.heading,
            'menu_name': self.page.menu_name,
            'menu_location': self.page.menu_location,
            'layout': self.page.layout
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_form_valid(self):
        form = PageForm(data=self.form_data(), instance=self.page)
        self.assertTrue(form.is_valid())

    def test_new_form_with_duplicate_page_name(self):
        data = {
            'name': self.page.name,
            'heading': 'Test Heading',
            'menu_name': 'test_name',
            'menu_location': 'main',
            'layout': 'no-img'
        }
        form = PageForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Page with this Name already exists",
            form.errors['name'][0],
        )


    def test_required_fields(self):
        pass

class SubsectionFormsetTests(TestCase):

    def setUp(self):
        self.subsection = mommy.make(SubSection)

    def formset_data(self, extra_data={}):
        data = {
            'subsections-TOTAL_FORMS': 1,
            'subsections-INITIAL_FORMS': 1,
            'subsections-0-id': self.subsection.id,
            'subsections-0-content': self.subsection.content,
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_formset_valid(self):
        formset = SubsectionFormset(data=self.formset_data())
        self.assertTrue(formset.is_valid())

    def test_content_field_required(self):
        formset = SubsectionFormset(
            data=self.formset_data({'subsections-0-content': ''})
        )
        self.assertFalse(formset.is_valid())

        form = formset.forms[0]
        self.assertIn(
            'This field is required', str(form.errors['content']),
            form.errors
        )


class PictureFormsetTests(TestCase):

    pass