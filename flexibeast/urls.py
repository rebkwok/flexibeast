from django.urls import include, path
from django.conf import settings
from django.contrib import admin
from django.views.generic import RedirectView
from django.conf.urls.static import static

from accounts.views import CustomLoginView

from website.views import permission_denied

urlpatterns = [
    path(
        'studioadmin/', include('studioadmin.urls')
    ),
    path('admin/', admin.site.urls),
    path('gallery/', include('gallery.urls')),
    path('timetable/', include('timetable.urls')),
    path('testimonials/', include('reviews.urls')),
    path('page-not-available/', permission_denied, name='permission_denied'),
    path('accounts/profile/', include('accounts.urls')),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('allauth.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('favicon.ico/',
        RedirectView.as_view(url=settings.STATIC_URL+'favicon.ico',
                             permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:  # pragma: no cover
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))

if settings.HEROKU:  # pragma: no cover
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )

urlpatterns.append(path('', include('website.urls')))