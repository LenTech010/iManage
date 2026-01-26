# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from contextlib import suppress

from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = "imanage.common"

    def ready(self):
        from . import checks  # noqa
        from . import log_display  # noqa
        from . import signals  # noqa
        from . import update_check  # noqa


with suppress(ImportError):
    from imanage import celery_app as celery  # NOQA
