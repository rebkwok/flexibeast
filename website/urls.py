from django.conf.urls import url

from website.views import contact, page

urlpatterns = [
    url(r'^contact/$', contact, name='contact'
    ),
    url(r'^(?P<page_name>[\w\d-]+)/$', page, name='page'),
    url(r'^$', page, {'page_name': 'about'}, name='about'),
]
