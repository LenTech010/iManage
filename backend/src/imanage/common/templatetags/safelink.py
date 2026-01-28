# SPDX-FileCopyrightText: 2024-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django import template

from imanage.common.views.redirect import safelink as sl

register = template.Library()


@register.simple_tag
def safelink(url):
    return sl(url)
