"""
Update live status for charging points from Open Charge Map API.
"""
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from ukcharge.models import ChargingPoint
from ukcharge.services import OCMAPIClient
from django.conf import settings

logger = logging.getLogger("ukcharge")


class Command(BaseCommand):
    help = "Update live status for UK charging points from Open Charge Map"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="Maximum number of points to update (default: 500)",
        )
        parser.add_argument(
            "--ocm-id",
            type=int,
            default=None,
            help="Update a specific charging point by OCM ID",
        )
        parser.add_argument(
            "--stale-only",
            action="store_true",
            default=True,
            help="Only update points whose status is stale (>1 hour old)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Update all points, not just live ones",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        ocm_id = options["ocm_id"]
        stale_only = not options["all"]
        update_all = options["all"]

        if not settings.OCM_API_KEY:
            self.stdout.write(
                self.style.ERROR("OCM_API_KEY not set in environment.")
            )
            return

        client = OCMAPIClient(api_key=settings.OCM_API_KEY)

        if ocm_id:
            points = ChargingPoint.objects.filter(ocm_id=ocm_id)
        elif update_all:
            points = ChargingPoint.objects.filter(country_code="GB")[:limit]
        else:
            points = ChargingPoint.objects.filter(
                country_code="GB", is_live_status=True
            )[:limit]

        total = points.count() if not ocm_id else 1
        self.stdout.write(self.style.NOTICE(
            f"Updating live status for {total} charging points..."
        ))

        updated = 0
        failed = 0
        unchanged = 0

        for point in points:
            status_data = client.fetch_live_status(point.ocm_id)
            if status_data is None:
                failed += 1
                continue

            if stale_only and point.last_status_update:
                from datetime import timedelta
                from django.utils import timezone
                if timezone.now() - point.last_status_update < timedelta(hours=1):
                    unchanged += 1
                    continue

            with transaction.atomic():
                point.status = status_data["status"]
                point.is_live_status = status_data["is_live"]
                point.last_status_update = status_data["last_update"]
                point.save(update_fields=[
                    "status", "is_live_status", "last_status_update", "updated"
                ])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nStatus update complete!\n"
            f"  Updated: {updated}\n"
            f"  Unchanged (fresh): {unchanged}\n"
            f"  Failed: {failed}\n"
            f"  Total checked: {total}"
        ))