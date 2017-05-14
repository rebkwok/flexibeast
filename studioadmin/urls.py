from django.conf.urls import url
from django.views.generic import RedirectView
from studioadmin.views.activitylog import ActivityLogListView
from studioadmin.views.email_users import choose_users_to_email, \
    email_users_view
from studioadmin.views.users import UserListView
from studioadmin.views.website import PageListView, PageCreateView, \
    PageUpdateView


urlpatterns = [
    url(r'^users/$', UserListView.as_view(), name="users"),
    url(r'^users/email/$', choose_users_to_email, name="choose_email_users"),
    url(r'^users/email/emailform/$', email_users_view,
        name="email_users_view"),
    url(
        r'activitylog/$', ActivityLogListView.as_view(), name='activitylog'
    ),
    url(
        r'^website-pages/$',
        PageListView.as_view(), name='website_pages_list'
    ),
    url(
        r'^website-pages/new/$', PageCreateView.as_view(), name='add_page'
    ),
    url(
        r'^website-pages/(?P<name>[\w\d//-]+)$',
        PageUpdateView.as_view(), name='edit_page'
    ),
    url(
        r'^$',
        RedirectView.as_view(url='/studioadmin/classes/', permanent=True)
    ),
]
