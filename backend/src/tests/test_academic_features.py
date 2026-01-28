import pytest
from django.urls import reverse
from imanage.event.models import Event
from imanage.submission.models import Question, ReviewScoreCategory

@pytest.mark.django_db
def test_academic_event_creation(orga_client, organiser):
    url = reverse("orga:event.create")
    
    # Step 1: Initial
    response = orga_client.post(url, {
        "event_wizard-current_step": "initial",
        "initial-organiser": organiser.pk,
        "initial-locales": ["en"],
    })
    assert response.status_code == 200
    
    # Step 2: Basics
    response = orga_client.post(url, {
        "event_wizard-current_step": "basics",
        "basics-name_0": "Academic Conference",
        "basics-slug": "acaconf",
        "basics-timezone": "UTC",
        "basics-email": "admin@acaconf.org",
        "basics-locale": "en",
    })
    assert response.status_code == 200

    # Step 3: Timeline
    response = orga_client.post(url, {
        "event_wizard-current_step": "timeline",
        "timeline-date_from": "2026-01-01",
        "timeline-date_to": "2026-01-02",
    })
    assert response.status_code == 200

    # Step 4: Display
    response = orga_client.post(url, {
        "event_wizard-current_step": "display",
        "display-primary_color": "#2c3e50",
    })
    assert response.status_code == 200

    # Step 5: Plugins (Final step)
    response = orga_client.post(url, {
        "event_wizard-current_step": "plugins",
    }, follow=True)
    
    assert response.status_code == 200
    assert Event.objects.filter(slug="acaconf").exists()
    
    event = Event.objects.get(slug="acaconf")
    
    # Check if Paper PDF question exists
    assert Question.objects.filter(event=event, question__contains="Paper (PDF)").exists()
    
    # Check if Academic Review Categories exist
    assert ReviewScoreCategory.objects.filter(event=event, name__contains="Originality").exists()
    assert ReviewScoreCategory.objects.filter(event=event, name__contains="Relevance").exists()
    assert ReviewScoreCategory.objects.filter(event=event, name__contains="Clarity").exists()
