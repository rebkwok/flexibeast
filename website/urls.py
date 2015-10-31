from django.conf.urls import include, patterns, url

urlpatterns = patterns('',
    url(r'^contact/$',
        'website.views.contact', name='contact'
    ),
    # url(r'^private-instruction/$',
    #     'website.views.page', {'page_name': 'private'}, name='private'
    # ),
    url(r'^(?P<page_name>[\w\d-]+)/$', 'website.views.page', name='page'),
    url(r'^$', 'website.views.page', {'page_name': 'about'}, name='about'),
)
