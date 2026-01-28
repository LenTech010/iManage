# SPDX-FileCopyrightText: 2025-present Tobias Kunze
# SPDX-License-Identifier: AGPL-3.0-only WITH LicenseRef-Imanage-AGPL-3.0-Terms

import csv
from io import StringIO, BytesIO

from django.utils.translation import gettext_lazy as _

from imanage.common.exporter import BaseExporter


class AnalyticsCSVExporter(BaseExporter):
    """Export event analytics data as CSV."""

    extension = "csv"
    filename_identifier = "analytics"
    verbose_name = _("Event Analytics (CSV)")
    content_type = "text/csv"

    def get_data(self):
        """Generate CSV data for event analytics."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Event',
            'Date',
            'Total Submissions',
            'Accepted',
            'Rejected',
            'Pending',
            'Total Reviews',
            'Avg Review Score',
            'Avg Review Turnaround (days)',
            'Registered Attendees',
            'Active Attendees',
            'Page Views',
            'Unique Visitors',
        ])
        
        # Get metrics for the event
        from imanage.event.models import EventMetrics
        
        metrics = EventMetrics.objects.filter(event=self.event).order_by('-date')
        
        for metric in metrics:
            writer.writerow([
                str(self.event.name),
                metric.date.strftime('%Y-%m-%d'),
                metric.total_submissions,
                metric.accepted_submissions,
                metric.rejected_submissions,
                metric.pending_submissions,
                metric.total_reviews,
                f"{metric.avg_review_score:.2f}" if metric.avg_review_score else "N/A",
                f"{metric.avg_review_turnaround_days:.1f}" if metric.avg_review_turnaround_days else "N/A",
                metric.registered_attendees,
                metric.active_attendees,
                metric.page_views,
                metric.unique_visitors,
            ])
        
        return output.getvalue().encode('utf-8')


class AttendeeCSVExporter(BaseExporter):
    """Export attendee data as CSV."""

    extension = "csv"
    filename_identifier = "attendees"
    verbose_name = _("Attendee Metrics (CSV)")
    content_type = "text/csv"

    def get_data(self):
        """Generate CSV data for attendee information."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'User Email',
            'User Name',
            'Institution',
            'Country',
            'City',
            'Sessions Attended',
            'Papers Submitted',
            'Reviews Completed',
            'Registered At',
            'Checked In',
            'Last Active',
        ])
        
        # Get attendee metrics for the event
        from imanage.event.models import AttendeeMetrics
        
        attendees = AttendeeMetrics.objects.filter(
            event=self.event
        ).select_related('user').order_by('user__email')
        
        for attendee in attendees:
            writer.writerow([
                attendee.user.email,
                attendee.user.get_display_name(),
                attendee.institution,
                attendee.country,
                attendee.city,
                attendee.sessions_attended,
                attendee.papers_submitted,
                attendee.reviews_completed,
                attendee.registered_at.strftime('%Y-%m-%d %H:%M'),
                'Yes' if attendee.checked_in else 'No',
                attendee.last_active.strftime('%Y-%m-%d %H:%M'),
            ])
        
        return output.getvalue().encode('utf-8')


class ReviewSummaryCSVExporter(BaseExporter):
    """Export review summary data as CSV."""

    extension = "csv"
    filename_identifier = "review-summary"
    verbose_name = _("Review Summary (CSV)")
    content_type = "text/csv"

    def get_data(self):
        """Generate CSV data for review summaries."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Submission Code',
            'Submission Title',
            'Submitter',
            'Track',
            'Total Reviews',
            'Avg Score',
            'Status',
            'Submission Date',
        ])
        
        # Get submissions with review data
        from imanage.submission.models import Submission
        from django.db.models import Avg, Count
        
        submissions = Submission.objects.filter(event=self.event).annotate(
            review_count=Count('reviews'),
            avg_score=Avg('reviews__score')
        ).select_related('track').prefetch_related('speakers')
        
        for submission in submissions:
            submitters = ', '.join(
                speaker.get_display_name() 
                for speaker in submission.speakers.all()
            )
            
            writer.writerow([
                submission.code,
                str(submission.title),
                submitters,
                str(submission.track.name) if submission.track else 'N/A',
                submission.review_count,
                f"{submission.avg_score:.2f}" if submission.avg_score else "N/A",
                submission.get_state_display(),
                submission.created.strftime('%Y-%m-%d'),
            ])
        
        return output.getvalue().encode('utf-8')
