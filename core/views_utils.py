import json
from datetime import timedelta

from django.db.models import Avg, OuterRef, Subquery
from django.utils import timezone

from core.models import ServiceStatus


class StatusSummaryMixin:
    def get_incidents(self, services):
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)

        down_statuses = ServiceStatus.objects.filter(
            service__in=services, status=ServiceStatus.StatusChoices.DOWN, checked_at__gte=twenty_four_hours_ago
        )

        up_after_down = ServiceStatus.objects.filter(
            service=OuterRef("service"), status=ServiceStatus.StatusChoices.UP, checked_at__gt=OuterRef("checked_at")
        ).order_by("checked_at")

        down_statuses_annotated = down_statuses.annotate(
            latest_up_after=Subquery(up_after_down.values("checked_at")[:1])
        )

        active_incidents = down_statuses_annotated.filter(latest_up_after__isnull=True)

        recently_resolved = down_statuses_annotated.filter(latest_up_after__isnull=False)

        return active_incidents, recently_resolved

    def get_service_response_time_data(self, service):
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)

        hourly_data = (
            service.statuses.filter(checked_at__gte=start_time)
            .extra({"hour": "date_trunc('hour', checked_at)"})
            .values("hour")
            .annotate(response_time=Avg("response_time"))
            .order_by("hour")
        )

        return json.dumps(
            [
                {"timestamp": entry["hour"].isoformat(), "response_time": float(entry["response_time"] or 0)}
                for entry in hourly_data
            ]
        )

    @staticmethod
    def get_status_summary(statuses, end_time, start_time, number_of_sticks):
        summary = []
        duration = end_time - start_time
        interval = duration / number_of_sticks

        for i in range(number_of_sticks):
            stick_end = start_time + interval * (i + 1)
            stick_start = start_time + interval * i

            stick_statuses = [s for s in statuses if stick_start <= s.checked_at < stick_end]

            if stick_statuses:
                # Prioritize 'down' status, then 'degraded', then 'up'
                if any(s.status == "DOWN" for s in stick_statuses):
                    summary.append("down")
                elif any(s.status == "DEGRADED" for s in stick_statuses):
                    summary.append("degraded")
                elif any(s.status == "UP" for s in stick_statuses):
                    summary.append("up")
                else:
                    summary.append("unknown")
            else:
                summary.append("unknown")

        return summary

    def add_status_summary_to_services(self, services, days=1, number_of_sticks=24):
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days)

        for service in services:
            statuses = list(service.statuses.filter(checked_at__gte=start_time).order_by("checked_at"))
            service.status_summary = self.get_status_summary(statuses, end_time, start_time, number_of_sticks)

            # Add current status
            latest_status = statuses[-1] if statuses else None
            service.current_status = latest_status.status.lower() if latest_status else "unknown"

    def get_overall_project_status(self, services, days=90, number_of_sticks=90):
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days)

        all_statuses = []
        for service in services:
            service_statuses = list(service.statuses.filter(checked_at__gte=start_time))
            all_statuses.extend(service_statuses)

        return self.get_status_summary(all_statuses, end_time, start_time, number_of_sticks)
