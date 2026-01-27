# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.conf import settings
from django.db import models
from django_scopes import ScopedManager

from imanage.common.models.mixins import ImanageModel


class EventFavourite(ImanageModel):
    """Allows users to favorite events for easy access and notifications."""

    event = models.ForeignKey(
        to="Event",
        on_delete=models.CASCADE,
        related_name="favourites",
    )
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_favourites",
    )

    objects = ScopedManager(event="event")

    class Meta:
        unique_together = [["user", "event"]]

    def __str__(self):
        return f"{self.user} ♥ {self.event}"
