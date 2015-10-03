from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.views.generic import RedirectView
from django.conf.urls.static import static

from accounts.views import CustomLoginView

urlpatterns = patterns('',
    url(r'^studioadmin/',
        include('studioadmin.urls', namespace='studioadmin')),
    url(r'^', include('flex_bookings.urls', namespace='flexbookings')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^gallery/', include('gallery.urls', namespace='gallery')),
    url(r'^reviews/', include('reviews.urls', namespace='reviews')),
    url(r'^', include('website.urls', namespace='website')),
    url(r'^accounts/profile/', include('accounts.urls', namespace='profile')),
    url(r'^accounts/login/$', CustomLoginView.as_view(), name='login'),
    (r'^accounts/', include('allauth.urls')),
    (r'^ckeditor/', include('ckeditor.urls')),
    (r'^payments/ipn-paypal-notify/', include('paypal.standard.ipn.urls')),
    url(r'payments/', include('payments.urls', namespace='payments')),
    url(r'^favicon.ico/$',
        RedirectView.as_view(url=settings.STATIC_URL+'favicon.ico',
                             permanent=False)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
