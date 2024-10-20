from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

class StatusSummaryMixin:
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
                if any(s.status == 'DOWN' for s in stick_statuses):
                    summary.append('down')
                elif any(s.status == 'DEGRADED' for s in stick_statuses):
                    summary.append('degraded')
                elif any(s.status == 'UP' for s in stick_statuses):
                    summary.append('up')
                else:
                    summary.append('unknown')
            else:
                summary.append('unknown')

        return summary

    def add_status_summary_to_services(self, services, days=90, number_of_sticks=90):
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days)

        for service in services:
            statuses = list(service.statuses.filter(checked_at__gte=start_time).order_by('checked_at'))
            service.status_summary = self.get_status_summary(statuses, end_time, start_time, number_of_sticks)

            # Add current status
            latest_status = statuses[-1] if statuses else None
            service.current_status = latest_status.status.lower() if latest_status else 'unknown'

    def get_overall_project_status(self, services, days=90, number_of_sticks=90):
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days)

        all_statuses = []
        for service in services:
            service_statuses = list(service.statuses.filter(checked_at__gte=start_time))
            all_statuses.extend(service_statuses)

        return self.get_status_summary(all_statuses, end_time, start_time, number_of_sticks)
