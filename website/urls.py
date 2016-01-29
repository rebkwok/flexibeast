from django.conf.urls import url

from website.views import contact, page, restricted_page_not_logged_in

urlpatterns = [
    url(r'^contact/$', contact, name='contact'),
    url(
        r'^login-required', restricted_page_not_logged_in,
        name='restricted_page_not_logged_in'
    ),
    url(r'^(?P<page_name>[\w\d//-]+)/$', page, name='page'),
    url(r'^$', page, {'page_name': 'about'}, name='about'),
]
