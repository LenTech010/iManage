# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from rest_framework import viewsets

from imanage.api.documentation import (
    build_search_docs,
    extend_schema,
    extend_schema_view,
)
from imanage.api.serializers.mail import MailTemplateSerializer
from imanage.api.views.mixins import ActivityLogMixin, ImanageViewSetMixin
from imanage.mail.models import MailTemplate


@extend_schema_view(
    list=extend_schema(
        summary="List Mail Templates", parameters=[build_search_docs("role", "subject")]
    ),
    retrieve=extend_schema(summary="Show Mail Template"),
    create=extend_schema(summary="Create Mail Template"),
    update=extend_schema(summary="Update Mail Template"),
    partial_update=extend_schema(summary="Update Mail Template (Partial Update)"),
    destroy=extend_schema(summary="Delete Mail Template"),
)
class MailTemplateViewSet(ActivityLogMixin, ImanageViewSetMixin, viewsets.ModelViewSet):
    serializer_class = MailTemplateSerializer
    queryset = MailTemplate.objects.none()
    endpoint = "mail-templates"
    search_fields = ("role", "subject")
    ordering_fields = ("id", "subject")
    ordering = ("id",)

    def get_queryset(self):
        return self.event.mail_templates.all().select_related("event").order_by("pk")
