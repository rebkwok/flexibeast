from django.urls import path, re_path

from website.views import about, classes, contact, home, page, \
    privacy_policy, restricted_page_not_logged_in, retreats, \
    stretch_clinics, workshops


app_name = 'website'


urlpatterns = [
    path('contact/', contact, name='contact'),
    path(
        'login-required/', restricted_page_not_logged_in,
        name='restricted_page_not_logged_in'
    ),
    path('about/', about, name='about'),
    path('classes/', classes, name='classes'),
    path('stretch-clinics/', stretch_clinics, name='stretch_clinics'),
    path('workshops/', workshops, name='workshops'),
    path('retreats/', retreats, name='retreats'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    re_path(r'^(?P<page_name>[\w\d//-]+)/$', page, name='page'),
    # path('', page, {'page_name': 'about'}, name='about'),
    path('', home, name='home'),
]
