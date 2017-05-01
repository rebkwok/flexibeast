from django.contrib.auth.models import User

from model_mommy.recipe import Recipe, seq

from allauth.socialaccount.models import SocialApp


user = Recipe(User,
              username=seq("test_user"),
              password="password",
              email="test_user@test.com",
              )

fb_app = Recipe(SocialApp, provider='facebook')
