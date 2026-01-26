# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

"""WSGI config for imanage.

Use with gunicorn or uwsgi.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imanage.settings")

from django.core.wsgi import get_wsgi_application  # NOQA

application = get_wsgi_application()
