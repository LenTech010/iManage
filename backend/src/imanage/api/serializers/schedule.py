# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    DateTimeField,
    SerializerMethodField,
    SlugRelatedField,
)

from imanage.api.documentation import extend_schema_field
from imanage.api.serializers.mixins import ImanageSerializer
from imanage.api.versions import CURRENT_VERSIONS, register_serializer
from imanage.schedule.models import Schedule, TalkSlot


@register_serializer()
class ScheduleListSerializer(FlexFieldsSerializerMixin, ImanageSerializer):
    version = CharField(source="version_with_fallback")

    class Meta:
        model = Schedule
        fields = ["id", "version", "published"]


@register_serializer(versions=CURRENT_VERSIONS)
class ScheduleSerializer(ScheduleListSerializer):
    slots = SerializerMethodField()

    @extend_schema_field(list[int])
    def get_slots(self, obj):
        only_visible_slots = self.context.get("only_visible_slots", True)
        if only_visible_slots and not obj.version:
            # This should never happen, but better safe than sorry.
            return []
        qs = obj.talks.all()
        if only_visible_slots:
            qs = qs.filter(is_visible=True)
        if serializer := self.get_extra_flex_field("slots", qs):
            return serializer.data
        return qs.values_list("pk", flat=True)

    class Meta(ScheduleListSerializer.Meta):
        fields = ScheduleListSerializer.Meta.fields + ["comment", "slots"]
        extra_expandable_fields = {
            "slots": (
                "imanage.api.serializers.schedule.TalkSlotSerializer",
                {"read_only": True, "many": True, "omit": ("schedule",)},
            )
        }


@register_serializer(versions=CURRENT_VERSIONS)
class ScheduleReleaseSerializer(ImanageSerializer):
    version = serializers.CharField(required=True)
    comment = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Schedule
        fields = ("version", "comment")

    def validate_version(self, value):
        event = self.context["request"].event
        if event.schedules.filter(version=value).exists():
            raise ValidationError(
                f"A schedule with the version '{value}' already exists for this event."
            )
        return value


@register_serializer(versions=CURRENT_VERSIONS)
class TalkSlotSerializer(FlexFieldsSerializerMixin, ImanageSerializer):
    submission = SlugRelatedField(slug_field="code", read_only=True)
    end = DateTimeField(source="local_end", required=False)

    class Meta:
        model = TalkSlot
        fields = [
            "id",
            "room",
            "start",
            "end",
            "submission",
            "schedule",
            "description",
            "duration",
        ]
        read_only_fields = ["submission", "schedule"]
        expandable_fields = {
            "submission": (
                "imanage.api.serializers.submission.SubmissionSerializer",
                {"read_only": True, "omit": ("slots",)},
            ),
            "schedule": (
                "imanage.api.serializers.schedule.ScheduleSerializer",
                {"read_only": True, "omit": ("slots", "speakers")},
            ),
            "room": (
                "imanage.api.serializers.room.RoomSerializer",
                {"read_only": True},
            ),
        }


@register_serializer(versions=CURRENT_VERSIONS)
class TalkSlotOrgaSerializer(TalkSlotSerializer):
    class Meta(TalkSlotSerializer.Meta):
        fields = TalkSlotSerializer.Meta.fields + ["is_visible", "slot_type"]
        read_only_fields = TalkSlotSerializer.Meta.read_only_fields + [
            "is_visible",
            "slot_type",
        ]
        expandable_fields = TalkSlotSerializer.Meta.expandable_fields

    def validate_end(self, value):
        if self.instance and self.instance.submission:
            raise ValidationError(
                "End can only be edited if there is no submission associated with the slot. Otherwise, update the submission duration."
            )
        return value

    def validate_description(self, value):
        if self.instance and self.instance.submission:
            raise ValidationError(
                "Description can only be edited if there is no submission associated with the slot. Otherwise, update the submission abstract."
            )
        return value

    def update(self, instance, validated_data):
        from imanage.schedule.tasks import task_update_unreleased_schedule_changes

        result = super().update(instance, validated_data)
        task_update_unreleased_schedule_changes.apply_async(
            kwargs={"event": instance.event.slug}
        )
        return result
