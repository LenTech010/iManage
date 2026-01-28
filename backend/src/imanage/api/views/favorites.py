# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.db import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from imanage.api.views.mixins import EventPermissionMixin
from imanage.event.models import EventFavourite


class EventFavouriteViewSet(EventPermissionMixin, viewsets.ViewSet):
    """API endpoints for managing event favorites."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list(self, request, event):
        """List all favorite events for the current user."""
        favourites = EventFavourite.objects.filter(
            user=request.user,
            event__is_public=True
        ).select_related('event')
        
        return Response({
            'count': favourites.count(),
            'results': [
                {
                    'event': {
                        'slug': fav.event.slug,
                        'name': str(fav.event.name),
                        'date_from': fav.event.date_from,
                        'date_to': fav.event.date_to,
                        'status': fav.event.get_event_status(),
                    },
                    'created': fav.created,
                }
                for fav in favourites
            ]
        })

    @action(detail=False, methods=['post'])
    def add(self, request, event):
        """Add an event to favorites."""
        try:
            favourite = EventFavourite.objects.create(
                user=request.user,
                event=event
            )
            return Response(
                {
                    'message': 'Event added to favorites',
                    'created': favourite.created
                },
                status=status.HTTP_201_CREATED
            )
        except IntegrityError:
            return Response(
                {'message': 'Event already in favorites'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['delete'])
    def remove(self, request, event):
        """Remove an event from favorites."""
        try:
            favourite = EventFavourite.objects.get(
                user=request.user,
                event=event
            )
            favourite.delete()
            return Response(
                {'message': 'Event removed from favorites'},
                status=status.HTTP_204_NO_CONTENT
            )
        except EventFavourite.DoesNotExist:
            return Response(
                {'message': 'Event not in favorites'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def check(self, request, event):
        """Check if an event is in favorites."""
        is_favorite = EventFavourite.objects.filter(
            user=request.user,
            event=event
        ).exists()
        return Response({'is_favorite': is_favorite})
