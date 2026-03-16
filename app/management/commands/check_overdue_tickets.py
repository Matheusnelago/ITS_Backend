from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import Ticket, Case

class Command(BaseCommand):
    help = 'Check for overdue tickets and create cases'

    def handle(self, *args, **options):
        today = timezone.now().date()

        # Find unpaid tickets that are overdue (status != 'paid', due_date < today, no case)
        overdue_tickets = Ticket.objects.filter(
            due_date__lt=today,
            status__in=['pending', 'overdue'],  # unpaid
            case__isnull=True
        )

        created_cases = 0
        for ticket in overdue_tickets:
            # Set status to overdue (tag)
            ticket.status = 'overdue'
            ticket.save()

            # Create case
            case = Case.objects.create(
                ticket=ticket,
                notes=f'Case created automatically due to overdue payment on {today}'
            )

            # New: Judiciary notification workflow
            case.available = True
            case.judiciary_notified = True
            case.save()

            # Log judiciary notification
            AuditLog.objects.create(
                action='message_sent',
                details=f'New available case created for judiciary review: {ticket.ticket_issued}'
            )

            created_cases += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Processed overdue ticket {ticket.ticket_issued}: status='overdue', case created and judiciary notified"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Check complete. Created {created_cases} new cases for overdue tickets.'
            )
        )
