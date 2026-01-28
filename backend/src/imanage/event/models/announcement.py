# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.conf import settings
from django.db import models
from django_scopes import ScopedManager
from i18nfield.fields import I18nCharField, I18nTextField

from imanage.common.models.mixins import ImanageModel


class Announcement(ImanageModel):
    """Direct announcements from organizers to participants."""

    event = models.ForeignKey(
        to="Event",
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="announcements",
    )
    title = I18nCharField(max_length=200)
    message = I18nTextField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    send_email = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    
    # Target audience options
    TARGET_CHOICES = [
        ('all', 'All participants'),
        ('speakers', 'Speakers only'),
        ('reviewers', 'Reviewers only'),
        ('attendees', 'Registered attendees'),
    ]
    target_audience = models.CharField(
        max_length=20,
        choices=TARGET_CHOICES,
        default='all',
    )

    objects = ScopedManager(event="event")

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.title} ({self.event})"
