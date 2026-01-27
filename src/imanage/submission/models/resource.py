# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

import hashlib
from contextlib import suppress
from pathlib import Path

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_scopes import ScopedManager

from imanage.common.models.mixins import ImanageModel
from imanage.common.text.path import path_with_hash
from imanage.common.urls import get_base_url


def resource_path(instance, filename):
    base_path = f"{instance.submission.event.slug}/submissions/{instance.submission.code}/resources/"
    return path_with_hash(filename, base_path=base_path)


class Resource(ImanageModel):
    """Resources are file uploads belonging to a :class:`~imanage.submission.models.submission.Submission`."""

    log_prefix = "imanage.submission.resource"

    submission = models.ForeignKey(
        to="submission.Submission", related_name="resources", on_delete=models.PROTECT
    )
    resource = models.FileField(
        verbose_name=_("File"),
        upload_to=resource_path,
        null=True,
        blank=True,
    )
    link = models.URLField(max_length=400, verbose_name=_("URL"), null=True, blank=True)
    description = models.CharField(
        null=True, blank=True, max_length=1000, verbose_name=_("Description")
    )
    is_public = models.BooleanField(
        default=True, verbose_name=_("Publicly visible resource")
    )
    
    # Security fields for file integrity
    file_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name=_("File hash (SHA-256)"),
        help_text=_("SHA-256 hash of the file for integrity verification")
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_("File size in bytes")
    )
    mime_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("MIME type")
    )

    objects = ScopedManager(event="submission__event")

    class Meta:
        verbose_name_plural = _("Resources")  # Used to display submission log entries

    def __str__(self):
        """Help when debugging."""
        return f"Resource(event={self.submission.event.slug}, submission={self.submission.title})"
    
    def save(self, *args, **kwargs):
        """Calculate file hash and size on save."""
        if self.resource and not self.file_hash:
            # Calculate SHA-256 hash
            self.resource.seek(0)
            file_hash = hashlib.sha256()
            for chunk in self.resource.chunks():
                file_hash.update(chunk)
            self.file_hash = file_hash.hexdigest()
            
            # Get file size
            self.resource.seek(0, 2)  # Seek to end
            self.file_size = self.resource.tell()
            self.resource.seek(0)  # Reset to beginning
            
            # Get MIME type from content_type if available
            self.mime_type = getattr(self.resource, 'content_type', None)
        
        super().save(*args, **kwargs)
    
    def verify_integrity(self):
        """Verify the file integrity by recalculating the hash."""
        if not self.resource or not self.file_hash:
            return True
        
        self.resource.seek(0)
        file_hash = hashlib.sha256()
        for chunk in self.resource.chunks():
            file_hash.update(chunk)
        calculated_hash = file_hash.hexdigest()
        self.resource.seek(0)
        
        return calculated_hash == self.file_hash

    @cached_property
    def url(self):
        if self.link:
            return self.link
        with suppress(ValueError):
            url = getattr(self.resource, "url", None)
            if url:
                base_url = get_base_url(self.submission.event)
                return base_url + url

    @cached_property
    def filename(self):
        with suppress(ValueError):
            if self.resource:
                return Path(self.resource.name).name
