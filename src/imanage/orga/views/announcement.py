# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django_context_decorator import context

from imanage.common.views.mixins import EventPermissionRequired, PermissionRequired
from imanage.event.models import Announcement
from imanage.mail.models import QueuedMail


class AnnouncementListView(EventPermissionRequired, PermissionRequired, ListView):
    """List all announcements for an event."""

    template_name = "orga/announcement/list.html"
    permission_required = "orga.view_orga_area"
    model = Announcement
    context_object_name = "announcements"
    paginate_by = 20

    def get_queryset(self):
        return Announcement.objects.filter(event=self.request.event).order_by('-created')


class AnnouncementCreateView(EventPermissionRequired, PermissionRequired, CreateView):
    """Create a new announcement."""

    template_name = "orga/announcement/form.html"
    permission_required = "orga.change_settings"
    model = Announcement
    fields = ['title', 'message', 'target_audience', 'send_email']

    def form_valid(self, form):
        form.instance.event = self.request.event
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        messages.success(self.request, _("Announcement created successfully."))
        return response

    def get_success_url(self):
        return self.request.event.orga_urls.announcements


class AnnouncementUpdateView(EventPermissionRequired, PermissionRequired, UpdateView):
    """Update an existing announcement."""

    template_name = "orga/announcement/form.html"
    permission_required = "orga.change_settings"
    model = Announcement
    fields = ['title', 'message', 'target_audience', 'send_email', 'is_published']

    def get_queryset(self):
        return Announcement.objects.filter(event=self.request.event)

    def form_valid(self, form):
        # If publishing for the first time, set published_at
        if form.instance.is_published and not form.instance.published_at:
            form.instance.published_at = now()
            
            # Send email if requested and not already sent
            if form.instance.send_email and not form.instance.email_sent:
                self._send_announcement_emails(form.instance)
                form.instance.email_sent = True
        
        response = super().form_valid(form)
        messages.success(self.request, _("Announcement updated successfully."))
        return response

    def _send_announcement_emails(self, announcement):
        """Send announcement emails to target audience."""
        recipients = self._get_recipients(announcement)
        
        for email in recipients:
            QueuedMail.objects.create(
                event=self.request.event,
                to=email,
                subject=f"[{self.request.event.name}] {announcement.title}",
                text=str(announcement.message),
                locale=self.request.event.locale,
            )
        
        messages.info(self.request, _("Announcement email queued for %(count)d recipients.") % {'count': len(recipients)})

    def _get_recipients(self, announcement):
        """Get recipient emails based on target audience."""
        recipients = set()
        
        if announcement.target_audience == 'all' or announcement.target_audience == 'speakers':
            # Add all speakers
            recipients.update(
                self.request.event.submitters.values_list('email', flat=True)
            )
        
        if announcement.target_audience == 'all' or announcement.target_audience == 'reviewers':
            # Add all reviewers
            from imanage.submission.models import Review
            reviewers = Review.objects.filter(
                submission__event=self.request.event
            ).values_list('user__email', flat=True).distinct()
            recipients.update(reviewers)
        
        if announcement.target_audience == 'all' or announcement.target_audience == 'attendees':
            # Add registered attendees
            from imanage.event.models import AttendeeMetrics
            attendees = AttendeeMetrics.objects.filter(
                event=self.request.event
            ).values_list('user__email', flat=True)
            recipients.update(attendees)
        
        return {email for email in recipients if email}

    def get_success_url(self):
        return self.request.event.orga_urls.announcements


class AnnouncementDeleteView(EventPermissionRequired, PermissionRequired, DeleteView):
    """Delete an announcement."""

    template_name = "orga/announcement/delete.html"
    permission_required = "orga.change_settings"
    model = Announcement

    def get_queryset(self):
        return Announcement.objects.filter(event=self.request.event)

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Announcement deleted successfully."))
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.event.orga_urls.announcements


class AnnouncementPublishView(EventPermissionRequired, PermissionRequired, UpdateView):
    """Publish an announcement and optionally send emails."""

    permission_required = "orga.change_settings"
    model = Announcement
    fields = []

    def get_queryset(self):
        return Announcement.objects.filter(event=self.request.event)

    def post(self, request, *args, **kwargs):
        announcement = self.get_object()
        
        if not announcement.is_published:
            announcement.is_published = True
            announcement.published_at = now()
            
            # Send email if configured
            if announcement.send_email and not announcement.email_sent:
                update_view = AnnouncementUpdateView()
                update_view.request = request
                update_view._send_announcement_emails(announcement)
                announcement.email_sent = True
            
            announcement.save()
            messages.success(request, _("Announcement published successfully."))
        else:
            messages.info(request, _("Announcement was already published."))
        
        return redirect(self.request.event.orga_urls.announcements)
