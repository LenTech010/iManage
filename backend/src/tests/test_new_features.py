# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

import pytest
from django.utils.timezone import now, timedelta
from imanage.event.models import Event, EventFavourite, Notification, SecurityAlert


@pytest.mark.django_db
def test_event_status_tracking(event):
    """Test that event status is correctly determined."""
    today = now().date()
    
    # Test upcoming event
    event.date_from = today + timedelta(days=5)
    event.date_to = today + timedelta(days=7)
    event.save()
    assert event.get_event_status() == 'upcoming'
    assert not event.is_active
    
    # Test active event
    event.date_from = today - timedelta(days=1)
    event.date_to = today + timedelta(days=1)
    event.save()
    assert event.get_event_status() == 'active'
    assert event.is_active
    
    # Test past event
    event.date_from = today - timedelta(days=7)
    event.date_to = today - timedelta(days=5)
    event.save()
    assert event.get_event_status() == 'past'
    assert not event.is_active


@pytest.mark.django_db
def test_event_favorites(event, user):
    """Test event favorites functionality."""
    from django_scopes import scope
    
    with scope(event=event):
        # Create a favorite
        favorite = EventFavourite.objects.create(event=event, user=user)
        assert favorite.event == event
        assert favorite.user == user
        
        # Check favorite count
        assert event.favourites.count() == 1
        
        # Test unique constraint
        with pytest.raises(Exception):  # IntegrityError
            EventFavourite.objects.create(event=event, user=user)


@pytest.mark.django_db
def test_notifications(event, user):
    """Test notification creation and marking as read."""
    from django_scopes import scope
    
    with scope(event=event):
        # Create a notification
        notification = Notification.objects.create(
            user=user,
            event=event,
            notification_type='submission_accepted',
            title='Your submission was accepted',
            message='Congratulations! Your submission has been accepted.',
        )
        
        assert notification.is_read is False
        assert notification.read_at is None
        
        # Mark as read
        notification.mark_as_read()
        assert notification.is_read is True
        assert notification.read_at is not None


@pytest.mark.django_db
def test_security_alert_creation(event, user):
    """Test security alert creation."""
    alert = SecurityAlert.objects.create(
        user=user,
        event=event,
        alert_type='spam_submission',
        severity='medium',
        description='User submitted multiple spam entries',
    )
    
    assert alert.status == 'open'
    assert alert.severity == 'medium'
    assert alert.resolved_by is None


@pytest.mark.django_db
def test_file_validation_in_question(event):
    """Test file validation fields in Question model."""
    from imanage.submission.models import Question, QuestionVariant
    from django_scopes import scope
    
    with scope(event=event):
        question = Question.objects.create(
            event=event,
            variant=QuestionVariant.FILE,
            question="Upload your paper (PDF only)",
            allowed_file_types="pdf",
            max_file_size=5,  # 5MB
        )
        
        assert question.allowed_file_types == "pdf"
        assert question.max_file_size == 5
        
        # Test file validation method exists
        assert hasattr(question, 'validate_file')


@pytest.mark.django_db  
def test_resource_file_integrity_fields(event, submission):
    """Test that Resource model has file integrity fields."""
    from imanage.submission.models import Resource
    from django_scopes import scope
    
    with scope(event=event):
        resource = Resource.objects.create(
            submission=submission,
            description="Test resource",
        )
        
        # Check that integrity fields exist
        assert hasattr(resource, 'file_hash')
        assert hasattr(resource, 'file_size')
        assert hasattr(resource, 'mime_type')
        assert hasattr(resource, 'verify_integrity')


@pytest.mark.django_db
def test_review_phase_double_blind_options(event):
    """Test that ReviewPhase supports double-blind review."""
    from imanage.submission.models import ReviewPhase
    from django_scopes import scope
    
    with scope(event=event):
        phase = ReviewPhase.objects.create(
            event=event,
            name="Blind Review Phase",
            can_see_speaker_names=False,
            can_see_reviewer_names=False,
        )
        
        assert phase.can_see_speaker_names is False
        assert phase.can_see_reviewer_names is False
