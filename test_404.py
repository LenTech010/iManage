from django.test import RequestFactory
from imanage.cfp.views.event import EventStartpage
from imanage.event.models import Event
from imanage.person.models import User
from django.urls import resolve

from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

from django.contrib.auth.models import AnonymousUser

def dummy_get_response(request):
    return None

factory = RequestFactory()
request = factory.get('/iccike/')
middleware = SessionMiddleware(dummy_get_response)
middleware.process_request(request)
request.session.save()

event = Event.objects.get(slug='iccike')
request.event = event
# Authenticate the user
request.user = User.objects.first()

# Mock resolver_match
request.resolver_match = resolve('/iccike/')

view = EventStartpage.as_view()
try:
    response = view(request, event='iccike')
    print(f'Status: {response.status_code}')
    if hasattr(response, 'url'):
        print(f'Redirect URL: {response.url}')
except Exception as e:
    import traceback
    print(f'Exception: {e}')
    traceback.print_exc()
