from django.conf.urls import url
from payments.views import paypal_cancel_return, paypal_confirm_return

urlpatterns = [
    url(r'^confirm/$', paypal_confirm_return,
        name='paypal_confirm'),
    url(r'^cancel/$', paypal_cancel_return,
        name='paypal_cancel'),
    ]
