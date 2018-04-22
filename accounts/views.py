from django.shortcuts import render, HttpResponse, HttpResponseRedirect, \
    get_object_or_404
from django.views.generic import FormView, UpdateView
from django.contrib.auth.models import User
from django.urls import reverse
from braces.views import LoginRequiredMixin

from allauth.account.views import LoginView

from .forms import DataPrivacyAgreementForm
from .models import DataPrivacyPolicy, SignedDataPrivacy
from .utils import has_active_data_privacy_agreement



def profile(request):
    if DataPrivacyPolicy.current_version() > 0 and request.user.is_authenticated \
            and not has_active_data_privacy_agreement(request.user):
        return HttpResponseRedirect(
            reverse('accounts:data_privacy_review') + '?next=' + request.path
        )
    return render(request, 'account/profile.html')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    template_name = 'account/update_profile.html'
    fields = ('username', 'first_name', 'last_name',)

    def get_object(self):
        return get_object_or_404(
            User, username=self.request.user.username, email=self.request.user.email
        )

    def get_success_url(self):
        return reverse('profile:profile')


class CustomLoginView(LoginView):

    def get_success_url(self):
        super(CustomLoginView, self).get_success_url()

        ret = self.request.POST.get('next') or self.request.GET.get('next')
        if not ret or ret == '/accounts/password/change/':
            ret = reverse('profile:profile')

        return ret


class SignedDataPrivacyCreateView(LoginRequiredMixin, FormView):
    template_name = 'account/data_privacy_review.html'
    form_class = DataPrivacyAgreementForm

    def dispatch(self, *args, **kwargs):
        if has_active_data_privacy_agreement(self.request.user):
            return HttpResponseRedirect(
                self.request.GET.get('next', reverse('booking:events'))
            )
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['next_url'] = self.request.GET.get('next')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_needed = (
            SignedDataPrivacy.objects.filter(
                user=self.request.user,
                version__lt=DataPrivacyPolicy.current_version()
            ).exists() and not has_active_data_privacy_agreement(
                self.request.user)
        )

        context.update({
            'data_protection_policy': DataPrivacyPolicy.current(),
            'update_needed': update_needed
        })
        return context

    def form_valid(self, form):
        user = self.request.user
        SignedDataPrivacy.objects.create(
            user=user, version=form.data_privacy_policy.version
        )
        return self.get_success_url()

    def get_success_url(self):
        return HttpResponseRedirect(reverse('accounts:profile'))


def data_privacy_policy(request):
    return render(
        request, 'account/data_privacy_policy.html',
        {'data_privacy_policy': DataPrivacyPolicy.current()}
    )


def cookie_policy(request):
    return render(
        request, 'account/cookie_policy.html',
        {'data_privacy_policy': DataPrivacyPolicy.current()}
    )
