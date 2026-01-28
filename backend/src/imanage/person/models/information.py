# SPDX-FileCopyrightText: 2018-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from i18nfield.fields import I18nCharField, I18nTextField

from imanage.common.models.mixins import ImanageModel
from imanage.common.text.path import path_with_hash
from imanage.common.text.phrases import phrases
from imanage.common.urls import EventUrls
from imanage.event.rules import can_change_event_settings
from imanage.person.rules import can_view_information
from imanage.submission.rules import orga_can_change_submissions


def resource_path(instance, filename):
    return path_with_hash(
        filename, base_path=f"{instance.event.slug}/speaker_information/"
    )


class SpeakerInformation(ImanageModel):
    """Represents any information organisers want to show all or some
    submitters or speakers."""

    event = models.ForeignKey(
        to="event.Event", related_name="information", on_delete=models.CASCADE
    )
    target_group = models.CharField(
        choices=(
            ("submitters", phrases.base.all_choices),
            ("accepted", _("All accepted speakers")),
            ("confirmed", _("Only confirmed speakers")),
        ),
        default="accepted",
        max_length=11,
    )
    limit_tracks = models.ManyToManyField(
        to="submission.Track",
        verbose_name=_("Limit to tracks"),
        blank=True,
        help_text=_("Leave empty to show this information to all tracks."),
    )
    limit_types = models.ManyToManyField(
        to="submission.SubmissionType",
        verbose_name=_("Limit to proposal types"),
        blank=True,
        help_text=_("Leave empty to show this information for all proposal types."),
    )
    title = I18nCharField(
        verbose_name=pgettext_lazy("email subject", "Subject"), max_length=200
    )
    text = I18nTextField(verbose_name=_("Text"), help_text=phrases.base.use_markdown)
    resource = models.FileField(
        verbose_name=_("File"),
        null=True,
        blank=True,
        help_text=_("Please try to keep your upload small, preferably below 16 MB."),
        upload_to=resource_path,
    )

    log_prefix = "imanage.speaker_information"

    @property
    def log_parent(self):
        return self.event

    class orga_urls(EventUrls):
        base = edit = "{self.event.orga_urls.information}{self.pk}/"
        delete = "{base}delete/"

    class Meta:
        rules_permissions = {
            "list": orga_can_change_submissions,
            "view": can_view_information,
            "orga_view": orga_can_change_submissions,
            "create": can_change_event_settings,
            "update": can_change_event_settings,
            "delete": can_change_event_settings,
        }
