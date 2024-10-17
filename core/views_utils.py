from django.utils import timezone
from datetime import timedelta

class StatusSummaryMixin:
    @staticmethod
    def get_status_summary(statuses, now, start_time, number_of_sticks):
        summary = []
        for i in range(number_of_sticks):
            minutes = 60*24 / number_of_sticks  # Each stick represents X minutes
            stick_time = start_time + timedelta(minutes=i*minutes)
            status = statuses.filter(checked_at__lte=stick_time).last()
            if status:
                if status.is_up:
                    summary.append('up')
                elif status.is_down:
                    summary.append('down')
                else:
                    summary.append('unknown')
            else:
                summary.append('unknown')
        return summary

    def add_status_summary_to_services(self, services, number_of_sticks=85):
        now = timezone.now()
        twenty_four_hours_ago = now - timedelta(hours=24)

        for service in services:
            statuses = service.statuses.filter(checked_at__gte=twenty_four_hours_ago).order_by('checked_at')
            service.status_summary = self.get_status_summary(statuses, now, twenty_four_hours_ago, number_of_sticks)
