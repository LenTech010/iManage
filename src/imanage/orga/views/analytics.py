# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils.timezone import now
from django.views.generic import TemplateView
from django_context_decorator import context

from imanage.common.views.mixins import EventPermissionRequired, PermissionRequired
from imanage.event.models import AttendeeMetrics, EventMetrics
from imanage.submission.models import Review, Submission


class AnalyticsDashboardView(EventPermissionRequired, PermissionRequired, TemplateView):
    """Analytics dashboard showing event metrics and visualizations."""

    template_name = "orga/analytics/dashboard.html"
    permission_required = "orga.view_orga_area"

    @context
    def metrics_data(self):
        """Get current metrics for the event."""
        # Get the latest metrics or calculate current ones
        latest_metric = EventMetrics.objects.filter(event=self.request.event).first()
        
        # Calculate current statistics
        submissions = Submission.objects.filter(event=self.request.event)
        total = submissions.count()
        accepted = submissions.filter(state='accepted').count()
        rejected = submissions.filter(state='rejected').count()
        pending = submissions.filter(state='submitted').count()
        
        reviews = Review.objects.filter(submission__event=self.request.event)
        avg_score = reviews.aggregate(Avg('score'))['score__avg'] or 0
        
        attendees = AttendeeMetrics.objects.filter(event=self.request.event)
        
        return {
            'total_submissions': total,
            'accepted_submissions': accepted,
            'rejected_submissions': rejected,
            'pending_submissions': pending,
            'acceptance_rate': (accepted / total * 100) if total > 0 else 0,
            'total_reviews': reviews.count(),
            'avg_review_score': round(avg_score, 2),
            'registered_attendees': attendees.count(),
            'active_attendees': attendees.filter(last_active__gte=now() - timedelta(days=7)).count(),
        }

    @context
    def submission_timeline_data(self):
        """Get submission timeline data for chart."""
        from django.db.models.functions import TruncDate
        
        submissions = Submission.objects.filter(
            event=self.request.event
        ).annotate(
            date=TruncDate('created')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return {
            'labels': [str(item['date']) for item in submissions],
            'data': [item['count'] for item in submissions],
        }

    @context
    def submission_status_data(self):
        """Get submission status distribution for pie chart."""
        submissions = Submission.objects.filter(event=self.request.event)
        
        status_counts = {
            'Accepted': submissions.filter(state='accepted').count(),
            'Rejected': submissions.filter(state='rejected').count(),
            'Pending': submissions.filter(state='submitted').count(),
            'Confirmed': submissions.filter(state='confirmed').count(),
            'Withdrawn': submissions.filter(state='withdrawn').count(),
        }
        
        return {
            'labels': list(status_counts.keys()),
            'data': list(status_counts.values()),
        }

    @context
    def review_turnaround_data(self):
        """Get review turnaround time data."""
        from django.db.models import F, ExpressionWrapper, fields
        
        reviews = Review.objects.filter(
            submission__event=self.request.event,
            created__isnull=False,
            updated__isnull=False
        ).annotate(
            turnaround=ExpressionWrapper(
                F('updated') - F('created'),
                output_field=fields.DurationField()
            )
        )
        
        turnaround_days = []
        for review in reviews:
            if review.turnaround:
                days = review.turnaround.total_seconds() / 86400
                turnaround_days.append(round(days, 1))
        
        # Calculate average turnaround by week
        avg_turnaround = sum(turnaround_days) / len(turnaround_days) if turnaround_days else 0
        
        return {
            'avg_turnaround_days': round(avg_turnaround, 1),
            'turnaround_data': turnaround_days[:20],  # Latest 20 reviews
        }

    @context
    def attendee_demographics_data(self):
        """Get attendee demographics data."""
        attendees = AttendeeMetrics.objects.filter(event=self.request.event)
        
        # Country distribution
        countries = attendees.exclude(country='').values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return {
            'country_labels': [item['country'] for item in countries],
            'country_data': [item['count'] for item in countries],
        }


class AttendeeMetricsView(EventPermissionRequired, PermissionRequired, TemplateView):
    """View for detailed attendee metrics."""

    template_name = "orga/analytics/attendees.html"
    permission_required = "orga.view_orga_area"

    @context
    def attendees(self):
        """Get all attendee metrics for the event."""
        return AttendeeMetrics.objects.filter(
            event=self.request.event
        ).select_related('user').order_by('-last_active')

    @context
    def engagement_stats(self):
        """Calculate engagement statistics."""
        attendees = AttendeeMetrics.objects.filter(event=self.request.event)
        
        total = attendees.count()
        checked_in = attendees.filter(checked_in=True).count()
        active_week = attendees.filter(last_active__gte=now() - timedelta(days=7)).count()
        
        return {
            'total_attendees': total,
            'checked_in': checked_in,
            'check_in_rate': (checked_in / total * 100) if total > 0 else 0,
            'active_this_week': active_week,
            'activity_rate': (active_week / total * 100) if total > 0 else 0,
        }
