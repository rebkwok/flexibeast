from django.conf.urls import include, patterns, url


urlpatterns = patterns('',
    url(r'^contact/$',
        'website.views.contact', name='contact'
    ),
    url(r'^private-instruction/$',
        'website.views.private', name='private'
    ),
    url(r'', 'website.views.about', name='about'),
)
