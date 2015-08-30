from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):

    def handle(self, *args, **options):

        self.stdout.write("Configuring facebook social app for test site")

        site = Site.objects.get(id=1)
        site.name = "flexibeast"
        site.save()

        sapp, _ = SocialApp.objects.get_or_create(name="flexibeast - test",
                                        provider="facebook",
                                        client_id="1899252493632325",
                                        secret="880e9e082a9b38bc1979e3232c024a9b")
        sapp.save()
        sapp.sites.add(1)
