import os

from model_bakery import baker
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.test import TestCase, override_settings

from studioadmin.forms import (
    ChooseUsersFormSet,
    DAY_CHOICES,
    DAY_CHOICES_DICT,
    EmailUsersForm,
    PageForm,
    PagesFormset,
    PictureFormset,
    TimetableWeeklySessionFormSet,
    EditSessionForm
)
from timetable.models import Location, WeeklySession
from website.models import Page


class TimetableWeeklySessionFormSetTests(TestCase):

    def setUp(self):
        self.session = baker.make(WeeklySession)
        self.formset_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': str(self.session.id),
        }

    def test_event_formset_valid(self):
        formset = TimetableWeeklySessionFormSet(data=self.formset_data)
        self.assertTrue(formset.is_valid())

    def test_additional_form_data(self):
        formset = TimetableWeeklySessionFormSet(
            data=self.formset_data, queryset=WeeklySession.objects.all())
        form = formset.forms[0]
        self.assertEquals(form.formatted_day, DAY_CHOICES_DICT[self.session.day])
        self.assertEquals(form.full_id, 'full_0')

    def test_can_delete(self):
        session_to_delete = baker.make(WeeklySession)
        fset_data = self.formset_data.copy()
        fset_data.update(
            {
                'form-TOTAL_FORMS': 2,
                'form-INITIAL_FORMS': 2,
                'form-1-DELETE': 'on',
                'form-1-id': session_to_delete.id,
            }
        )
        formset = TimetableWeeklySessionFormSet(
            data=fset_data, queryset=WeeklySession.objects.all()
        )
        self.assertEqual(len(formset.deleted_forms), 1)
        deleted_form = formset.deleted_forms[0]
        self.assertEqual(deleted_form.cleaned_data['id'], session_to_delete)


class WeeklySessionEditFormTests(TestCase):

    def setUp(self):

        location = baker.make(Location)
        self.form_data = {
            'name': 'test_event',
            'day': '01MON',
            'time': '12:00',
            'cost': '7',
            'location': location.id
        }

    def test_form_valid(self):
        form = EditSessionForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_time(self):
        data = self.form_data
        data.update({'time': '25:00'})
        form = EditSessionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid time format', str(form.errors['time']))


class ChooseUsersFormSetTests(TestCase):

    def setUp(self):
        self.user = baker.make_recipe('common.user')

    def formset_data(self, extra_data={}):

        data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-id': str(self.user.id),
            }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_choose_users_formset_valid(self):
        formset = ChooseUsersFormSet(data=self.formset_data())
        self.assertTrue(formset.is_valid())


class EmailUsersFormTests(TestCase):

    def setUp(self):
        pass

    def form_data(self, extra_data={}):
        data = {
            'subject': 'Test subject',
            'from_address': settings.DEFAULT_FROM_EMAIL,
            'message': 'Test message'
        }

        for key, value in extra_data.items():
            data[key] = value

        return data

    def test_form_valid(self):
        form = EmailUsersForm(data=self.form_data())
        self.assertTrue(form.is_valid())

    def test_missing_from_address(self):
        form = EmailUsersForm(
            data=self.form_data({'from_address': ''})
        )
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors['from_address'],
            ['This field is required.']
        )

    def test_missing_message(self):
        form = EmailUsersForm(
            data=self.form_data({'message': ''})
        )
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors['message'],
            ['This field is required.']
        )


class PagesFormSetTests(TestCase):

    def setUp(self):
        self.page = baker.make(Page)

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
        self.page = baker.make(Page)

    def form_data(self, extra_data={}):
        data = {
            'id': self.page.id,
            'name': self.page.name,
            'heading': self.page.heading,
            'menu_name': self.page.menu_name,
            'menu_location': self.page.menu_location,
            'layout': self.page.layout,
            'content': self.page.content,
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
            'layout': 'no-img',
            'content': self.page.content
        }
        form = PageForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Page with this Name already exists",
            form.errors['name'][0],
        )

    def test_form_invalid_name(self):
        data = {
            'name': 'name&',
            'heading': 'Test Heading',
            'menu_name': 'test_name',
            'menu_location': 'main',
            'layout': 'no-img',
            'content': self.page.content
        }
        form = PageForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "This field must contain only letters, numbers, / or -",
            form.errors['name'][0],
        )


@override_settings(MEDIA_ROOT='/tmp/')
class PictureFormsetTests(TestCase):

    def test_form_valid(self):
        page = baker.make(Page)
        pic_file = NamedTemporaryFile(suffix='.jpg', dir='/tmp')

        form_data = {
            'pictures-TOTAL_FORMS': 1,
            'pictures-INITIAL_FORMS': 0,
            'pictures-0-image': pic_file.name,
            }

        form = PictureFormset(data=form_data, instance=page)
        self.assertTrue(form.is_valid())
        os.unlink(pic_file.name)

    def test_main_ticked_for_more_than_one_picture(self):
        page = baker.make(Page)
        pic_file = NamedTemporaryFile(suffix='.txt', dir='/tmp')
        pic_file1 = NamedTemporaryFile(suffix='.txt', dir='/tmp')

        form_data = {
            'pictures-TOTAL_FORMS': 2,
            'pictures-INITIAL_FORMS': 0,
            'pictures-0-image': pic_file.name,
            'pictures-0-main': True,
            'pictures-1-image': pic_file1.name,
            'pictures-1-main': True
            }

        form = PictureFormset(data=form_data, instance=page)
        self.assertFalse(form.is_valid())
        self.assertIn(
            {
                'main image': 'More than one image is selected as the "main" '
                              'image to be displayed in single image layouts.  '
                              'Please select one only.'
            },
            form.errors
        )
        os.unlink(pic_file.name)
        os.unlink(pic_file1.name)
