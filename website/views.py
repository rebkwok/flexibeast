from django.shortcuts import render, HttpResponse, HttpResponseRedirect, \
    get_object_or_404
from django.template.response import TemplateResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from django.template.loader import get_template, select_template
from django.template import TemplateDoesNotExist
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.core.mail import send_mail

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


def page(request, page_name):
    page = get_object_or_404(Page, name=page_name)

    if page.restricted and not request.user.is_staff and not \
            request.user.has_perm('website.can_view_restricted'):
        return HttpResponseRedirect(reverse(settings.PERMISSION_DENIED_URL))

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

    return TemplateResponse(
        request, template, {'page': page, 'include_html': include_html}
    )


def process_contact_form(request):
    form = ContactForm(request.POST)

    if form.is_valid():
        subject = form.cleaned_data['subject']
        email_address = form.cleaned_data['email_address']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        cc = form.cleaned_data['cc']
        message = form.cleaned_data['message']

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
    first_name = request.session.get('first_name', '')
    last_name = request.session.get('last_name', '')
    email_address = request.session.get('email_address', '')

    page = request.session['return_url'].split('/')[-2]
    if page == 'classes':
        subject = 'Booking Enquiry'
    elif page == 'workshops':
        subject = 'Workshop Enquiry'
    else:
        subject = 'General Enquiry'

    return ContactForm(initial={
        'first_name': first_name, 'last_name': last_name,
        'email_address': email_address, 'subject': subject
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