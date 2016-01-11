from datetime import timedelta
from model_mommy import mommy

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone

from flex_bookings.models import Event, Booking, Block
from flex_bookings.views import update_block
from flex_bookings.tests.helpers import set_up_fb, _create_session, setup_view


class UpdateBlockViewTests(TestCase):
    def setUp(self):
        set_up_fb()
        self.factory = RequestFactory()
        self.user = mommy.make_recipe('flex_bookings.user')

    def _set_session(self, user, request):
        request.session = _create_session()
        request.user = user
        messages = FallbackStorage(request)
        request._messages = messages

    def _get_response(self, user, block):
        url = reverse('flex_bookings:update_block', args=[block.id])
        request = self.factory.get(url)
        self._set_session(user, request)
        return update_block(request)

    def _post_response(self, user, form_data):
        url = reverse('booking:update_block', args=[block.id])
        request = self.factory.post(url, form_data)
        self._set_session(user, request)
        return update_block(request)

    def test_update_block(self):
        """
        Test creating a block
        """
        pass
