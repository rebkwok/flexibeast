from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag('reviews/ratings.html')
def show_rating(rating):
    result = {}
    if rating:
        rating_list = []
        for i in range(rating):
            rating_list.append(1)
        for i in range(5-rating):
            rating_list.append(0)
        result = {'rating_list': rating_list}
    return result

