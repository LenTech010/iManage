# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django.apps import AppConfig


class ScheduleConfig(AppConfig):
    name = "imanage.schedule"

    def ready(self):
        from . import signals  # noqa
        from .phrases import SchedulePhrases  # noqa
