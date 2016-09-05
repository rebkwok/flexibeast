from datetime import datetime

from django.conf import settings
from django.utils import timezone

from website.models import Page

from reviews.models import Review


def website_pages(request):
    pages = Page.objects.all().exclude(active=False)
    return {'website_pages': pages}


def more_menu_options(request):
    """
    :param request:
    :return: True if there are website pages to be shown in the "More"
    dropdown menu
    """
    pages = Page.objects.all().exclude(active=False)
    more_menu_options_unrestricted = [
        True for page in pages if page.menu_name and
        page.menu_location == 'dropdown' and not page.restricted
        ]
    more_menu_options_restricted = [
        True for page in pages if page.menu_name and
        page.menu_location == 'dropdown' and page.restricted
        ]

    if more_menu_options_unrestricted:
        return {'more_menu_options': True}
    elif more_menu_options_restricted:
        if request.user.has_perm('website.can_view_restricted'):
            return {'more_menu_options': True}
        return {'more_menu_options': False}
    else:
        return {'more_menu_options': False}


def menu_options(request):
    """
    :param request:
    :return: True if there are any website pages to be shown in the menu bar
    """
    pages = Page.objects.all().exclude(active=False)
    menu_options = [True for page in pages if page.menu_name]
    return {'menu_options': True if menu_options else False}


def reviews_pending(request):
    if request.user.is_staff:
        reviews_pending = Review.objects.filter(reviewed=False).count()
        return {'reviews_pending': reviews_pending}
    else:
        return {}


def booking_on(request):
    return {'booking_on': settings.BOOKING_ON}


def out_of_office(request):
    start_date = datetime(2016, 9, 5, tzinfo=timezone.utc)
    end_date = datetime(2016, 9, 17, tzinfo=timezone.utc)

    out_of_office_status = False
    msg = ''
    if start_date < timezone.now() < end_date:
        out_of_office_status = True
        msg = 'I am at a conference until 16th September and will reply to ' \
          'any enquiries when I get back'

    return {'out_of_office': out_of_office_status, 'out_of_office_msg': msg}



