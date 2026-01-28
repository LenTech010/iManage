# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from imanage.api.views.mixins import EventPermissionMixin
from imanage.event.models import Notification


class NotificationViewSet(EventPermissionMixin, viewsets.ViewSet):
    """API endpoints for managing user notifications."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list(self, request, event=None):
        """List all notifications for the current user."""
        notifications = Notification.objects.filter(user=request.user)
        
        if event:
            notifications = notifications.filter(event=event)
        
        # Filter by read/unread if specified
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            notifications = notifications.filter(is_read=is_read.lower() == 'true')
        
        notifications = notifications.order_by('-created')[:50]  # Limit to 50 most recent
        
        return Response({
            'count': notifications.count(),
            'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
            'results': [
                {
                    'id': notif.id,
                    'title': notif.title,
                    'message': notif.message,
                    'notification_type': notif.notification_type,
                    'is_read': notif.is_read,
                    'created': notif.created,
                    'read_at': notif.read_at,
                    'action_url': notif.action_url,
                    'action_text': notif.action_text,
                    'event': {
                        'slug': notif.event.slug,
                        'name': str(notif.event.name)
                    } if notif.event else None,
                }
                for notif in notifications
            ]
        })

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None, event=None):
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(
                pk=pk,
                user=request.user
            )
            notification.mark_as_read()
            return Response(
                {'message': 'Notification marked as read'},
                status=status.HTTP_200_OK
            )
        except Notification.DoesNotExist:
            return Response(
                {'message': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request, event=None):
        """Mark all notifications as read."""
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        
        if event:
            notifications = notifications.filter(event=event)
        
        count = notifications.count()
        for notif in notifications:
            notif.mark_as_read()
        
        return Response(
            {'message': f'{count} notifications marked as read'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['delete'])
    def delete(self, request, pk=None, event=None):
        """Delete a notification."""
        try:
            notification = Notification.objects.get(
                pk=pk,
                user=request.user
            )
            notification.delete()
            return Response(
                {'message': 'Notification deleted'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Notification.DoesNotExist:
            return Response(
                {'message': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
