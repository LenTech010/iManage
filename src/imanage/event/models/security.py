# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.conf import settings
from django.db import models

from imanage.common.models.mixins import ImanageModel


class SecurityAlert(ImanageModel):
    """Track security alerts and suspicious activities."""

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    ALERT_TYPE_CHOICES = [
        ('spam_submission', 'Spam Submission'),
        ('inappropriate_content', 'Inappropriate Content'),
        ('multiple_account_abuse', 'Multiple Account Abuse'),
        ('policy_violation', 'Policy Violation'),
        ('suspicious_login', 'Suspicious Login'),
        ('data_breach_attempt', 'Data Breach Attempt'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_alerts",
        null=True,
        blank=True,
    )
    event = models.ForeignKey(
        to="event.Event",
        on_delete=models.CASCADE,
        related_name="security_alerts",
        null=True,
        blank=True,
    )
    alert_type = models.CharField(
        max_length=50,
        choices=ALERT_TYPE_CHOICES,
        default='other',
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='medium',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
    )
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    resolved_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_security_alerts",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['user', 'alert_type']),
        ]

    def __str__(self):
        target = self.user or self.event or "System"
        return f"{self.get_alert_type_display()} - {target} ({self.severity})"


class ModerationLog(ImanageModel):
    """Log of moderation actions taken by admins."""

    ACTION_CHOICES = [
        ('account_suspended', 'Account Suspended'),
        ('account_removed', 'Account Removed'),
        ('account_reinstated', 'Account Reinstated'),
        ('content_removed', 'Content Removed'),
        ('content_flagged', 'Content Flagged'),
        ('warning_issued', 'Warning Issued'),
        ('ban_issued', 'Ban Issued'),
        ('ban_lifted', 'Ban Lifted'),
    ]

    moderator = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderation_actions",
    )
    target_user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="moderation_logs",
        null=True,
        blank=True,
    )
    event = models.ForeignKey(
        to="event.Event",
        on_delete=models.CASCADE,
        related_name="moderation_logs",
        null=True,
        blank=True,
    )
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
    )
    reason = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    related_alert = models.ForeignKey(
        to=SecurityAlert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_logs",
    )

    class Meta:
        ordering = ['-created']

    def __str__(self):
        target = self.target_user or self.event or "Unknown"
        return f"{self.get_action_display()} - {target} by {self.moderator}"
