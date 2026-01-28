# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

import django_filters

from imanage.submission.models import Answer


class AnswerFilterSet(django_filters.FilterSet):
    question = django_filters.NumberFilter(field_name="question_id")
    submission = django_filters.CharFilter(
        field_name="submission__code",
        lookup_expr="iexact",
    )
    person = django_filters.CharFilter(
        field_name="person__code",
        lookup_expr="iexact",
    )
    review = django_filters.NumberFilter(field_name="review_id")

    class Meta:
        model = Answer
        fields = ("question", "submission", "person", "review")
