# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.conf import settings
from django.db import models
from django_scopes import ScopedManager

from imanage.common.models.mixins import ImanageModel


class Notification(ImanageModel):
    """Real-time notifications for users about platform activities."""

    NOTIFICATION_TYPE_CHOICES = [
        ('submission_accepted', 'Submission Accepted'),
        ('submission_rejected', 'Submission Rejected'),
        ('review_assigned', 'Review Assigned'),
        ('review_deadline', 'Review Deadline Approaching'),
        ('schedule_change', 'Schedule Change'),
        ('event_announcement', 'Event Announcement'),
        ('event_cancelled', 'Event Cancelled'),
        ('event_reminder', 'Event Reminder'),
        ('message_received', 'Message Received'),
        ('system_update', 'System Update'),
    ]

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    event = models.ForeignKey(
        to="Event",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Optional link for "View More" action
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=50, blank=True, default="View More")
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    objects = ScopedManager(event="event", _manager_class=models.Manager)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['event', 'notification_type']),
        ]

    def __str__(self):
        return f"{self.title} for {self.user}"

    def mark_as_read(self):
        """Mark the notification as read."""
        from django.utils.timezone import now
        if not self.is_read:
            self.is_read = True
            self.read_at = now()
            self.save(update_fields=['is_read', 'read_at'])
