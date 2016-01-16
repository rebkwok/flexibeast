from django.core.management.base import BaseCommand
from website.models import Page


class Command(BaseCommand):

    def handle(self, *args, **options):

        page, created = Page.objects.get_or_create(
            name='about'
        )
        if created:
            page.menu_location = 'main'
            page.heading = ''
            page.layout = 'no-img'
            page.content = 'Coming Soon'
            page.save()

        if created:
            self.stdout.write('About page created.')
        else:
            self.stdout.write('About page already exists.')
