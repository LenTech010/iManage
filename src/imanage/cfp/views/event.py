# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms
#
# This file contains Apache-2.0 licensed contributions copyrighted by the following contributors:
# SPDX-FileContributor: Raphael Michel

import logging
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import TemplateView
from django_context_decorator import context
from django_scopes import scopes_disabled

from imanage.common.views.mixins import PermissionRequired
from imanage.event.models import Event
from imanage.event.rules import get_events_for_user

logger = logging.getLogger(__name__)


class EventPageMixin(PermissionRequired):
    permission_required = "event.view_event"

    def get_permission_object(self):
        return getattr(self.request, "event", None)


# check login first, then permission so users get redirected to /login, if they are missing one
class LoggedInEventPageMixin(LoginRequiredMixin, EventPageMixin):
    def get_login_url(self) -> str:
        return reverse("cfp:event.login", kwargs={"event": self.request.event.slug})


class EventStartpage(EventPageMixin, TemplateView):
    template_name = "cfp/event/index.html"

    @context
    def has_submissions(self):
        return (
            not self.request.user.is_anonymous
            and self.request.event.submissions.filter(
                speakers__in=[self.request.user]
            ).exists()
        )

    @context
    def has_featured(self):
        return self.request.event.submissions.filter(is_featured=True).exists()

    @context
    def submit_qs(self):
        params = [
            (key, self.request.GET.get(key))
            for key in ("track", "submission_type", "access_code")
            if self.request.GET.get(key) is not None
        ]
        return f"?{urlencode(params)}" if params else ""

    @context
    def access_code(self):
        code = self.request.GET.get("access_code")
        if code:
            return self.request.event.submitter_access_codes.filter(
                code__iexact=code
            ).first()


class EventCfP(EventStartpage):
    template_name = "cfp/event/cfp.html"

    @context
    def has_featured(self):
        return self.request.event.submissions.filter(is_featured=True).exists()


class GeneralView(TemplateView):
    template_name = "cfp/index.html"

    def dispatch(self, request, *args, **kwargs):
        # Removed automatic redirect to dashboard - users should be able to
        # access the home page even if they have management permissions
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        _now = now().date()
        if self.request.uses_custom_domain:
            qs = Event.objects.filter(custom_domain=f"https://{self.request.host}")
        else:
            qs = Event.objects.filter(custom_domain__isnull=True)
        qs = get_events_for_user(self.request.user, qs).distinct()

        # Add proper sorting by date (most recent first)
        qs = qs.order_by("-date_from")

        # Get managed events for authenticated users
        my_managed_events_qs = None
        if self.request.user.is_authenticated:
            with scopes_disabled():
                my_managed_events_qs = self.request.user.get_events_with_any_permission()
                if self.request.uses_custom_domain:
                    my_managed_events_qs = my_managed_events_qs.filter(
                        custom_domain=f"https://{self.request.host}"
                    )
                else:
                    my_managed_events_qs = my_managed_events_qs.filter(
                        custom_domain__isnull=True
                    )
                my_managed_events_qs = my_managed_events_qs.distinct().order_by("-date_from")

        result["current_events"] = []
        result["past_events"] = []
        result["future_events"] = []
        result["my_managed_current"] = []
        result["my_managed_past"] = []
        result["my_managed_future"] = []
        
        for event in qs:
            try:
                # Add error handling for events with missing or invalid date fields
                if not event.date_from or not event.date_to:
                    logger.warning(f"Event {event.slug} is missing date fields.")
                    continue

                # Add filtering to exclude non-public events for non-authenticated users
                if not self.request.user.is_authenticated and not event.is_public:
                    continue

                # Safety check for URL generation
                try:
                    event.urls.base
                    if self.request.user.is_authenticated:
                        event.orga_urls.base
                except Exception as e:
                    logger.error(f"Error generating URLs for event {event.slug}: {e}")
                    continue

                event.display_badge = "Active" if event.date_from <= _now <= event.date_to else "Upcoming" if event.date_from > _now else "Past"
                event.display_badge_color = "success" if event.date_from <= _now <= event.date_to else "primary" if event.date_from > _now else "secondary"

                if event.date_from <= _now <= event.date_to:
                    result["current_events"].append(event)
                elif event.date_to < _now:
                    result["past_events"].append(event)
                else:
                    result["future_events"].append(event)
            except Exception as e:
                logger.exception(f"Unexpected error processing event {event.slug}: {e}")
        
        # Process managed events separately
        if my_managed_events_qs is not None:
            for event in my_managed_events_qs:
                try:
                    # Add error handling for events with missing or invalid date fields
                    if not event.date_from or not event.date_to:
                        logger.warning(f"Event {event.slug} is missing date fields.")
                        continue

                    # Safety check for URL generation
                    try:
                        event.urls.base
                        event.orga_urls.base
                    except Exception as e:
                        logger.error(f"Error generating URLs for event {event.slug}: {e}")
                        continue

                    event.display_badge = "Active" if event.date_from <= _now <= event.date_to else "Upcoming" if event.date_from > _now else "Past"
                    event.display_badge_color = "success" if event.date_from <= _now <= event.date_to else "primary" if event.date_from > _now else "secondary"

                    if event.date_from <= _now <= event.date_to:
                        result["my_managed_current"].append(event)
                    elif event.date_to < _now:
                        result["my_managed_past"].append(event)
                    else:
                        result["my_managed_future"].append(event)
                except Exception as e:
                    logger.exception(f"Unexpected error processing managed event {event.slug}: {e}")
        
        return result
