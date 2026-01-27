# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms
#
# This file contains Apache-2.0 licensed contributions copyrighted by the following contributors:
# SPDX-FileContributor: luto

from pathlib import Path

from csp.decorators import csp_update
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django.views.generic import (
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django.http import HttpResponse
from django_context_decorator import context
from django_scopes import scope, scopes_disabled
from formtools.wizard.views import SessionWizardView

from imanage.common.forms import I18nEventFormSet
from imanage.common.models import ActivityLog
from imanage.common.plugins import get_all_plugins_grouped
from imanage.common.text.phrases import phrases
from imanage.common.ui import Button, delete_link
from imanage.common.views.helpers import is_htmx
from imanage.common.views.mixins import (
    ActionConfirmMixin,
    EventPermissionRequired,
    Filterable,
    PermissionRequired,
    SensibleBackWizardMixin,
)
from imanage.event.exporters import (
    AnalyticsCSVExporter,
    AttendeeCSVExporter,
    ReviewSummaryCSVExporter,
)
from imanage.event.forms import (
    EventWizardBasicsForm,
    EventWizardDisplayForm,
    EventWizardInitialForm,
    EventWizardPluginForm,
    EventWizardTimelineForm,
)
from imanage.event.models import Event, Team, TeamInvite
from imanage.orga.forms import EventForm
from imanage.orga.forms.event import (
    EventFooterLinkFormset,
    EventHeaderLinkFormset,
    EventHistoryFilterForm,
    MailSettingsForm,
    ReviewPhaseForm,
    ReviewScoreCategoryForm,
    ReviewSettingsForm,
    WidgetGenerationForm,
    WidgetSettingsForm,
)
from imanage.orga.signals import activate_event
from imanage.person.forms import UserForm
from imanage.person.models import User
from imanage.submission.models import ReviewPhase, ReviewScoreCategory
from imanage.submission.tasks import recalculate_all_review_scores


class EventSettingsPermission(EventPermissionRequired):
    permission_required = "event.update_event"
    write_permission_required = "event.update_event"

    @property
    def permission_object(self):
        return self.request.event


class EventDetail(EventSettingsPermission, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "orga/settings/form.html"

    def get_object(self, queryset=None):
        return self.object

    @cached_property
    def object(self):
        return Event.objects.prefetch_related("extra_links").get(
            pk=self.request.event.pk
        )

    def get_form_kwargs(self, *args, **kwargs):
        response = super().get_form_kwargs(*args, **kwargs)
        response["is_administrator"] = self.request.user.is_administrator
        return response

    @context
    @cached_property
    def header_links_formset(self):
        return EventHeaderLinkFormset(
            self.request.POST if self.request.method == "POST" else None,
            event=self.object,
            prefix="header-links",
            instance=self.object,
        )

    @context
    @cached_property
    def footer_links_formset(self):
        return EventFooterLinkFormset(
            self.request.POST if self.request.method == "POST" else None,
            event=self.object,
            prefix="footer-links",
            instance=self.object,
        )

    @context
    def tablist(self):
        return {
            "general": _("General information"),
            "localisation": _("Localisation"),
            "display": _("Display settings"),
            "texts": _("Texts"),
        }

    def get_success_url(self) -> str:
        return self.object.orga_urls.settings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_buttons"] = [Button()]
        if self.request.user.is_administrator:
            context["submit_buttons_extra"] = [
                delete_link(
                    self.request.event.orga_urls.delete, label=_("Delete event")
                )
            ]
        return context

    @transaction.atomic
    def form_valid(self, form):
        if (
            not self.footer_links_formset.is_valid()
            or not self.header_links_formset.is_valid()
        ):
            messages.error(self.request, phrases.base.error_saving_changes)
            return self.form_invalid(form)

        result = super().form_valid(form)
        self.footer_links_formset.save()
        self.header_links_formset.save()

        # TODO log data and display
        form.instance.log_action(
            "imanage.event.update", person=self.request.user, orga=True
        )
        messages.success(self.request, phrases.base.saved)
        return result


class EventLive(EventSettingsPermission, TemplateView):
    template_name = "orga/event/live.html"

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        warnings = []
        suggestions = []
        # TODO: move to signal
        if (
            not self.request.event.cfp.text
            or len(str(self.request.event.cfp.text)) < 50
        ):
            warnings.append(
                {
                    "text": _("The CfP doesn’t have a full text yet."),
                    "url": self.request.event.cfp.urls.text,
                }
            )
        if (
            not self.request.event.landing_page_text
            or len(str(self.request.event.landing_page_text)) < 50
        ):
            warnings.append(
                {
                    "text": _("The event doesn’t have a landing page text yet."),
                    "url": self.request.event.orga_urls.settings,
                }
            )
        # TODO: test that mails can be sent
        if (
            self.request.event.get_feature_flag("use_tracks")
            and self.request.event.cfp.request_track
            and self.request.event.tracks.count() < 2
        ):
            suggestions.append(
                {
                    "text": _(
                        "You want submitters to choose the tracks for their proposals, but you do not offer tracks for selection. Add at least one track!"
                    ),
                    "url": self.request.event.cfp.urls.tracks,
                }
            )
        if self.request.event.submission_types.count() == 1:
            suggestions.append(
                {
                    "text": _("You have configured only one session type so far."),
                    "url": self.request.event.cfp.urls.types,
                }
            )
        if not self.request.event.questions.exists():
            suggestions.append(
                {
                    "text": _("You have configured no custom fields yet."),
                    "url": self.request.event.cfp.urls.new_question,
                }
            )
        result["warnings"] = warnings
        result["suggestions"] = suggestions
        button_kwargs = {"name": "action", "icon": None}
        if self.request.event.is_public:
            button_kwargs["value"] = "deactivate"
            button_kwargs["color"] = "danger"
            button_kwargs["label"] = _("Go offline")
        else:
            button_kwargs["value"] = "activate"
            button_kwargs["label"] = _("Go live")
        result["submit_buttons"] = [Button(**button_kwargs)]
        return result

    def post(self, request, *args, **kwargs):
        event = request.event
        action = request.POST.get("action")
        if action == "activate":
            if event.is_public:
                messages.success(request, _("This event was already live."))
            else:
                responses = activate_event.send_robust(event, request=request)
                exceptions = [
                    response[1]
                    for response in responses
                    if isinstance(response[1], Exception)
                ]
                if exceptions:
                    from imanage.common.templatetags.rich_text import render_markdown

                    messages.error(
                        request,
                        mark_safe("\n".join(render_markdown(e) for e in exceptions)),
                    )
                else:
                    event.is_public = True
                    event.save()
                    event.log_action(
                        "imanage.event.activate",
                        person=self.request.user,
                        orga=True,
                        data={},
                    )
                    messages.success(request, _("This event is now public."))
                    for response in responses:
                        if isinstance(response[1], str):
                            messages.success(request, response[1])
        else:  # action == 'deactivate'
            if not event.is_public:
                messages.success(request, _("This event was already hidden."))
            else:
                event.is_public = False
                event.save()
                event.log_action(
                    "imanage.event.deactivate",
                    person=self.request.user,
                    orga=True,
                    data={},
                )
                messages.success(request, _("This event is now hidden."))
        if not copy_from_event:
            from imanage.submission.models import (
                Question,
                QuestionTarget,
                QuestionVariant,
                ReviewScore,
                ReviewScoreCategory,
            )

            # Add Paper PDF question
            Question.objects.create(
                event=event,
                target=QuestionTarget.SUBMISSION,
                variant=QuestionVariant.FILE,
                question={"en": "Paper (PDF)"},
                help_text={"en": "Please upload your paper as a PDF file."},
                question_required=QuestionRequired.REQUIRED,
                active=True,
            )
            # Add Academic Review Categories
            cat_originality = ReviewScoreCategory.objects.create(
                event=event, name={"en": "Originality"}, weight=1, required=True
            )
            cat_relevance = ReviewScoreCategory.objects.create(
                event=event, name={"en": "Relevance"}, weight=1, required=True
            )
            cat_clarity = ReviewScoreCategory.objects.create(
                event=event, name={"en": "Clarity"}, weight=1, required=True
            )
            for cat in [cat_originality, cat_relevance, cat_clarity]:
                for val, label in [
                    (1, "Poor"),
                    (2, "Fair"),
                    (3, "Good"),
                    (4, "Very Good"),
                    (5, "Excellent"),
                ]:
                    ReviewScore.objects.create(category=cat, value=val, label=label)

        return redirect(event.orga_urls.base)


class EventHistory(Filterable, EventSettingsPermission, ListView):
    template_name = "orga/event/history.html"
    model = ActivityLog
    context_object_name = "log_entries"
    paginate_by = 200
    filter_form_class = EventHistoryFilterForm

    def get_queryset(self):
        qs = ActivityLog.objects.filter(event=self.request.event).select_related(
            "person", "content_type"
        )
        return self.filter_queryset(qs)


class EventHistoryDetail(EventSettingsPermission, DetailView):
    template_name = "orga/event/history_detail.html"
    model = ActivityLog
    context_object_name = "log"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return ActivityLog.objects.filter(event=self.request.event)

    @cached_property
    def is_htmx(self):
        return is_htmx(self.request)

    def get_template_names(self):
        if self.is_htmx:
            return ["orga/event/history_detail_content.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_htmx_request"] = self.is_htmx
        return context


class EventReviewSettings(EventSettingsPermission, FormView):
    form_class = ReviewSettingsForm
    template_name = "orga/settings/review.html"

    def get_success_url(self) -> str:
        return self.request.event.orga_urls.review_settings

    @context
    def tablist(self):
        return {
            "general": _("General information"),
            "scores": _("Review scoring"),
            "phases": _("Review phases"),
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["obj"] = self.request.event
        kwargs["attribute_name"] = "settings"
        kwargs["locales"] = self.request.event.locales
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        try:
            phases = self.save_phases()
            scores = self.save_scores()
        except ValidationError as e:
            messages.error(self.request, e.message)
            return self.get(self.request, *self.args, **self.kwargs)
        if not phases or not scores:
            return self.get(self.request, *self.args, **self.kwargs)
        form.save()
        if self.scores_formset.has_changed():
            recalculate_all_review_scores.apply_async(
                kwargs={"event_id": self.request.event.pk},
                ignore_result=True,
            )
        return super().form_valid(form)

    @context
    @cached_property
    def phases_formset(self):
        formset_class = inlineformset_factory(
            Event,
            ReviewPhase,
            form=ReviewPhaseForm,
            formset=I18nEventFormSet,
            can_delete=True,
            extra=0,
        )
        return formset_class(
            self.request.POST if self.request.method == "POST" else None,
            queryset=ReviewPhase.objects.filter(
                event=self.request.event
            ).select_related("event"),
            event=self.request.event,
            prefix="phase",
        )

    def save_phases(self):
        if not self.phases_formset.is_valid():
            return False

        with transaction.atomic():
            for form in self.phases_formset.initial_forms:
                # Deleting is handled elsewhere, so we skip it here
                if form.has_changed():
                    form.instance.event = self.request.event
                    form.save()

            extra_forms = [
                form
                for form in self.phases_formset.extra_forms
                if form.has_changed
                and not self.phases_formset._should_delete_form(form)
            ]
            for form in extra_forms:
                form.instance.event = self.request.event
                form.save()

            for form in self.phases_formset.deleted_forms:
                form.instance.delete()

            # Now that everything is saved, check for overlapping review phases,
            # and show an error message if any exist. Raise an exception to
            # get out of the transaction.
            review_phases = self.request.event.reorder_review_phases()
            for phase, next_phase in zip(review_phases, review_phases[1:]):
                if not phase.end:
                    raise ValidationError(
                        _("Only the last review phase may be open-ended.")
                    )
                if not next_phase.start:
                    raise ValidationError(
                        _(
                            "All review phases except for the first one need a start date."
                        )
                    )
                if phase.end > next_phase.start:
                    raise ValidationError(
                        _(
                            "The review phases '{phase1}' and '{phase2}' overlap. "
                            "Please make sure that review phases do not overlap, then save again."
                        ).format(phase1=phase.name, phase2=next_phase.name)
                    )
        return True

    @context
    @cached_property
    def scores_formset(self):
        formset_class = inlineformset_factory(
            Event,
            ReviewScoreCategory,
            form=ReviewScoreCategoryForm,
            formset=I18nEventFormSet,
            can_delete=True,
            extra=0,
        )
        return formset_class(
            self.request.POST if self.request.method == "POST" else None,
            queryset=ReviewScoreCategory.objects.filter(event=self.request.event)
            .select_related("event")
            .prefetch_related("scores"),
            event=self.request.event,
            prefix="scores",
        )

    def save_scores(self):
        if not self.scores_formset.is_valid():
            return False
        weights_changed = False
        for form in self.scores_formset.initial_forms:
            # Deleting is handled elsewhere, so we skip it here
            if form.has_changed():
                if "weight" in form.changed_data:
                    weights_changed = True
                form.instance.event = self.request.event
                form.save()

        extra_forms = [
            form
            for form in self.scores_formset.extra_forms
            if form.has_changed and not self.scores_formset._should_delete_form(form)
        ]
        for form in extra_forms:
            form.instance.event = self.request.event
            form.save()

        for form in self.scores_formset.deleted_forms:
            if not form.instance.is_independent:
                weights_changed = True
            if form.instance.pk:
                form.instance.scores.all().delete()
                form.instance.delete()

        if weights_changed:
            ReviewScoreCategory.recalculate_scores(self.request.event)
        return True


class PhaseActivate(EventSettingsPermission, View):

    def get_object(self):
        return get_object_or_404(
            ReviewPhase, event=self.request.event, pk=self.kwargs.get("pk")
        )

    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        phase = self.get_object()
        phase.activate()
        return redirect(self.request.event.orga_urls.review_settings)


class EventMailSettings(EventSettingsPermission, FormView):
    form_class = MailSettingsForm
    template_name = "orga/settings/mail.html"

    def get_success_url(self) -> str:
        return self.request.event.orga_urls.mail_settings

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["obj"] = self.request.event
        kwargs["locales"] = self.request.event.locales
        return kwargs

    @context
    def submit_buttons(self):
        return [
            Button(
                name="test", value="1", label=_("Save and test custom SMTP connection")
            ),
            Button(color="info", icon=None),
        ]

    def form_valid(self, form):
        form.save()

        if self.request.POST.get("test", "0").strip() == "1":
            backend = self.request.event.get_mail_backend(force_custom=True)
            try:
                backend.test(self.request.event.mail_settings["mail_from"])
            except Exception as e:
                messages.warning(
                    self.request,
                    _("An error occurred while contacting the SMTP server: %s")
                    % str(e),
                )
            else:  # pragma: no cover
                if form.cleaned_data.get("smtp_use_custom"):
                    messages.success(
                        self.request,
                        _(
                            "Yay, your changes have been saved and the connection attempt to "
                            "your SMTP server was successful."
                        ),
                    )
                else:
                    messages.success(
                        self.request,
                        _(
                            "We’ve been able to contact the SMTP server you configured. "
                            "Remember to check the “use custom SMTP server” checkbox, "
                            "otherwise your SMTP server will not be used."
                        ),
                    )
        else:
            messages.success(self.request, phrases.base.saved)

        return super().form_valid(form)


class InvitationView(FormView):
    template_name = "orga/invitation.html"
    form_class = UserForm

    @context
    @cached_property
    def invitation(self):
        return get_object_or_404(TeamInvite, token__iexact=self.kwargs.get("code"))

    @context
    def password_reset_link(self):
        return reverse("orga:auth.reset")

    def post(self, *args, **kwargs):
        if not self.request.user.is_anonymous:
            self.accept_invite(self.request.user)
            return redirect(reverse("orga:dashboard"))
        return super().post(*args, **kwargs)

    def form_valid(self, form):
        form.save()
        user = User.objects.filter(pk=form.cleaned_data.get("user_id")).first()
        if not user:
            messages.error(
                self.request,
                _(
                    "There was a problem with your authentication. Please contact the organiser for further help."
                ),
            )
            return redirect(self.request.event.urls.base)

        self.accept_invite(user)
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(reverse("orga:dashboard"))

    @transaction.atomic()
    def accept_invite(self, user):
        invite = self.invitation
        invite.team.members.add(user)
        invite.team.save()
        invite.team.organiser.log_action(
            "imanage.invite.orga.accept", person=user, orga=True
        )
        messages.info(self.request, _("You are now part of the team!"))
        invite.delete()


def condition_plugins(wizard):
    return bool(get_all_plugins_grouped())


class EventWizard(PermissionRequired, SensibleBackWizardMixin, SessionWizardView):
    permission_required = "event.create_event"
    file_storage = FileSystemStorage(location=Path(settings.MEDIA_ROOT) / "new_event")
    form_list = [
        ("initial", EventWizardInitialForm),
        ("basics", EventWizardBasicsForm),
        ("timeline", EventWizardTimelineForm),
        ("display", EventWizardDisplayForm),
        ("plugins", EventWizardPluginForm),
    ]
    condition_dict = {"plugins": condition_plugins}

    def get_template_names(self):
        return [
            f"orga/event/wizard/{self.steps.current}.html",
            "orga/event/wizard/base.html",
        ]

    def get_context_data(self, *args, **kwargs):
        result = super().get_context_data(*args, **kwargs)
        result["submit_buttons"] = [Button(label=_("Next step"), icon=None)]
        if step := result["wizard"]["steps"].prev:
            result["submit_buttons_extra"] = [
                Button(
                    label=_("Previous step"),
                    color="info",
                    name="wizard_goto_step",
                    value=step,
                    icon=None,
                )
            ]
        return result

    @context
    def organiser(self):
        return (
            self.get_cleaned_data_for_step("initial").get("organiser")
            if self.steps.current != "initial"
            else None
        )

    def render(self, form=None, **kwargs):
        if (
            self.steps.current != "initial"
            and self.get_cleaned_data_for_step("initial") is None
        ):
            return self.render_goto_step("initial")
        if self.steps.current == "timeline":
            fdata = self.get_cleaned_data_for_step("basics")
            year = now().year % 100
            if (
                fdata
                and str(year) not in fdata["slug"]
                and str(year + 1) not in fdata["slug"]
            ):
                messages.warning(
                    self.request,
                    str(
                        _(
                            "Please consider including your event’s year in the slug, e.g. myevent{number}."
                        )
                    ).format(number=year),
                )
        elif self.steps.current == "display":
            date_to = self.get_cleaned_data_for_step("timeline").get("date_to")
            if date_to and date_to < now().date():
                messages.warning(
                    self.request,
                    _("Did you really mean to make your event take place in the past?"),
                )
        return super().render(form, **kwargs)

    def get_form_kwargs(self, step=None):
        kwargs = {"user": self.request.user}
        if step != "initial":
            fdata = self.get_cleaned_data_for_step("initial")
            kwargs.update(fdata or {})
        if step in ("display", "plugins"):
            basics_data = self.get_cleaned_data_for_step("basics")
            if basics_data and basics_data.get("copy_from_event"):
                kwargs["copy_from_event"] = basics_data["copy_from_event"]
        return kwargs

    @transaction.atomic()
    def done(self, form_list, *args, **kwargs):
        steps = {}
        for step in ("initial", "basics", "timeline", "display", "plugins"):
            try:
                steps[step] = self.get_cleaned_data_for_step(step)
            except KeyError:
                steps[step] = {}

        with scopes_disabled():
            event = Event.objects.create(
                organiser=steps["initial"]["organiser"],
                locale_array=",".join(steps["initial"]["locales"]),
                content_locale_array=",".join(steps["initial"]["locales"]),
                name=steps["basics"]["name"],
                slug=steps["basics"]["slug"],
                timezone=steps["basics"]["timezone"],
                email=steps["basics"]["email"],
                locale=steps["basics"]["locale"],
                primary_color=steps["display"]["primary_color"],
                logo=steps["display"]["logo"],
                date_from=steps["timeline"]["date_from"],
                date_to=steps["timeline"]["date_to"],
            )
        with scope(event=event):
            deadline = steps["timeline"].get("deadline")
            if deadline:
                event.cfp.deadline = deadline.replace(tzinfo=event.tz)
                event.cfp.save()
            event_changed = False
            for setting in ("header_pattern",):
                if value := steps["display"].get(setting):
                    event.display_settings[setting] = value
                    event_changed = True
            if event_changed:
                event.save(update_fields=["display_settings"])
            if event.logo:
                event.process_image("logo")

        has_control_rights = self.request.user.teams.filter(
            organiser=event.organiser,
            all_events=True,
            can_change_event_settings=True,
            can_change_submissions=True,
        ).exists()
        if not has_control_rights:
            team = Team.objects.create(
                organiser=event.organiser,
                name=_(f"Team {event.name}"),
                can_change_event_settings=True,
                can_change_submissions=True,
            )
            team.members.add(self.request.user)
            team.limit_events.add(event)

        logdata = {}
        for form in form_list:
            logdata.update(form.cleaned_data)
        with scope(event=event):
            event.log_action(
                "imanage.event.create",
                person=self.request.user,
                orga=True,
            )

            copy_from_event = steps["basics"].get("copy_from_event")
            if copy_from_event:
                event.copy_data_from(
                    copy_from_event,
                    skip_attributes=[
                        "locale",
                        "locales",
                        "primary_color",
                        "timezone",
                        "email",
                        "deadline",
                        "plugins",
                    ],
                )

            if steps["plugins"]:
                selected_plugins = steps["plugins"].get("plugins") or []
                event.set_plugins(selected_plugins)
                event.save()

        return redirect(event.orga_urls.base + "?congratulations")


class EventDelete(PermissionRequired, ActionConfirmMixin, TemplateView):
    permission_required = "person.administrator_user"
    model = Event
    action_text = (
        _(
            "ALL related data, such as proposals, and speaker profiles, and "
            "uploads, will also be deleted and cannot be restored."
        )
        + " "
        + phrases.base.delete_warning
    )

    def get_object(self):
        return self.request.event

    def action_object_name(self):
        return ngettext_lazy("Event", "Events", 1) + f": {self.get_object().name}"

    @property
    def action_back_url(self):
        return self.get_object().orga_urls.settings

    def post(self, request, *args, **kwargs):
        self.get_object().shred(person=self.request.user)
        return redirect(reverse("orga:dashboard"))


@method_decorator(csp_update({"script-src": "'self' 'unsafe-eval'"}), name="dispatch")
class WidgetSettings(EventSettingsPermission, FormView):
    form_class = WidgetSettingsForm
    template_name = "orga/settings/widget.html"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, phrases.base.saved)
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["obj"] = self.request.event
        return kwargs

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result["extra_form"] = WidgetGenerationForm(instance=self.request.event)
        result["generate_submit"] = [
            Button(id="generate-widget", _type=None, label=_("Generate widget"))
        ]
        return result

    def get_success_url(self) -> str:
        return self.request.event.orga_urls.widget_settings


# Analytics Export Classes

class BaseExporter:
    """Base class for data exporters."""
    
    content_type = "text/csv"
    filename = "export.csv"
    
    def __init__(self, event):
        self.event = event
    
    def get_data(self):
        """Override this method to return export data."""
        raise NotImplementedError


class AnalyticsCSVExporter(BaseExporter):
    """Export general analytics data to CSV."""
    
    filename = "analytics.csv"
    
    def get_data(self):
        import csv
        import io
        from imanage.event.models import EventMetrics
        from imanage.submission.models import Submission, Review
        from django.db.models import Avg
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Date",
            "Total Submissions",
            "Accepted",
            "Rejected", 
            "Pending",
            "Total Reviews",
            "Avg Review Score",
            "Registered Attendees",
        ])
        
        # Get metrics over time
        metrics = EventMetrics.objects.filter(event=self.event).order_by('date')
        
        for metric in metrics:
            writer.writerow([
                metric.date,
                metric.total_submissions,
                metric.accepted_submissions,
                metric.rejected_submissions,
                metric.pending_submissions,
                metric.total_reviews,
                metric.avg_review_score or 0,
                metric.registered_attendees,
            ])
        
        # If no historical metrics, add current state
        if not metrics.exists():
            submissions = Submission.objects.filter(event=self.event)
            reviews = Review.objects.filter(submission__event=self.event)
            avg_score = reviews.aggregate(Avg('score'))['score__avg'] or 0
            
            writer.writerow([
                "Current",
                submissions.count(),
                submissions.filter(state='accepted').count(),
                submissions.filter(state='rejected').count(),
                submissions.filter(state='submitted').count(),
                reviews.count(),
                round(avg_score, 2),
                self.event.attendee_metrics.count(),
            ])
        
        return output.getvalue()


class AttendeeCSVExporter(BaseExporter):
    """Export attendee list to CSV."""
    
    filename = "attendees.csv"
    
    def get_data(self):
        import csv
        import io
        from imanage.event.models import AttendeeMetrics
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Email",
            "Name",
            "Institution",
            "Country",
            "City",
            "Registered At",
            "Checked In",
            "Papers Submitted",
            "Reviews Completed",
            "Sessions Attended",
            "Last Active",
        ])
        
        # Get attendees
        attendees = AttendeeMetrics.objects.filter(
            event=self.event
        ).select_related('user').order_by('-registered_at')
        
        for attendee in attendees:
            writer.writerow([
                attendee.user.email,
                attendee.user.get_display_name,
                attendee.institution,
                attendee.country,
                attendee.city,
                attendee.registered_at.strftime('%Y-%m-%d %H:%M'),
                'Yes' if attendee.checked_in else 'No',
                attendee.papers_submitted,
                attendee.reviews_completed,
                attendee.sessions_attended,
                attendee.last_active.strftime('%Y-%m-%d %H:%M'),
            ])
        
        return output.getvalue()


class ReviewSummaryCSVExporter(BaseExporter):
    """Export review summary to CSV."""
    
    filename = "review-summary.csv"
    
    def get_data(self):
        import csv
        import io
        from imanage.submission.models import Submission, Review
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Submission Code",
            "Title",
            "State",
            "Total Reviews",
            "Avg Score",
            "Created At",
        ])
        
        # Get submissions with review data
        submissions = Submission.objects.filter(event=self.event).prefetch_related('reviews')
        
        for submission in submissions:
            reviews = submission.reviews.all()
            avg_score = sum(r.score for r in reviews if r.score) / len(reviews) if reviews else 0
            
            writer.writerow([
                submission.code,
                submission.title,
                submission.state,
                reviews.count(),
                round(avg_score, 2) if avg_score else 'N/A',
                submission.created.strftime('%Y-%m-%d'),
            ])
        
        return output.getvalue()


class AnalyticsExportView(EventPermissionRequired, PermissionRequired, View):
    """Export analytics data in various formats."""

    permission_required = "orga.view_orga_area"

    def get(self, request, *args, **kwargs):
        format_type = kwargs.get("format", "csv")
        
        exporters = {
            "csv": AnalyticsCSVExporter,
            "attendees": AttendeeCSVExporter,
            "reviews": ReviewSummaryCSVExporter,
        }
        
        exporter_class = exporters.get(format_type, AnalyticsCSVExporter)
        exporter = exporter_class(request.event)
        
        response = HttpResponse(
            exporter.get_data(),
            content_type=exporter.content_type
        )
        response["Content-Disposition"] = f"attachment; filename=\"{request.event.slug}-{exporter.filename}\""
        
        return response

