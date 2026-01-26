# SPDX-FileCopyrightText: 2017-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

import string

from django.dispatch import receiver
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy as _n

from imanage.common.models.log import ActivityLog
from imanage.common.signals import activitylog_display, activitylog_object_link
from imanage.common.text.phrases import phrases
from imanage.event.models.event import Event
from imanage.mail.models import MailTemplate, QueuedMail
from imanage.person.models import SpeakerProfile
from imanage.submission.models import (
    Answer,
    AnswerOption,
    CfP,
    Question,
    Review,
    Submission,
    SubmissionComment,
    SubmissionStates,
)

# Usually, we don't have to include the object name in activity log
# strings, because we use ActivityLog.content_object to get the object
# and display it above the message. However, in some cases, like when
# we log the deletion of an object, we don't have the object anymore,
# so we'll want to format the message instead.
TEMPLATE_LOG_NAMES = {
    "imanage.event.delete": _("The event {name} ({slug}) by {organiser} was deleted."),
    "imanage.organiser.delete": _("The organiser {name} was deleted."),
    "imanage.submission.invitation.send": _(
        "A speaker invitation was sent to {email}."
    ),
    "imanage.submission.invitation.accept": _(
        "A speaker invitation to {email} was accepted."
    ),
    "imanage.submission.invitation.retract": _(
        "A speaker invitation to {email} was retracted."
    ),
}

# These log names were used in the past, and we still support them for display purposes
LOG_ALIASES = {
    "imanage.event.invite.orga.accept": "imanage.invite.orga.accept",
    "imanage.event.invite.orga.retract": "imanage.invite.orga.retract",
    "imanage.event.invite.orga.send": "imanage.invite.orga.send",
    "imanage.event.invite.reviewer.retract": "imanage.invite.reviewer.retract",
    "imanage.event.invite.reviewer.send": "imanage.invite.reviewer.send",
    "imanage.submission.confirmation": "imanage.submission.confirm",
    "imanage.submission.answerupdate": "imanage.submission.answer.update",
    "imanage.submission.answercreate": "imanage.submission.answer.create",
    # This isn't really the same thing, as the create takes place when the submission is
    # created, e.g. as a draft proposal, and the make_submitted takes place when the submission
    # is submitted to the CfP. But as we treat draft proposals as not existing at all
    # yet, we can treat this as a create action.
    "imanage.submission.make_submitted": "imanage.submission.create",
}

LOG_NAMES = {
    "imanage.cfp.update": _("The CfP has been modified."),
    "imanage.event.create": _("The event has been added."),
    "imanage.event.update": _("The event was modified."),
    "imanage.event.activate": _("The event was made public."),
    "imanage.event.deactivate": _("The event was deactivated."),
    "imanage.event.plugins.enabled": _("A plugin was enabled."),
    "imanage.event.plugins.disabled": _("A plugin was disabled."),
    "imanage.invite.orga.accept": _("The invitation to the event orga was accepted."),
    "imanage.invite.orga.retract": _("An invitation to the event orga was retracted."),
    "imanage.invite.orga.send": _("An invitation to the event orga was sent."),
    "imanage.invite.reviewer.retract": _(
        "The invitation to the review team was retracted."
    ),
    "imanage.invite.reviewer.send": _("The invitation to the review team was sent."),
    "imanage.team.member.remove": _("A team member was removed"),
    "imanage.mail.create": _("An email was created."),
    "imanage.mail.delete": _("A pending email was deleted."),
    "imanage.mail.delete_all": _("All pending emails were deleted."),
    "imanage.mail.sent": _("An email was sent."),
    "imanage.mail.update": _("An email was modified."),
    "imanage.mail_template.create": _("A mail template was added."),
    "imanage.mail_template.delete": _("A mail template was deleted."),
    "imanage.mail_template.update": _("A mail template was modified."),
    "imanage.question.create": _("A custom field was added."),
    "imanage.question.delete": _("A custom field was deleted."),
    "imanage.question.update": _("A custom field was modified."),
    "imanage.question.option.create": _("A custom field option was added."),
    "imanage.question.option.delete": _("A custom field option was deleted."),
    "imanage.question.option.update": _("A custom field option was modified."),
    "imanage.tag.create": _("A tag was added."),
    "imanage.tag.delete": _("A tag was deleted."),
    "imanage.tag.update": _("A tag was modified."),
    "imanage.room.create": _("A new room was added."),
    "imanage.room.update": _("A room was modified."),
    "imanage.room.delete": _("A room was deleted."),
    "imanage.schedule.release": _("A new schedule version was released."),
    "imanage.submission.accept": _("The proposal was accepted."),
    "imanage.submission.cancel": _("The proposal was cancelled."),
    "imanage.submission.confirm": _("The proposal was confirmed."),
    "imanage.submission.create": _("The proposal was added."),
    "imanage.submission.deleted": _("The proposal was deleted."),
    "imanage.submission.reject": _("The proposal was rejected."),
    "imanage.submission.resource.create": _("A proposal resource was added."),
    "imanage.submission.resource.delete": _("A proposal resource was deleted."),
    "imanage.submission.resource.update": _("A proposal resource was modified."),
    "imanage.submission.review.delete": _("A review was deleted."),
    "imanage.submission.review.update": _("A review was modified."),
    "imanage.submission.review.create": _("A review was added."),
    "imanage.submission.speakers.add": _("A speaker was added to the proposal."),
    "imanage.submission.speakers.invite": _("A speaker was invited to the proposal."),
    "imanage.submission.speakers.remove": _("A speaker was removed from the proposal."),
    "imanage.submission.invitation.send": _("A speaker invitation was sent."),
    "imanage.submission.invitation.accept": _("A speaker invitation was accepted."),
    "imanage.submission.invitation.retract": _("A speaker invitation was retracted."),
    "imanage.submission.unconfirm": _("The proposal was unconfirmed."),
    "imanage.submission.update": _("The proposal was modified."),
    "imanage.submission.withdraw": _("The proposal was withdrawn."),
    "imanage.submission.answer.update": _("A custom field response was modified."),
    "imanage.submission.answer.create": _("A custom field response was added."),
    "imanage.submission.answer.delete": _("A custom field response was removed."),
    "imanage.submission.comment.create": _("A proposal comment was added."),
    "imanage.submission.comment.delete": _("A proposal comment was deleted."),
    "imanage.submission_type.create": _("A session type was added."),
    "imanage.submission_type.delete": _("A session type was deleted."),
    "imanage.submission_type.make_default": _("The session type was made default."),
    "imanage.submission_type.update": _("A session type was modified."),
    "imanage.access_code.create": _("An access code was added."),
    "imanage.access_code.send": _("An access code was sent."),
    "imanage.access_code.update": _("An access code was modified."),
    "imanage.access_code.delete": _("An access code was deleted."),
    "imanage.track.create": _("A track was added."),
    "imanage.track.delete": _("A track was deleted."),
    "imanage.track.update": _("A track was modified."),
    "imanage.speaker.arrived": _("A speaker has been marked as arrived."),
    "imanage.speaker.unarrived": _("A speaker has been marked as not arrived."),
    "imanage.speaker_information.create": _("A speaker information note was added."),
    "imanage.speaker_information.update": _("A speaker information note was modified."),
    "imanage.speaker_information.delete": _("A speaker information note was deleted."),
    "imanage.user.token.reset": _("The API token was created."),
    "imanage.user.token.reset": _("The API token was reset."),
    "imanage.user.token.revoke": _("The API token was revoked."),
    "imanage.user.token.upgrade": _(
        "The API token was upgraded to the latest version."
    ),
    "imanage.user.password.reset": phrases.base.password_reset_success,
    "imanage.user.password.update": _("The password was modified."),
    "imanage.user.profile.update": _("The profile was modified."),
    "imanage.user.email.update": _("The user changed their email address."),
}


@receiver(activitylog_display)
def default_activitylog_display(sender: Event, activitylog: ActivityLog, **kwargs):
    if templated_entry := TEMPLATE_LOG_NAMES.get(activitylog.action_type):
        message = str(templated_entry)
        # Check if all placeholders are present in activitylog.data
        placeholders = {v[1] for v in string.Formatter().parse(message) if v[1]}
        if isinstance(activitylog.json_data, dict) and placeholders <= set(
            activitylog.json_data.keys()
        ):
            return message.format(**activitylog.json_data)
    action_type = LOG_ALIASES.get(activitylog.action_type, activitylog.action_type)
    return LOG_NAMES.get(action_type)


def _submission_label_text(submission: Submission) -> str:
    if submission.state in (
        SubmissionStates.ACCEPTED,
        SubmissionStates.CONFIRMED,
    ):
        return _n("Session", "Sessions", 1)
    return _n("Proposal", "Proposals", 1)


@receiver(activitylog_object_link)
def default_activitylog_object_link(sender: Event, activitylog: ActivityLog, **kwargs):
    if not activitylog.content_object:
        return
    url = ""
    text = ""
    link_text = ""
    if isinstance(activitylog.content_object, Submission):
        url = activitylog.content_object.orga_urls.base
        link_text = escape(activitylog.content_object.title)
        text = _submission_label_text(activitylog.content_object)
    elif isinstance(activitylog.content_object, SubmissionComment):
        url = (
            activitylog.content_object.submission.orga_urls.comments
            + f"#comment-{activitylog.content_object.pk}"
        )
        link_text = escape(activitylog.content_object.submission.title)
        text = _submission_label_text(activitylog.content_object.submission)
    elif isinstance(activitylog.content_object, Review):
        url = activitylog.content_object.submission.orga_urls.reviews
        link_text = escape(activitylog.content_object.submission.title)
        text = _submission_label_text(activitylog.content_object.submission)
    elif isinstance(activitylog.content_object, Question):
        url = activitylog.content_object.urls.base
        link_text = escape(activitylog.content_object.question)
        text = _("Custom field")
    elif isinstance(activitylog.content_object, AnswerOption):
        url = activitylog.content_object.question.urls.base
        link_text = escape(activitylog.content_object.question.question)
        text = _("Custom field")
    elif isinstance(activitylog.content_object, Answer):
        if activitylog.content_object.submission:
            url = activitylog.content_object.submission.orga_urls.base
        else:
            url = activitylog.content_object.question.urls.base
        link_text = escape(activitylog.content_object.question.question)
        text = _("Response to custom field")
    elif isinstance(activitylog.content_object, CfP):
        url = activitylog.content_object.urls.text
        link_text = _("Call for Proposals")
    elif isinstance(activitylog.content_object, MailTemplate):
        url = activitylog.content_object.urls.base
        text = _("Mail template")
        link_text = escape(activitylog.content_object.subject)
    elif isinstance(activitylog.content_object, QueuedMail):
        url = activitylog.content_object.urls.base
        text = _("Email")
        link_text = escape(activitylog.content_object.subject)
    elif isinstance(activitylog.content_object, SpeakerProfile):
        url = activitylog.content_object.orga_urls.base
        text = _("Speaker profile")
        link_text = escape(activitylog.content_object.user.get_display_name())
    elif isinstance(activitylog.content_object, Event):
        url = activitylog.content_object.orga_urls.base
        text = _("Event")
        link_text = escape(activitylog.content_object.name)
    if url:
        if not link_text:
            link_text = url
        return f'{text} <a href="{url}">{link_text}</a>'
    if text or link_text:
        return f"{text} {link_text}"
