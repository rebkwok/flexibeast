import pytz

from datetime import datetime, timedelta
from mock import Mock, patch
from model_mommy import mommy

from django.core.urlresolvers import reverse
from django.core import mail
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import User, Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone

from activitylog.models import ActivityLog

from studioadmin.tests.utils import TestPermissionMixin

from studioadmin.views.website import PageCreateView, PageListView, \
    PageUpdateView

from website.models import Page


class PageListViewTests(TestPermissionMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super(PageListViewTests, cls).setUpTestData()
        cls.url = reverse('studioadmin:website_pages_list')

    def test_staff_user_required(self):
        """
        not logged in: redirects to login page
        logged in as non-staff user: redirects to permission denied page
        """
        pass

    def test_all_pages_shown(self):
        pass
