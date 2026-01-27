# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.utils.timezone import now
from rest_framework import permissions, viewsets

from imanage.api.documentation import (
    build_search_docs,
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)
from imanage.api.serializers.event import EventListSerializer, EventSerializer
from imanage.api.views.mixins import ImanageViewSetMixin
from imanage.event.models import Event
from imanage.event.rules import get_events_for_user


@extend_schema_view(
    list=extend_schema(
        summary="List Events", 
        parameters=[
            build_search_docs("name"),
            OpenApiParameter(
                name="status",
                description="Filter events by status (active, upcoming, or past)",
                required=False,
                type=str,
                enum=["active", "upcoming", "past"]
            ),
        ], 
        tags=["events"]
    ),
    retrieve=extend_schema(summary="Show Events", tags=["events"]),
)
class EventViewSet(ImanageViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.none()
    lookup_field = "slug"
    lookup_url_kwarg = "event"
    pagination_class = None
    permission_classes = [permissions.AllowAny]
    search_fields = ("name",)
    filterset_fields = ("is_public",)
    ordering_fields = ("date_from", "date_to", "name", "slug")
    ordering = ("-date_from",)

    def get_unversioned_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        return EventSerializer

    def get_queryset(self):
        queryset = get_events_for_user(self.request.user).order_by("-date_from")
        
        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            today = now().date()
            if status == 'active':
                queryset = queryset.filter(date_from__lte=today, date_to__gte=today)
            elif status == 'upcoming':
                queryset = queryset.filter(date_from__gt=today)
            elif status == 'past':
                queryset = queryset.filter(date_to__lt=today)
        
        return queryset
