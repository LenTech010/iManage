# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

import json

import pytest
from django.conf import settings

from imanage.api.versions import CURRENT_VERSION


@pytest.mark.django_db
def test_api_root_returns_metadata(client):
    response = client.get("/api/")
    content = json.loads(response.text)

    assert response.status_code == 200
    assert content["name"] == "imanage"
    assert content["version"] == settings.IMANAGE_VERSION
    assert content["api_version"] == CURRENT_VERSION
    assert content["urls"]["events"] == settings.SITE_URL + "/api/events/"
