from django.conf.urls import url

from website.views import about, classes, contact, home, page, \
    restricted_page_not_logged_in, private, workshops

urlpatterns = [
    url(r'^contact/$', contact, name='contact'),
    url(
        r'^login-required', restricted_page_not_logged_in,
        name='restricted_page_not_logged_in'
    ),
    url(r'^about/$', about, name='about'),
    url(r'^classes/$', classes, name='classes'),
    url(r'^workshops/$', workshops, name='workshops'),
    url(r'^private-instruction/$', private, name='private'),

    url(r'^(?P<page_name>[\w\d//-]+)/$', page, name='page'),
    # url(r'^$', page, {'page_name': 'about'}, name='about'),
    url(r'^$', home, name='home'),
]
