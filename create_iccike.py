from imanage.event.models import Organiser, Event
from django.utils.timezone import now
from imanage.submission.models import Question, QuestionTarget, QuestionVariant, ReviewScore, ReviewScoreCategory
from imanage.submission.models.question import QuestionRequired
from imanage.person.models import User
from django_scopes import scopes_disabled

with scopes_disabled():
    org = Organiser.objects.first()
    if not org:
        org = Organiser.objects.create(name="Default Organiser", slug="default")
    
    event, created = Event.objects.get_or_create(
        slug='iccike',
        defaults={
            'organiser': org,
            'name': 'ICCIKE',
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
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        from imanage.event.models import Team
        team = Team.objects.filter(organiser=org, members__in=[admin_user], can_change_event_settings=True).first()
        if team:
            team.limit_events.add(event)
            print(f"Added {event.name} to team {team.name} for user {admin_user.email}")
