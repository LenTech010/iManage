import os
import django
from django.utils.timezone import now
from django_scopes import scopes_disabled

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imanage.settings")
django.setup()

from imanage.event.models import Organiser, Event, Team
from imanage.submission.models import Question, QuestionTarget, QuestionVariant, ReviewScore, ReviewScoreCategory
from imanage.submission.models.question import QuestionRequired
from imanage.person.models import User

def run():
    print("Outside scopes_disabled")
    with scopes_disabled():
        print("Starting setup inside scopes_disabled...")
        org, _ = Organiser.objects.get_or_create(
            slug='iccike',
            defaults={'name': 'ICCIKE'}
        )
        print(f"Organiser: {org.slug}")
        
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
        print(f"Event: {event.slug}, Created: {created}")
        
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
        
        print("Point A")
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("No superuser found. Creating admin@localhost...")
            admin_user = User.objects.create_superuser(
                email='admin@localhost',
                password='adminpassword',
            )
            print("Created superuser admin@localhost with password 'adminpassword'")
        
        print(f"Admin User: {admin_user}")
        if admin_user:
            print(f"Checking user: {admin_user.email}")
            if not admin_user.is_administrator:
                admin_user.is_administrator = True
                admin_user.save(update_fields=['is_administrator'])
                print(f"Updated user {admin_user.email} to be an administrator.")

            team = Team.objects.filter(organiser=org).first()
            if not team:
                team = Team.objects.create(
                    organiser=org,
                    name="Admins",
                    can_change_event_settings=True,
                    can_change_organiser_settings=True,
                    can_change_teams=True,
                    can_create_events=True,
                    can_change_submissions=True,
                    all_events=True,
                )
                print(f"Created team: {team.name}")

            if admin_user not in team.members.all():
                team.members.add(admin_user)
                print(f"Added {admin_user.email} to team {team.name}")
            
            print(f"Found team: {team.name}")
            changed = False
            if not team.can_change_organiser_settings:
                team.can_change_organiser_settings = True
                changed = True
                print(f"Ensured team {team.name} can change organiser settings.")
            if not team.all_events:
                team.all_events = True
                changed = True
                print(f"Set all_events=True for team {team.name}")
            if changed:
                team.save()

        print("Setup complete.")

if __name__ == "__main__":
    run()
