# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView, CreateView
from django_context_decorator import context

from imanage.common.views.mixins import PermissionRequired
from imanage.event.models import SecurityAlert, ModerationLog
from imanage.person.models import User


class SecurityDashboardView(PermissionRequired, ListView):
    """Security and moderation dashboard for admins."""

    template_name = "orga/security/dashboard.html"
    permission_required = "person.is_administrator"
    model = SecurityAlert
    context_object_name = "alerts"
    paginate_by = 50

    def get_queryset(self):
        queryset = SecurityAlert.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by severity
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by alert type
        alert_type = self.request.GET.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        return queryset.order_by('-created')

    @context
    def alert_stats(self):
        """Get statistics about security alerts."""
        alerts = SecurityAlert.objects.all()
        
        return {
            'total': alerts.count(),
            'open': alerts.filter(status='open').count(),
            'critical': alerts.filter(severity='critical').count(),
            'high': alerts.filter(severity='high').count(),
            'resolved_today': alerts.filter(
                status='resolved',
                resolved_at__date=now().date()
            ).count(),
        }

    @context
    def recent_moderation_logs(self):
        """Get recent moderation actions."""
        return ModerationLog.objects.all().order_by('-created')[:10]


class SecurityAlertDetailView(PermissionRequired, DetailView):
    """View details of a security alert."""

    template_name = "orga/security/alert_detail.html"
    permission_required = "person.is_administrator"
    model = SecurityAlert
    context_object_name = "alert"

    @context
    def related_logs(self):
        """Get moderation logs related to this alert."""
        return ModerationLog.objects.filter(
            related_alert=self.object
        ).order_by('-created')


class SecurityAlertResolveView(PermissionRequired, DetailView):
    """Resolve a security alert."""

    permission_required = "person.is_administrator"
    model = SecurityAlert

    def post(self, request, *args, **kwargs):
        alert = self.get_object()
        resolution_notes = request.POST.get('resolution_notes', '')
        
        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.resolved_at = now()
        alert.resolution_notes = resolution_notes
        alert.save()
        
        messages.success(request, _("Security alert resolved successfully."))
        return redirect('orga:security.dashboard')


class UserSuspendView(PermissionRequired, DetailView):
    """Suspend a user account."""

    permission_required = "person.is_administrator"
    model = User

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        reason = request.POST.get('reason', '')
        alert_id = request.POST.get('alert_id')
        
        # Mark user as inactive (suspend)
        user.is_active = False
        user.save()
        
        # Create moderation log
        related_alert = None
        if alert_id:
            related_alert = get_object_or_404(SecurityAlert, pk=alert_id)
        
        ModerationLog.objects.create(
            moderator=request.user,
            target_user=user,
            action='account_suspended',
            reason=reason,
            related_alert=related_alert,
            details={'suspended_at': str(now())}
        )
        
        messages.success(request, _("User %(email)s has been suspended.") % {'email': user.email})
        return redirect('orga:security.dashboard')


class UserReinstateView(PermissionRequired, DetailView):
    """Reinstate a suspended user account."""

    permission_required = "person.is_administrator"
    model = User

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        reason = request.POST.get('reason', '')
        
        # Reactivate user
        user.is_active = True
        user.save()
        
        # Create moderation log
        ModerationLog.objects.create(
            moderator=request.user,
            target_user=user,
            action='account_reinstated',
            reason=reason,
            details={'reinstated_at': str(now())}
        )
        
        messages.success(request, _("User %(email)s has been reinstated.") % {'email': user.email})
        return redirect('orga:security.dashboard')


class FlaggedUsersListView(PermissionRequired, ListView):
    """List users that have been flagged for suspicious activity."""

    template_name = "orga/security/flagged_users.html"
    permission_required = "person.is_administrator"
    model = User
    context_object_name = "users"
    paginate_by = 50

    def get_queryset(self):
        # Get users with open security alerts
        flagged_user_ids = SecurityAlert.objects.filter(
            status__in=['open', 'investigating'],
            user__isnull=False
        ).values_list('user_id', flat=True).distinct()
        
        return User.objects.filter(id__in=flagged_user_ids)

    @context
    def get_user_alerts(self):
        """Get alerts for each user."""
        user_alerts = {}
        for user in self.get_queryset():
            user_alerts[user.id] = SecurityAlert.objects.filter(
                user=user,
                status__in=['open', 'investigating']
            ).order_by('-created')
        return user_alerts


class ModerationLogListView(PermissionRequired, ListView):
    """List all moderation logs."""

    template_name = "orga/security/moderation_logs.html"
    permission_required = "person.is_administrator"
    model = ModerationLog
    context_object_name = "logs"
    paginate_by = 100

    def get_queryset(self):
        queryset = ModerationLog.objects.all()
        
        # Filter by action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by moderator
        moderator_id = self.request.GET.get('moderator')
        if moderator_id:
            queryset = queryset.filter(moderator_id=moderator_id)
        
        return queryset.order_by('-created')
