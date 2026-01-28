# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.db import models
from django_scopes import ScopedManager

from imanage.common.models.mixins import ImanageModel


class EventMetrics(ImanageModel):
    """Aggregated metrics for events, tracked over time."""

    event = models.ForeignKey(
        to="Event",
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    date = models.DateField(auto_now_add=True)
    
    # Submission metrics
    total_submissions = models.IntegerField(default=0)
    accepted_submissions = models.IntegerField(default=0)
    rejected_submissions = models.IntegerField(default=0)
    pending_submissions = models.IntegerField(default=0)
    
    # Review metrics
    total_reviews = models.IntegerField(default=0)
    avg_review_score = models.FloatField(null=True, blank=True)
    avg_review_turnaround_days = models.FloatField(null=True, blank=True)
    
    # Attendee metrics
    registered_attendees = models.IntegerField(default=0)
    active_attendees = models.IntegerField(default=0)
    
    # Engagement metrics
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)

    objects = ScopedManager(event="event")

    class Meta:
        unique_together = [['event', 'date']]
        ordering = ['-date']

    def __str__(self):
        return f"Metrics for {self.event} on {self.date}"


class AttendeeMetrics(ImanageModel):
    """Detailed metrics about individual attendees."""

    event = models.ForeignKey(
        to="Event",
        on_delete=models.CASCADE,
        related_name="attendee_metrics",
    )
    user = models.ForeignKey(
        to="person.User",
        on_delete=models.CASCADE,
        related_name="attendee_metrics",
    )
    
    # Demographic information (optional)
    institution = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Engagement metrics
    sessions_attended = models.IntegerField(default=0)
    papers_submitted = models.IntegerField(default=0)
    reviews_completed = models.IntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)
    
    # Registration details
    registered_at = models.DateTimeField(auto_now_add=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    objects = ScopedManager(event="event")

    class Meta:
        unique_together = [['event', 'user']]

    def __str__(self):
        return f"Attendee metrics for {self.user} at {self.event}"
