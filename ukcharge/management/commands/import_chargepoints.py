"""
Import UK charging points from Open Charge Map API.
"""
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from ukcharge.models import ChargingPoint, Operator, ConnectorType
from ukcharge.services import OCMAPIClient
from django.conf import settings

logger = logging.getLogger("ukcharge")


class Command(BaseCommand):
    help = "Import UK charging points from Open Charge Map API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max",
            type=int,
            default=5000,
            help="Maximum number of points to fetch (default: 5000)",
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Offset for pagination (default: 0)",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing points instead of skipping them",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch but don't save to database",
        )

    def handle(self, *args, **options):
        max_results = options["max"]
        offset = options["offset"]
        update_existing = options["update"]
        dry_run = options["dry_run"]

        if not settings.OCM_API_KEY:
            self.stdout.write(
                self.style.ERROR("OCM_API_KEY not set in environment. "
                                 "Get a free key at https://openchargemap.org/site/loginprovider/")
            )
            return

        self.stdout.write(self.style.NOTICE(
            f"Fetching UK charging points from Open Charge Map (max: {max_results})..."
        ))

        client = OCMAPIClient(api_key=settings.OCM_API_KEY)
        poi_data_list = client.fetch_uk_charge_points(
            max_results=max_results, offset=offset
        )

        if not poi_data_list:
            self.stdout.write(self.style.ERROR("No data returned from OCM API"))
            return

        self.stdout.write(self.style.NOTICE(
            f"Fetched {len(poi_data_list)} charging points. Parsing..."
        ))

        created_count = 0
        updated_count = 0
        skipped_count = 0
        operator_cache = {}
        connector_cache = {}

        for poi_data in poi_data_list:
            parsed = client.parse_poi(poi_data)
            if not parsed:
                skipped_count += 1
                continue

            if dry_run:
                created_count += 1
                continue

            with transaction.atomic():
                # Handle operator
                operator_name = parsed["operator_name"]
                operator = None
                if operator_name:
                    if operator_name in operator_cache:
                        operator = operator_cache[operator_name]
                    else:
                        operator, _ = Operator.objects.get_or_create(
                            ocm_operator_id=parsed.get("ocm_operator_id"),
                            defaults={"name": operator_name},
                        )
                        if operator.name != operator_name:
                            operator.name = operator_name
                            operator.save()
                        operator_cache[operator_name] = operator

                # Create or update charging point
                existing = ChargingPoint.objects.filter(
                    ocm_id=parsed["ocm_id"]
                ).first()

                if existing and not update_existing:
                    skipped_count += 1
                    continue

                defaults = {
                    "name": parsed["name"],
                    "lat": parsed["lat"],
                    "lon": parsed["lon"],
                    "address": parsed["address"],
                    "town": parsed["town"],
                    "county": parsed["county"],
                    "postcode": parsed["postcode"],
                    "country": parsed["country"],
                    "country_code": parsed["country_code"],
                    "operator": operator,
                    "operator_name": operator_name,
                    "connection_type": parsed["connection_type"],
                    "connector_types": parsed["connector_types"],
                    "power_kw": parsed["power_kw"],
                    "max_power_kw": parsed["max_power_kw"],
                    "number_of_points": parsed["number_of_points"],
                    "usage_type": parsed["usage_type"],
                    "access_type": parsed["access_type"],
                    "cost_type": parsed["cost_type"],
                    "usage_cost": parsed["usage_cost"],
                    "is_live_status": parsed["is_live_status"],
                    "status": parsed["status"],
                    "last_verified": parsed["last_verified"],
                    "ocm_data": parsed["raw_data"],
                }

                if existing:
                    for key, val in defaults.items():
                        setattr(existing, key, val)
                    existing.save()
                    updated_count += 1
                    charging_point = existing
                else:
                    charging_point = ChargingPoint.objects.create(
                        ocm_id=parsed["ocm_id"], **defaults
                    )
                    created_count += 1

                # Handle connector types
                if parsed["connector_types"]:
                    for ct_name in parsed["connector_types"]:
                        if ct_name in connector_cache:
                            ct = connector_cache[ct_name]
                        else:
                            ct, _ = ConnectorType.objects.get_or_create(
                                name=ct_name,
                                defaults={"formal_name": ct_name},
                            )
                            connector_cache[ct_name] = ct
                        charging_point.connector_ids.add(ct)

        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete!\n"
            f"  Created: {created_count}\n"
            f"  Updated: {updated_count}\n"
            f"  Skipped: {skipped_count}\n"
            f"  Total processed: {len(poi_data_list)}"
        ))