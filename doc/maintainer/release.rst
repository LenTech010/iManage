.. SPDX-FileCopyrightText: 2017-present Tobias Kunze
.. SPDX-License-Identifier: CC-BY-SA-4.0

Release a imanage version
=========================

You are a imanage maintainer and want to release a new version? Hold on to your fancy hat or your favourite socks, here we go!

Boarding checks
---------------

1. Are the translation files up to date?
2. Are there pending checks for bad translations on Weblate?
3. Are there pending translations from `Weblate <https://translate.imanage.com/projects/imanage/imanage/#repository>`_? Merge them.
4. Are all locales with more than 75% coverage included in the release? If new translations need to be added, add new calendar locales (you have to download the `release archive <https://github.com/fullcalendar/fullcalendar/releases/download/v6.1.5/fullcalendar-6.1.5.zip>`_) and extract the locales from there), and make sure that flags (in input fields) for the new locale are shown.
5. Are there warnings about missing migrations?
6. Any blockers to see `in our issues <https://github.com/imanage/imanage/issues?q=is%3Aopen+is%3Aissue+label%3A%22type%3A+bug%22+>`_?
7. Are there any TODOs that you have to resolve?
8. Are there any ``@pytest.mark.xfail`` that you have to resolve?
9. Are the :ref:`changelog` well-phrased and complete?
10. Are there `open pull requests <https://github.com/imanage/imanage/pulls>`_ that you should merge?
11. Are all tests passing in CI?
12. Have you written (and not pushed) a blog post? It should contain at least major features and all contributors involved in the release.

System checks
-------------

1. Deploy the release-ready commit to an instance. Check if the upgrade and the instance works.
2. Clean clone: ``git clone git@github.com:imanage/imanage imanage-release && cd imanage-release`` (or local clone)
3. Install release dependencies: ``uv pip install check-manifest twine wheel``
4. Run ``just release-checks`` **locally**.

Take-off and landing
--------------------

1. Bump version in ``src/imanage/__init__.py``.
2. Add the release to the :ref:`changelog`.
3. Run ``just release v202X.Y.Z``
4. Install/update the package somewhere.
5. Publish the blog post.
6. Add the release on `GitHub <https://github.com/imanage/imanage/releases>`_ (upload the archive you uploaded to PyPI, and add a link to the correct section of the :ref:`changelog`)
7. Upgrade `the docker repository <https://github.com/imanage/imanage-docker>`_ by running ``just release v202X.Y.Z``
8. Increment version number to ``version+1.dev0`` in ``src/imanage/__init__.py``.
9. ``rm -rf imanage-release``
10. Update version numbers in update checker (``versions.py``) and deploy.
11. Update any plugins waiting for the new release.
12. Check if the docker image build was successful.
13. Post about the release on ``chaos.social``, Twitter and LinkedIn.
14. Notify interested parties (e.g. big self-hosted instances, prominent plugin developers) about the release.
