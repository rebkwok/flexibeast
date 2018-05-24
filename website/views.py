from django.shortcuts import render, HttpResponse, HttpResponseRedirect, \
    get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.conf import settings
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from django.template.loader import get_template, select_template
from django.template import TemplateDoesNotExist
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.core.mail import send_mail

from accounts.models import DataPrivacyPolicy
from accounts.utils import has_active_data_privacy_agreement
from reviews.models import Review
from timetable.models import WeeklySession, Event
from website.models import Page
from website.forms import ContactForm


TEMPLATES = {
    'no-img': 'website/page.html',
    '1-img-top': 'website/page.html',
    '1-img-left': 'website/page_side.html',
    '1-img-right': 'website/page_side.html',
    'img-col-left': 'website/page_col.html',
    'img-col-right': 'website/page_col.html',
}


def home(request):
    if DataPrivacyPolicy.current_version() > 0 and request.user.is_authenticated \
            and not has_active_data_privacy_agreement(request.user):
        return HttpResponseRedirect(
            reverse('profile:data_privacy_review') + '?next=' + request.path
        )
    reviews = Review.objects.filter(selected=True).order_by('-submission_date')
    return TemplateResponse(
        request, 'website/index.html',
        {'nav_section': 'home', 'testimonials': reviews}
    )

def about(request):
    return TemplateResponse(
        request, 'website/about.html', {'nav_section': 'about'}
    )


def classes(request):
    return TemplateResponse(
        request, 'website/classes.html', {'nav_section': 'services'}
    )


def retreats(request):
    return TemplateResponse(
        request, 'website/retreats.html', {'nav_section': 'services'}
    )


def stretch_clinics(request):
    events = Event.objects.filter(show_on_site=True, event_type='clinic').order_by('-date')
    return TemplateResponse(
        request, 'website/stretch_clinics.html',
        {'nav_section': 'services', 'events': events}
    )


def workshops(request):
    events = Event.objects.filter(show_on_site=True, event_type='workshop').order_by('-date')
    return TemplateResponse(
        request, 'website/workshops.html', {'nav_section': 'services', 'events': events}
    )


def page(request, page_name):
    page = get_object_or_404(Page, name=page_name)

    if not page.active and not request.user.is_staff:
        return HttpResponseRedirect(reverse(settings.PERMISSION_DENIED_URL))

    if page.restricted:
        if request.user.is_anonymous:
            return HttpResponseRedirect(
                reverse('website:restricted_page_not_logged_in')
            )
        elif not request.user.is_staff and not \
            request.user.has_perm('website.can_view_restricted'):
            return HttpResponseRedirect(reverse(settings.PERMISSION_DENIED_URL))
        elif (
            DataPrivacyPolicy.current_version() > 0 and
                request.user.is_authenticated and not
                has_active_data_privacy_agreement(request.user)
        ):
            return HttpResponseRedirect(
                reverse('profile:data_privacy_review') + '?next=' + request.path
            )

    template = TEMPLATES['no-img']
    if page.pictures.count() > 0:
        template = TEMPLATES[page.layout]

    try:
        select_template(
            ['website/{}_extra.html'.format(page_name)]
        )
        include_html = 'website/{}_extra.html'.format(page_name)
    except TemplateDoesNotExist:
        include_html = ''

    context = {
        'page': page, 'include_html': include_html, 'nav_section': 'more'
    }
    return TemplateResponse(request, template, context)


def process_contact_form(request):
    form = ContactForm(request.POST)

    if form.is_valid():
        subject = form.cleaned_data['subject']
        other_subject = form.cleaned_data.get('other_subject')
        email_address = form.cleaned_data['email_address']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        cc = form.cleaned_data['cc']
        message = form.cleaned_data['message']

        if other_subject:
            subject = "{}: {}".format(subject, other_subject)

        ctx = {
            'host': 'http://{}'.format(request.META.get('HTTP_HOST')),
            'first_name': first_name,
            'last_name': last_name,
            'email_address': email_address,
            'message': message,
        }

        try:
            msg = EmailMultiAlternatives(
                '{} {}'.format(settings.ACCOUNT_EMAIL_SUBJECT_PREFIX, subject),
                get_template(
                    'website/contact_form_email.txt'
                ).render(ctx),
                settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_STUDIO_EMAIL],
                cc=[email_address] if cc else [],
                reply_to=[email_address]
            )
            msg.attach_alternative(
                get_template(
                    'website/contact_form_email.html'
                ).render(ctx),
                "text/html"
            )
            msg.send(fail_silently=False)

            messages.info(
                request,
                "Thank you for your enquiry! Your email has been sent and "
                "we'll get back to you as soon as possible."
            )
        except Exception as e:
            # send mail to tech support with Exception
            try:
                send_mail('{} An error occurred! ({})'.format(
                        settings.ACCOUNT_EMAIL_SUBJECT_PREFIX,
                        'contact form'
                        ),
                    'An error occurred in {}\n\nThe exception '
                    'raised was "{}"\n\n'
                    'first_name: {}\n'
                    'last_name: {}\n'
                    'email: {}\n'
                    'message: {}'.format(
                        __name__, repr(e), first_name, last_name,
                        email_address, message
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.SUPPORT_EMAIL],
                    fail_silently=True)
                messages.error(request, "A problem occurred while submitting "
                                        "the form.  Tech support has been notified.")
            except Exception as e:
                messages.error(
                    request, mark_safe(
                        "A problem occurred while submitting the form, "
                         "please contact the studio on "
                         "<a href='mailto:{}' target=_blank>{}</a> for "
                        "information".format(
                            settings.DEFAULT_STUDIO_EMAIL,
                            settings.DEFAULT_STUDIO_EMAIL
                        )
                    )
                )
                pass

        request.session['first_name'] = first_name
        request.session['last_name'] = last_name
        request.session['email_address'] = email_address
        # required field, so must be True if form valid
        request.session['data_privacy_accepted'] = True

        return_url = request.session.get(
            'return_url', reverse('website:contact')
        )
        return HttpResponseRedirect(return_url)

    else:
        messages.error(
            request, "Please correct the errors below"
        )
        return TemplateResponse(
            request, 'website/contact.html',
            {'section': 'contact', 'form': form}
        )


def get_initial_contact_form(request):
    request.session['return_url'] = request.META.get(
        'HTTP_REFERER', request.get_full_path()
    )

    tt_session_id = request.GET.get('enq')
    if tt_session_id:
        tt_session = WeeklySession.objects.get(id=tt_session_id)
        subject = 'Booking Enquiry'
    else:
        page = request.session['return_url'].split('/')[-2]
        if page == 'classes':
            subject = 'Booking Enquiry'
        elif page == 'workshops':
            subject = 'Workshop Enquiry'
        else:
            subject = 'General Enquiry'

    first_name = request.session.get('first_name', '')
    last_name = request.session.get('last_name', '')
    email_address = request.session.get('email_address', '')
    data_privacy_accepted = request.session.get('data_privacy_accepted', False)

    return ContactForm(initial={
        'first_name': first_name, 'last_name': last_name,
        'email_address': email_address, 'subject': subject,
        'other_subject': tt_session if tt_session_id else '',
        'data_privacy_accepted': data_privacy_accepted,
    })


def contact(request, template_name='website/contact.html'):

    if request.method == 'POST':
        return process_contact_form(request)

    form = get_initial_contact_form(request)

    return TemplateResponse(
        request, template_name, {'section': 'contact', 'form': form}
    )


def permission_denied(request):
    return render(request, 'website/permission_denied.html')


def restricted_page_not_logged_in(request):
    return render(request, 'website/restricted_page_not_logged_in.html')


def privacy_policy(request):
    return render(request, 'website/privacy_policy.html')

