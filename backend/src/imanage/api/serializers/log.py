# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from imanage.api.serializers.mixins import ImanageSerializer
from imanage.api.versions import CURRENT_VERSIONS, register_serializer
from imanage.common.models import ActivityLog
from imanage.person.models import User


class UserSerializer(ImanageSerializer):
    class Meta:
        model = User
        fields = ("code", "name")


@register_serializer(versions=CURRENT_VERSIONS)
class ActivityLogSerializer(ImanageSerializer):
    person = UserSerializer()

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "timestamp",
            "action_type",
            "is_orga_action",
            "person",
            "display",
            "data",
        ]
