import logging

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, \
    get_object_or_404, render_to_response
from django.views.generic import CreateView, ListView, UpdateView
from braces.views import LoginRequiredMixin

from activitylog.models import ActivityLog

from studioadmin.forms import TimetableWeeklySessionFormSet, \
    EditSessionForm, EditStretchClinicForm, StretchClinicFormSet
from studioadmin.views.utils import StaffUserMixin

from timetable.models import StretchClinic, WeeklySession

logger = logging.getLogger(__name__)


class WeeklySessionListView(LoginRequiredMixin, StaffUserMixin, ListView):

    model = WeeklySession
    template_name = 'studioadmin/timetable_sessions_list.html'
    context_object_name = 'sessions'

    def get_context_data(self):
        context = super(WeeklySessionListView, self).get_context_data()
        context['sessions_formset'] = TimetableWeeklySessionFormSet()
        context['sidenav_selection'] = 'timetable'
        return context

    def post(self, request, *args, **kwargs):
        session_forms = TimetableWeeklySessionFormSet(request.POST)

        if session_forms.has_changed():
            deleted_session_ids = []
            for form in session_forms:
                if form.has_changed() and 'DELETE' in form.changed_data:
                    session = WeeklySession.objects.get(id=form.instance.id)
                    deleted_session_ids.append(session.id)
                    # delete session
                    session.delete()

                msg = "Session{} {} {} been deleted".format(
                    's' if len(deleted_session_ids) > 1 else '',
                    ', '.join(["{}".format(id) for id in deleted_session_ids]),
                    'have' if len(deleted_session_ids) > 1 else 'has',
                )
            ActivityLog.objects.create(
                log="Session{plural} (id{plural} {ids}) {pluralhas} "
                    "been deleted by admin user {user}".format(
                        plural='s' if len(deleted_session_ids) > 1 else '',
                        pluralhas = 'have' if len(deleted_session_ids) > 1
                        else 'has',
                        ids=', '.join(
                            ["{}".format(id) for id in deleted_session_ids]
                        ),
                        user=request.user.username
                    )
            )
            messages.success(request, msg)
        else:
            messages.info(request, "No changes made")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:timetable_sessions_list')


class StretchClinicListView(LoginRequiredMixin, StaffUserMixin, ListView):

    model = StretchClinic
    template_name = 'studioadmin/timetable_clinics_list.html'
    context_object_name = 'clinics'

    def get_context_data(self):
        context = super(StretchClinicListView, self).get_context_data()
        context['clinics_formset'] = StretchClinicFormSet()
        context['sidenav_selection'] = 'timetable'
        return context

    def post(self, request, *args, **kwargs):
        clinics_forms = StretchClinicFormSet(request.POST)

        if clinics_forms.has_changed():
            deleted_clinic_ids = []
            updated_clinic_ids = []
            for form in clinics_forms:
                if form.has_changed():
                    if 'DELETE' in form.changed_data:
                        clinic = StretchClinic.objects.get(id=form.instance.id)
                        deleted_clinic_ids.append(clinic.id)
                        # delete session
                        clinic.delete()
                    else:
                        updated_clinic_ids.append(form.instance.id)
                        form.save()

            if deleted_clinic_ids:
                msg = "Stretch Clinic{} {} {} been deleted".format(
                    's' if len(deleted_clinic_ids) > 1 else '',
                    ', '.join(["{}".format(name) for name in deleted_clinic_ids]),
                    'have' if len(deleted_clinic_ids) > 1 else 'has',
                )
                ActivityLog.objects.create(
                    log="Stretch Clinic{plural} (id{plural} {ids}) "
                        "{pluralhas} been deleted by admin user {user}".format(
                            plural='s' if len(deleted_clinic_ids) > 1 else '',
                            pluralhas = 'have' if len(deleted_clinic_ids) > 1
                            else 'has',
                            ids=', '.join(
                                ["{}".format(id) for id in deleted_clinic_ids]
                            ),
                            user=request.user.username
                        )
                )
            if updated_clinic_ids:
                msg = "Stretch Clinic{} {} {} been updated".format(
                    's' if len(updated_clinic_ids) > 1 else '',
                    ', '.join(["{}".format(id) for id in updated_clinic_ids]),
                    'have' if len(updated_clinic_ids) > 1 else 'has',
                )
                ActivityLog.objects.create(
                    log="Stretch Clinic{plural} (id{plural} {ids}) "
                        "{pluralhas} been deleted by admin user {user}".format(
                            plural='s' if len(updated_clinic_ids) > 1 else '',
                            pluralhas = 'have' if len(updated_clinic_ids) > 1
                            else 'has',
                            ids=', '.join(
                                ["{}".format(id) for id in updated_clinic_ids]
                            ),
                            user=request.user.username
                        )
                )

            messages.success(request, msg)
        else:
            messages.info(request, "No changes made")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('studioadmin:timetable_clinics_list')


class CreateWeeklySessionView(LoginRequiredMixin, StaffUserMixin, CreateView):
    model = WeeklySession
    form_class = EditSessionForm
    template_name = 'studioadmin/add_weekly_session.html'

    def get_success_url(self):
        return reverse('studioadmin:timetable_sessions_list')


class CreateStretchClinicView(LoginRequiredMixin, StaffUserMixin, CreateView):
    model = StretchClinic
    form_class = EditStretchClinicForm
    template_name = 'studioadmin/add_stretch_clinic.html'

    def get_success_url(self):
        return reverse('studioadmin:timetable_clinics_list')


class WeeklySessionEditView(LoginRequiredMixin, StaffUserMixin, UpdateView):

    model = WeeklySession
    template_name = 'studioadmin/includes/weekly-session-modal.html'
    form_class = EditSessionForm

    def form_valid(self, form):
        form.save()
        if form.has_changed():
            messages.success(self.request, 'Saved!')
            form.save()
        else:
            messages.success(self.request, 'No changes made')
        return render_to_response(
                'studioadmin/includes/weekly-session-edit-success.html'
            )


class StretchClinicEditView(LoginRequiredMixin, StaffUserMixin, UpdateView):

    model = StretchClinic
    template_name = 'studioadmin/includes/stretch-clinic-modal.html'
    form_class = EditStretchClinicForm

    def form_valid(self, form):
        form.save()
        if form.has_changed():
            messages.success(self.request, 'Saved!')
            form.save()
        else:
            messages.success(self.request, 'No changes made')
        return render_to_response(
                'studioadmin/includes/stretch-clinic-edit-success.html'
            )
