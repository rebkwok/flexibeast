from django import template

from website.models import MENU_CHOICES, PAGE_LAYOUT_CHOICES


register = template.Library()


@register.filter
def format_menu(value):
    """
    Show full name for website page menu choice
    """
    menu_choices = dict(MENU_CHOICES)
    return menu_choices[value]


@register.filter
def format_layout(value):
    """
    Show full name for website page layout choice
    """
    layout_choices = dict(PAGE_LAYOUT_CHOICES)
    return layout_choices[value]