from django.urls import reverse
from django.test import TestCase, RequestFactory

from studioadmin.tests.utils import TestPermissionMixin


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
