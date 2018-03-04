from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):

    def handle(self, *args, **options):

        self.stdout.write("Configuring facebook social app for test site")

        site = Site.objects.get(id=1)
        site.name = "flexibeast"
        site.save()

        sapp, _ = SocialApp.objects.get_or_create(name="flexibeast",
                                        provider="facebook",
                                        client_id="1234",
                                        secret="1234")
        sapp.save()
        sapp.sites.add(1)
