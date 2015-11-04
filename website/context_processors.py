from website.models import Page

from reviews.models import Review


def website_pages(request):
    pages = Page.objects.all()
    return {'website_pages': pages}


def more_menu_options(request):
    """
    :param request:
    :return: True if there are website pages to be shown in the "More"
    dropdown menu
    """
    pages = Page.objects.all()
    more_menu_options = [
        True for page in pages if page.menu_name and
        page.menu_location == 'dropdown'
        ]
    return {'more_menu_options': True if more_menu_options else False}


def menu_options(request):
    """
    :param request:
    :return: True if there are any website pages to be shown in the menu bar
    """
    pages = Page.objects.all()
    menu_options = [True for page in pages if page.menu_name]
    return {'menu_options': True if menu_options else False}


def reviews_pending(request):
    if request.user.is_staff:
        reviews_pending = Review.objects.filter(reviewed=False).count()
        return {'reviews_pending': reviews_pending}
    else:
        return {}
