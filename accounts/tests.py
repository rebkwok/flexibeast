from decimal import Decimal

from model_mommy import mommy


from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.urls import reverse

from .admin import CookiePolicyAdminForm, DataPrivacyPolicyAdminForm
from .forms import DataPrivacyAgreementForm, SignupForm
from .models import CookiePolicy, DataPrivacyPolicy, SignedDataPrivacy
from .utils import active_data_privacy_cache_key, \
    has_active_data_privacy_agreement
from .views import ProfileUpdateView, profile
from common.helpers import set_up_fb


def make_data_privacy_agreement(user):
    if not has_active_data_privacy_agreement(user):
        if DataPrivacyPolicy.current_version() == 0:
            mommy.make(
                DataPrivacyPolicy, content='Foo', version=1
            )
        mommy.make(
            SignedDataPrivacy, user=user,
            version=DataPrivacyPolicy.current_version()
        )


class SignUpFormTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.factory = RequestFactory()

    def test_signup_form(self):
        form_data = {'first_name': 'Test',
                     'last_name': 'User'}
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_signup_form_with_invalid_data(self):
        # first_name must have 30 characters or fewer
        form_data = {'first_name': 'abcdefghijklmnopqrstuvwxyz12345',
                     'last_name': 'User'}
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_user_assigned_from_request(self):
        user = mommy.make(User)
        url = reverse('account_signup')
        request = self.factory.get(url)
        request.user = user
        form_data = {'first_name': 'New',
                     'last_name': 'Name'}
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.signup(request, user)
        self.assertEquals('New', user.first_name)
        self.assertEquals('Name', user.last_name)

    def test_signup_dataprotection_confirmation_required(self):
        mommy.make(DataPrivacyPolicy)
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'data_privacy_confirmation': False
        }
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_sign_up_with_data_protection(self):
        dp = mommy.make(DataPrivacyPolicy)
        self.assertFalse(SignedDataPrivacy.objects.exists())
        form_data = {
                'first_name': 'New',
                'last_name': 'Name',
                'username': 'testnew',
                'email': 'testnewuser@test.com',
                'password1': 'test1234',
                'password2': 'test1234',
                'data_privacy_confirmation': True
        }
        url = reverse('account_signup')
        self.client.post(url, form_data)
        user = User.objects.latest('id')
        self.assertEquals('New', user.first_name)
        self.assertEquals('Name', user.last_name)
        self.assertTrue(SignedDataPrivacy.objects.exists())
        self.assertEqual(user.data_privacy_agreement.first().version, dp.version)


class ProfileUpdateViewTests(TestCase):

    def setUp(self):
        set_up_fb()
        self.factory = RequestFactory()

    def test_updating_user_data(self):
        """
        Test custom view to allow users to update their details
        """
        user = mommy.make(User, username="test_user",
                          first_name="Test",
                          last_name="User",
                          )
        url = reverse('profile:update_profile')
        request = self.factory.post(
            url, {'username': user.username,
                  'first_name': 'Fred', 'last_name': user.last_name}
        )
        request.user = user
        view = ProfileUpdateView.as_view()
        resp = view(request)
        updated_user = User.objects.get(username="test_user")
        self.assertEquals(updated_user.first_name, "Fred")


class ProfileTest(TestCase):

    def setUp(self):
        set_up_fb()
        self.user = User.objects.create_user(
            username='testprofileuser', email='test@profile.test',
            password='test'
        )
        self.factory = RequestFactory()
        self.url = url = reverse('profile:profile')

    def test_profile_view(self):
        request = self.factory.get(self.url)
        request.user = self.user
        resp = profile(request)

        self.assertEquals(resp.status_code, 200)

    def test_profile_requires_signed_data_privacy(self):
        mommy.make(DataPrivacyPolicy)
        request = self.factory.get(self.url)
        request.user = self.user
        resp = profile(request)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('profile:data_privacy_review'), resp.url)


class DataPrivacyPolicyModelTests(TestCase):

    def test_no_policy_version(self):
        self.assertEqual(DataPrivacyPolicy.current_version(), 0)

    def test_policy_versioning(self):
        self.assertEqual(DataPrivacyPolicy.current_version(), 0)

        DataPrivacyPolicy.objects.create(content='Foo')
        self.assertEqual(DataPrivacyPolicy.current_version(), Decimal('1.0'))

        DataPrivacyPolicy.objects.create(content='Foo1')
        self.assertEqual(DataPrivacyPolicy.current_version(), Decimal('2.0'))

        DataPrivacyPolicy.objects.create(content='Foo2', version=Decimal('2.6'))
        self.assertEqual(DataPrivacyPolicy.current_version(), Decimal('2.6'))

        DataPrivacyPolicy.objects.create(content='Foo3')
        self.assertEqual(DataPrivacyPolicy.current_version(), Decimal('3.0'))

    def test_cannot_make_new_version_with_same_content(self):
        DataPrivacyPolicy.objects.create(content='Foo')
        self.assertEqual(DataPrivacyPolicy.current_version(), Decimal('1.0'))
        with self.assertRaises(ValidationError):
            DataPrivacyPolicy.objects.create(content='Foo')

    def test_policy_str(self):
        dp = DataPrivacyPolicy.objects.create(content='Foo')
        self.assertEqual(
            str(dp), 'Data Privacy Policy - Version {}'.format(dp.version)
        )


class CookiePolicyModelTests(TestCase):

    def test_policy_versioning(self):
        CookiePolicy.objects.create(content='Foo')
        self.assertEqual(CookiePolicy.current().version, Decimal('1.0'))

        CookiePolicy.objects.create(content='Foo1')
        self.assertEqual(CookiePolicy.current().version, Decimal('2.0'))

        CookiePolicy.objects.create(content='Foo2', version=Decimal('2.6'))
        self.assertEqual(CookiePolicy.current().version, Decimal('2.6'))

        CookiePolicy.objects.create(content='Foo3')
        self.assertEqual(CookiePolicy.current().version, Decimal('3.0'))

    def test_cannot_make_new_version_with_same_content(self):
        CookiePolicy.objects.create(content='Foo')
        self.assertEqual(CookiePolicy.current().version, Decimal('1.0'))
        with self.assertRaises(ValidationError):
            CookiePolicy.objects.create(content='Foo')

    def test_policy_str(self):
        dp = CookiePolicy.objects.create(content='Foo')
        self.assertEqual(
            str(dp), 'Cookie Policy - Version {}'.format(dp.version)
        )


class SignedDataPrivacyModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        DataPrivacyPolicy.objects.create(content='Foo')

    def setUp(self):
        self.user = mommy.make(User)

    def test_cached_on_save(self):
        make_data_privacy_agreement(self.user)
        self.assertTrue(cache.get(active_data_privacy_cache_key(self.user)))

        cache.clear()
        DataPrivacyPolicy.objects.create(content='New Foo')
        self.assertFalse(has_active_data_privacy_agreement(self.user))

    def test_delete(self):
        make_data_privacy_agreement(self.user)
        self.assertTrue(cache.get(active_data_privacy_cache_key(self.user)))

        SignedDataPrivacy.objects.get(user=self.user).delete()
        self.assertIsNone(cache.get(active_data_privacy_cache_key(self.user)))


class DataPrivacyViewTests(TestCase):

    def test_get_data_privacy_view(self):
        # no need to be a logged in user to access
        resp = self.client.get(reverse('data_privacy_policy'))
        self.assertEqual(resp.status_code, 200)


class CookiePolicyViewTests(TestCase):

    def test_get_cookie_view(self):
        # no need to be a logged in user to access
        resp = self.client.get(reverse('cookie_policy'))
        self.assertEqual(resp.status_code, 200)


class SignedDataPrivacyCreateViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('profile:data_privacy_review')
        cls.data_privacy_policy = mommy.make(DataPrivacyPolicy, version=None)
        cls.user = User.objects.create_user(
            username='test', email='test@test.com', password='test'
        )
        make_data_privacy_agreement(cls.user)

    def setUp(self):
        super(SignedDataPrivacyCreateViewTests, self).setUp()
        self.client.login(username=self.user.username, password='test')

    def test_user_already_has_active_signed_agreement(self):
        # dp agreement is created in setup
        self.assertTrue(has_active_data_privacy_agreement(self.user))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('website:home'))

        # make new policy
        cache.clear()
        mommy.make(DataPrivacyPolicy, version=None)
        self.assertFalse(has_active_data_privacy_agreement(self.user))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_create_new_agreement(self):
        # make new policy
        cache.clear()
        mommy.make(DataPrivacyPolicy, version=None)
        self.assertFalse(has_active_data_privacy_agreement(self.user))

        self.client.post(self.url, data={'confirm': True})
        self.assertTrue(has_active_data_privacy_agreement(self.user))


class DataPrivacyAgreementFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = mommy.make(User)
        mommy.make(DataPrivacyPolicy)

    def test_confirm_required(self):
        form = DataPrivacyAgreementForm(next_url='/')
        self.assertFalse(form.is_valid())

        form = DataPrivacyAgreementForm(next_url='/', data={'confirm': True})
        self.assertTrue(form.is_valid())


class CookiePolicyAdminFormTests(TestCase):

    def test_create_cookie_policy_version_help(self):
        form = CookiePolicyAdminForm()
        # version initial set to 1.0 for first policy
        self.assertEqual(form.fields['version'].help_text, '')
        self.assertEqual(form.fields['version'].initial, 1.0)

        mommy.make(CookiePolicy, version=1.0)
        # help text added if updating
        form = CookiePolicyAdminForm()
        self.assertEqual(
            form.fields['version'].help_text,
            'Current version is 1.0.  Leave blank for next major version'
        )
        self.assertIsNone(form.fields['version'].initial)

    def test_validation_error_if_no_changes(self):
        policy = mommy.make(CookiePolicy, version=1.0, content='Foo')
        form = CookiePolicyAdminForm(
            data={
                'content': 'Foo',
                'version': 1.5,
                'issue_date': policy.issue_date
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            [
                'No changes made from previous version; new version must '
                'update policy content'
            ]
        )


class DataPrivacyPolicyAdminFormTests(TestCase):

    def test_create_data_privacy_policy_version_help(self):
        form = DataPrivacyPolicyAdminForm()
        # version initial set to 1.0 for first policy
        self.assertEqual(form.fields['version'].help_text, '')
        self.assertEqual(form.fields['version'].initial, 1.0)

        mommy.make(DataPrivacyPolicy, version=1.0)
        # help text added if updating
        form = DataPrivacyPolicyAdminForm()
        self.assertEqual(
            form.fields['version'].help_text,
            'Current version is 1.0.  Leave blank for next major version'
        )
        self.assertIsNone(form.fields['version'].initial)

    def test_validation_error_if_no_changes(self):
        policy = mommy.make(DataPrivacyPolicy, version=1.0, content='Foo')
        form = DataPrivacyPolicyAdminForm(
            data={
                'content': 'Foo',
                'version': 1.5,
                'issue_date': policy.issue_date
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            [
                'No changes made from previous version; new version must '
                'update policy content'
            ]
        )
