
import os
import django
from django.conf import settings
from django.test import RequestFactory
from django.utils.timezone import now
from datetime import timedelta

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imanage.settings")
django.setup()

from imanage.event.models import Event, Organiser
from imanage.cfp.views.event import GeneralView
from django.contrib.auth import get_user_model

User = get_user_model()

def reproduce():
    # Setup data
    organiser = Organiser.objects.create(name="Test Organiser", slug="test-organiser")
    user = User.objects.create_user(username="testuser", password="password")
    
    _now = now().date()
    
    # Create events
    e1 = Event.objects.create(
        organiser=organiser,
        name="Current Event",
        slug="current",
        date_from=_now,
        date_to=_now + timedelta(days=1),
        is_public=True
    )
    
    # Event with missing dates (if possible, let's see if it causes issues in the loop)
    # The loop does event.date_from <= _now <= event.date_to
    # If date_from or date_to is None, it will raise TypeError
    try:
        e2 = Event.objects.create(
            organiser=organiser,
            name="Broken Event",
            slug="broken",
            is_public=True
            # date_from and date_to are None
        )
    except Exception as e:
        print(f"Could not create event with missing dates: {e}")
        e2 = None

    # Simulate duplicate events in the queryset
    # In a real scenario, this might happen due to joins in get_events_for_user
    # Let's see if we can trigger it.
    
    view = GeneralView()
    request = RequestFactory().get('/')
    request.user = user
    request.uses_custom_domain = False
    view.request = request
    
    print("Testing get_context_data...")
    try:
        context = view.get_context_data()
        print("Current events:", [e.name for e in context["current_events"]])
    except TypeError as e:
        print(f"Caught expected TypeError: {e}")
    except Exception as e:
        print(f"Caught unexpected exception: {e}")

    # Test URL generation error
    # If event.urls.base fails, it might be because of missing slug or something
    if e1:
        print(f"Event urls base: {e1.urls.base}")
        # To simulate error, we might need an event where reverse() fails
        # or where urlman fails.

if __name__ == "__main__":
    reproduce()
