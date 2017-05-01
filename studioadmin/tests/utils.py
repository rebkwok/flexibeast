from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import User, Permission

from common.helpers import set_up_fb


class TestPermissionMixin(object):

    def setUp(self):
        set_up_fb()
        self.client = Client()
        self.factory = RequestFactory()
        self.user = User.objects.create(
            username='user', email='user@test.com', password='test'
        )
        self.staff_user = User.objects.create(
            username='staff', email='staff@test.com', password='test'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
