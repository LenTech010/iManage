# SPDX-FileCopyrightText: 2020-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from django import forms
from django.utils.translation import gettext_lazy as _

from imanage.common.forms.fields import ColorField
from imanage.common.forms.mixins import ImanageI18nModelForm, ReadOnlyFlag
from imanage.submission.models import Tag


class TagForm(ReadOnlyFlag, ImanageI18nModelForm):
    def __init__(self, *args, event=None, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)

    def clean_tag(self):
        tag = self.cleaned_data["tag"].strip()
        qs = self.event.tags.all()
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if any(tag_obj.tag == tag for tag_obj in qs):
            raise forms.ValidationError(_("You already have a tag by this name!"))
        return tag

    class Meta:
        model = Tag
        fields = ("tag", "description", "color", "is_public")
        field_classes = {
            "color": ColorField,
        }
