.. SPDX-FileCopyrightText: 2018-present Tobias Kunze
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. highlight:: python
   :linenothreshold: 5

.. _`pluginsignals`:

General APIs
============

This page lists some general signals and hooks which do not belong to a
specific plugin but might come in handy for all sorts of plugin.

Core
----

.. automodule:: imanage.common.signals
   :members: periodic_task, register_locales, auth_html

.. automodule:: imanage.submission.signals
   :members: submission_state_change

.. automodule:: imanage.schedule.signals
   :members: schedule_release

.. automodule:: imanage.mail.signals
   :members: register_mail_placeholders, queuedmail_post_send, queuedmail_pre_send, request_pre_send

.. automodule:: imanage.person.signals
   :members: delete_user

Exporters
---------

.. automodule:: imanage.common.signals
   :no-index:
   :members: register_data_exporters


Organiser area
--------------

.. automodule:: imanage.orga.signals
   :members: nav_event, nav_global, html_head, html_above_orga_page, html_below_orga_page, activate_event, nav_event_settings, event_copy_data, extra_form, speaker_form, submission_form, review_form, mail_form, dashboard_tile

.. automodule:: imanage.common.signals
   :no-index:
   :members: activitylog_display, activitylog_object_link

Display
-------

.. automodule:: imanage.cfp.signals
   :members: cfp_steps, footer_link, html_above_submission_list, html_above_profile_page, html_head

.. automodule:: imanage.agenda.signals
   :members: register_recording_provider, html_above_session_pages, html_below_session_pages

.. automodule:: imanage.common.signals
   :no-index:
   :members: profile_bottom_html
