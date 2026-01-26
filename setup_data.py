import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imanage.settings")
import sys
sys.path.insert(0, os.path.abspath("src"))
django.setup()

from imanage.event.models import Organiser, Event, Team
from django.utils.timezone import now
from imanage.submission.models import Question, QuestionTarget, QuestionVariant, ReviewScore, ReviewScoreCategory
from imanage.submission.models.question import QuestionRequired
from imanage.person.models import User
from django_scopes import scopes_disabled

with scopes_disabled():
    # Create superuser if it doesn't exist
    admin_user = User.objects.filter(email='admin@example.com').first()
    if not admin_user:
        admin_user = User.objects.create_superuser(email='admin@example.com', password='admin')
        print("Created superuser 'admin@example.com' with password 'admin'")
    else:
        print(f"User already exists: {admin_user.email}")
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()
            print("Promoted user to superuser.")

    org = Organiser.objects.first()
    if not org:
        org = Organiser.objects.create(name="Default Organiser", slug="default")
    
    event, created = Event.objects.get_or_create(
        slug='iccike',
        defaults={
            'organiser': org,
            'name': 'ICCIKE 2026',
            'timezone': 'UTC',
            'email': 'admin@iccike.org',
            'date_from': now().date(),
            'date_to': now().date(),
        }
    )
    
    if not Question.objects.filter(event=event, question__contains='Paper (PDF)').exists():
        Question.objects.create(
            event=event,
            target=QuestionTarget.SUBMISSION,
            variant=QuestionVariant.FILE,
            question={'en': 'Paper (PDF)'},
            help_text={'en': 'Please upload your paper as a PDF file.'},
            question_required=QuestionRequired.REQUIRED,
            active=True
        )
        print("Created Paper (PDF) question.")

    for cat_name in ['Originality', 'Relevance', 'Clarity']:
        if not ReviewScoreCategory.objects.filter(event=event, name__contains=cat_name).exists():
            cat = ReviewScoreCategory.objects.create(
                event=event, name={'en': cat_name}, weight=1, required=True
            )
            for val, label in [(1, 'Poor'), (2, 'Fair'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')]:
                ReviewScore.objects.create(category=cat, value=val, label=label)
            print(f"Created {cat_name} scoring category.")
    
    # Ensure admin has access
    team = Team.objects.filter(organiser=org, members__in=[admin_user]).first()
    if not team:
        team = Team.objects.create(organiser=org, name="Admin Team", can_change_event_settings=True)
        team.members.add(admin_user)
    
    team.limit_events.add(event)
    print(f"Added {event.name} to team {team.name} for user {admin_user.email}")

    # Create a test submission
    from imanage.submission.models import Submission, SubmissionType
    sub_type, _ = SubmissionType.objects.get_or_create(event=event, name={'en': 'Talk'})
    
    submission, created = Submission.objects.get_or_create(
        event=event,
        title="Sample Paper Title",
        defaults={
            'submission_type': sub_type,
            'abstract': 'This is a sample abstract for the paper.',
            'state': 'accepted',
        }
    )
    if created:
        print(f"Created test submission: {submission.title}")
    
    print(f"Submission URL: /orga/event/{event.slug}/submissions/{submission.code}/")
