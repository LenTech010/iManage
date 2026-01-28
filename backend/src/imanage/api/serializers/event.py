# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from contextlib import suppress

from rest_framework.serializers import ModelSerializer, SerializerMethodField

from imanage.api.serializers.fields import UploadedFileField
from imanage.api.versions import register_serializer
from imanage.event.models import Event


@register_serializer()
class EventListSerializer(ModelSerializer):
    status = SerializerMethodField()
    is_active = SerializerMethodField()
    favourite_count = SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            "name",
            "slug",
            "is_public",
            "date_from",
            "date_to",
            "timezone",
            "status",
            "is_active",
            "favourite_count",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        with suppress(Exception):
            if not request or not request.user or not request.user.is_authenticated:
                # Keep API docs small; doesn't matter for validation with unauthenticated
                # users.
                self.fields["timezone"].choices = []
    
    def get_status(self, obj):
        """Get the event status: active, upcoming, or past."""
        return obj.get_event_status()
    
    def get_is_active(self, obj):
        """Check if the event is currently active."""
        return obj.is_active
    
    def get_favourite_count(self, obj):
        """Get the number of users who have favourited this event."""
        return obj.favourites.count()


@register_serializer()
class EventSerializer(EventListSerializer):
    logo = UploadedFileField(required=False)

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + [
            "email",  # Email is public in the footer anyway
            "primary_color",
            "custom_domain",
            "logo",
            "header_image",
            "locale",
            "locales",
            "content_locales",
        ]
