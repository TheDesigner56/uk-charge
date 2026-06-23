"""
Seed UK charging points data — no API key required.
Major charging locations from well-known UK networks.
"""
from django.core.management.base import BaseCommand
from ukcharge.models import ChargingPoint, Operator, ConnectorType

SEED_OPERATORS = [
    {"name": "InstaVolt", "website": "https://instavolt.co.uk", "phone": "0800 024 6359",
     "ocm_operator_id": 34, "is_private": False},
    {"name": "GridServe", "website": "https://gridserve.com", "phone": "0800 042 1444",
     "ocm_operator_id": 223, "is_private": False},
    {"name": "Pod Point", "website": "https://pod-point.com", "phone": "020 7247 4114",
     "ocm_operator_id": 1, "is_private": False},
    {"name": "BP Pulse", "website": "https://bppulse.co.uk", "phone": "0330 016 5614",
     "ocm_operator_id": 2, "is_private": False},
    {"name": "Char.gy", "website": "https://char.gy", "phone": "0800 024 6265",
     "ocm_operator_id": 56, "is_private": False},
    {"name": "Osprey Charging", "website": "https://ospreycharging.co.uk", "phone": "0800 046 3666",
     "ocm_operator_id": 140, "is_private": False},
    {"name": "FastNed", "website": "https://fastned.co.uk", "phone": "020 3880 0600",
     "ocm_operator_id": 36, "is_private": False},
    {"name": "Tesla Supercharger", "website": "https://tesla.com", "phone": "",
     "ocm_operator_id": 33, "is_private": False},
    {"name": "Ecotricity / Electric Highway", "website": "https://ecotricity.co.uk", "phone": "0800 032 7540",
     "ocm_operator_id": 4, "is_private": False},
    {"name": "GeniePoint", "website": "https://geniepoint.co.uk", "phone": "0330 024 9310",
     "ocm_operator_id": 7, "is_private": False},
]

SEED_CHARGE_POINTS = [
    # London
    {"name": "InstaVolt - London Lewisham", "lat": 51.4635, "lon": -0.0068, "address": "Loampit Lane", "town": "London", "county": "Greater London", "postcode": "SE13 7ET", "operator_name": "InstaVolt", "connection_type": "CCS", "power_kw": 150, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.79/kWh"},
    {"name": "GridServe - London Heathrow T5", "lat": 51.4700, "lon": -0.4543, "address": "Heathrow Airport Terminal 5", "town": "London", "county": "Greater London", "postcode": "TW6 2GW", "operator_name": "GridServe", "connection_type": "CCS", "power_kw": 350, "number_of_points": 6, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.85/kWh"},
    {"name": "Pod Point - London Westfield", "lat": 51.5069, "lon": -0.2218, "address": "Westfield Shopping Centre", "town": "London", "county": "Greater London", "postcode": "W12 7SL", "operator_name": "Pod Point", "connection_type": "Type 2", "power_kw": 7.4, "number_of_points": 8, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "Free"},
    {"name": "BP Pulse - London Canary Wharf", "lat": 51.5035, "lon": -0.0189, "address": "Canada Square", "town": "London", "county": "Greater London", "postcode": "E14 5AB", "operator_name": "BP Pulse", "connection_type": "CCS", "power_kw": 50, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.55/kWh"},

    # Birmingham
    {"name": "InstaVolt - Birmingham Bullring", "lat": 52.4759, "lon": -1.8908, "address": "Bullring Shopping Centre", "town": "Birmingham", "county": "West Midlands", "postcode": "B5 4BG", "operator_name": "InstaVolt", "connection_type": "CCS", "power_kw": 120, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.79/kWh"},
    {"name": "GridServe - Birmingham NEC", "lat": 52.4524, "lon": -1.7180, "address": "National Exhibition Centre", "town": "Birmingham", "county": "West Midlands", "postcode": "B40 1NT", "operator_name": "GridServe", "connection_type": "CCS", "power_kw": 350, "number_of_points": 6, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.85/kWh"},

    # Manchester
    {"name": "InstaVolt - Manchester Trafford Centre", "lat": 53.4641, "lon": -2.3430, "address": "Trafford Centre", "town": "Manchester", "county": "Greater Manchester", "postcode": "M17 8AA", "operator_name": "InstaVolt", "connection_type": "CCS", "power_kw": 150, "number_of_points": 6, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.79/kWh"},
    {"name": "BP Pulse - Manchester Piccadilly", "lat": 53.4773, "lon": -2.2304, "address": "Piccadilly Station", "town": "Manchester", "county": "Greater Manchester", "postcode": "M1 2PB", "operator_name": "BP Pulse", "connection_type": "CCS", "power_kw": 50, "number_of_points": 2, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.55/kWh"},

    # Leeds
    {"name": "Osprey Charging - Leeds Kirkgate", "lat": 53.7956, "lon": -1.5491, "address": "Kirkgate Market", "town": "Leeds", "county": "West Yorkshire", "postcode": "LS2 7HY", "operator_name": "Osprey Charging", "connection_type": "CCS", "power_kw": 150, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.69/kWh"},

    # Bristol
    {"name": "InstaVolt - Bristol Cribbs Causeway", "lat": 51.5410, "lon": -2.5683, "address": "The Mall at Cribbs Causeway", "town": "Bristol", "county": "Bristol", "postcode": "BS34 5DG", "operator_name": "InstaVolt", "connection_type": "CCS", "power_kw": 120, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.79/kWh"},
    {"name": "Pod Point - Bristol Temple Meads", "lat": 51.4490, "lon": -2.5767, "address": "Temple Meads Station", "town": "Bristol", "county": "Bristol", "postcode": "BS1 6QF", "operator_name": "Pod Point", "connection_type": "Type 2", "power_kw": 7.4, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "Free"},

    # Edinburgh
    {"name": "GridServe - Edinburgh Airport", "lat": 55.9500, "lon": -3.3725, "address": "Edinburgh Airport", "town": "Edinburgh", "county": "City of Edinburgh", "postcode": "EH12 9DN", "operator_name": "GridServe", "connection_type": "CCS", "power_kw": 350, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.85/kWh"},
    {"name": "Char.gy - Edinburgh Princes Street", "lat": 55.9532, "lon": -3.1904, "address": "Princes Street", "town": "Edinburgh", "county": "City of Edinburgh", "postcode": "EH2 2EQ", "operator_name": "Char.gy", "connection_type": "Type 2", "power_kw": 7.4, "number_of_points": 6, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.35/kWh"},

    # Glasgow
    {"name": "InstaVolt - Glasgow Silverburn", "lat": 55.8120, "lon": -4.3180, "address": "Silverburn Shopping Centre", "town": "Glasgow", "county": "Glasgow City", "postcode": "G53 6AG", "operator_name": "InstaVolt", "connection_type": "CCS", "power_kw": 150, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.79/kWh"},

    # Liverpool
    {"name": "BP Pulse - Liverpool One", "lat": 53.4071, "lon": -2.9790, "address": "Liverpool ONE Shopping Centre", "town": "Liverpool", "county": "Merseyside", "postcode": "L1 8AF", "operator_name": "BP Pulse", "connection_type": "CCS", "power_kw": 50, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.55/kWh"},

    # Newcastle
    {"name": "FastNed - Newcastle Metro Centre", "lat": 54.9693, "lon": -1.6140, "address": "Metro Centre", "town": "Newcastle upon Tyne", "county": "Tyne and Wear", "postcode": "NE11 9XY", "operator_name": "FastNed", "connection_type": "CCS", "power_kw": 300, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.69/kWh"},

    # Sheffield
    {"name": "Osprey Charging - Sheffield Meadowhall", "lat": 53.4117, "lon": -1.4607, "address": "Meadowhall Shopping Centre", "town": "Sheffield", "county": "South Yorkshire", "postcode": "S9 1EP", "operator_name": "Osprey Charging", "connection_type": "CCS", "power_kw": 150, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.69/kWh"},

    # Cambridge
    {"name": "Pod Point - Cambridge Grand Arcade", "lat": 52.2080, "lon": 0.1310, "address": "Grand Arcade Shopping Centre", "town": "Cambridge", "county": "Cambridgeshire", "postcode": "CB2 3BJ", "operator_name": "Pod Point", "connection_type": "Type 2", "power_kw": 7.4, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "Free"},

    # Brighton
    {"name": "Char.gy - Brighton Seafront", "lat": 50.8290, "lon": -0.1410, "address": "Marine Parade", "town": "Brighton", "county": "East Sussex", "postcode": "BN2 1TA", "operator_name": "Char.gy", "connection_type": "Type 2", "power_kw": 7.4, "number_of_points": 8, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.35/kWh"},

    # Oxford
    {"name": "Tesla Supercharger - Oxford Supercharger", "lat": 51.7360, "lon": -1.2490, "address": "Oxford Services", "town": "Oxford", "county": "Oxfordshire", "postcode": "OX2 8JD", "operator_name": "Tesla Supercharger", "connection_type": "CCS", "power_kw": 250, "number_of_points": 8, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.60/kWh"},

    # Reading
    {"name": "InstaVolt - Reading Oracle", "lat": 51.4614, "lon": -0.9740, "address": "The Oracle Shopping Centre", "town": "Reading", "county": "Berkshire", "postcode": "RG1 2EG", "operator_name": "InstaVolt", "connection_type": "CCS", "power_kw": 120, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.79/kWh"},

    # Southampton
    {"name": "BP Pulse - Southampton West Quay", "lat": 50.7120, "lon": -1.4140, "address": "WestQuay Shopping Centre", "town": "Southampton", "county": "Hampshire", "postcode": "SO15 1QD", "operator_name": "BP Pulse", "connection_type": "CCS", "power_kw": 50, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.55/kWh"},

    # Exeter
    {"name": "GridServe - Exeter Services", "lat": 50.7330, "lon": -3.5430, "address": "Exeter Services M5", "town": "Exeter", "county": "Devon", "postcode": "EX2 5TL", "operator_name": "GridServe", "connection_type": "CCS", "power_kw": 350, "number_of_points": 6, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.85/kWh"},

    # York
    {"name": "Osprey Charging - York Designer Outlet", "lat": 53.9577, "lon": -1.0940, "address": "York Designer Outlet", "town": "York", "county": "North Yorkshire", "postcode": "YO19 4TA", "operator_name": "Osprey Charging", "connection_type": "CCS", "power_kw": 150, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.69/kWh"},

    # Nottingham
    {"name": "Pod Point - Nottingham Victoria Centre", "lat": 52.9480, "lon": -1.1390, "address": "Victoria Shopping Centre", "town": "Nottingham", "county": "Nottinghamshire", "postcode": "NG1 3QN", "operator_name": "Pod Point", "connection_type": "Type 2", "power_kw": 7.4, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "Free"},

    # Motorway services
    {"name": "GridServe - Watford Gap Services M1", "lat": 52.3450, "lon": -1.1480, "address": "Watford Gap Services M1", "town": "Daventry", "county": "Northamptonshire", "postcode": "NN11 6DT", "operator_name": "GridServe", "connection_type": "CCS", "power_kw": 350, "number_of_points": 6, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.85/kWh"},
    {"name": "FastNed - Banbury Services M40", "lat": 52.0680, "lon": -1.3170, "address": "Banbury Services M40", "town": "Banbury", "county": "Oxfordshire", "postcode": "OX16 9AH", "operator_name": "FastNed", "connection_type": "CCS", "power_kw": 300, "number_of_points": 4, "status": "available", "usage_type": "Public", "access_type": "Public", "usage_cost": "£0.69/kWh"},
]

SEED_CONNECTORS = [
    {"name": "CCS", "formal_name": "Combined Charging System (CCS/Type 2)", "power_kw": 350},
    {"name": "Type 2", "formal_name": "Type 2 (Mennekes)", "power_kw": 22},
    {"name": "CHAdeMO", "formal_name": "CHAdeMO", "power_kw": 100},
    {"name": "Type 1", "formal_name": "Type 1 (J1772)", "power_kw": 7.4},
]


class Command(BaseCommand):
    help = 'Seed UK charging point data without requiring an API key.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding.')

    def handle(self, *args, **options):
        if options['clear']:
            ChargingPoint.objects.all().delete()
            Operator.objects.all().delete()
            ConnectorType.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all existing data.'))

        # Create operators
        op_cache = {}
        for op_data in SEED_OPERATORS:
            from django.utils.text import slugify
            op, _ = Operator.objects.get_or_create(
                ocm_operator_id=op_data.get("ocm_operator_id"),
                defaults={
                    "name": op_data["name"],
                    "website": op_data.get("website", ""),
                    "phone": op_data.get("phone", ""),
                    "is_private": op_data.get("is_private", False),
                },
            )
            op_cache[op_data["name"]] = op

        # Create connector types
        conn_cache = {}
        for ct_data in SEED_CONNECTORS:
            ct, _ = ConnectorType.objects.get_or_create(
                name=ct_data["name"],
                defaults={"formal_name": ct_data.get("formal_name", ""), "power_kw": ct_data.get("power_kw")},
            )
            conn_cache[ct_data["name"]] = ct

        # Create charging points
        created = 0
        for i, cp_data in enumerate(SEED_CHARGE_POINTS, 1):
            operator = op_cache.get(cp_data.get("operator_name"))
            cp = ChargingPoint.objects.create(
                ocm_id=10000 + i,
                name=cp_data["name"],
                lat=cp_data["lat"],
                lon=cp_data["lon"],
                address=cp_data.get("address", ""),
                town=cp_data.get("town", ""),
                county=cp_data.get("county", ""),
                postcode=cp_data.get("postcode", ""),
                country="United Kingdom",
                country_code="GB",
                operator=operator,
                operator_name=cp_data.get("operator_name", ""),
                connection_type=cp_data.get("connection_type", ""),
                power_kw=cp_data.get("power_kw", 0),
                max_power_kw=cp_data.get("power_kw", 0),
                number_of_points=cp_data.get("number_of_points", 1),
                usage_type=cp_data.get("usage_type", "Public"),
                access_type=cp_data.get("access_type", "Public"),
                cost_type="Per kWh" if "kWh" in cp_data.get("usage_cost", "") else "Free" if "Free" in cp_data.get("usage_cost", "") else "Unknown",
                usage_cost=cp_data.get("usage_cost", ""),
                is_live_status=False,
                status=cp_data.get("status", "available"),
            )
            # Link connector type
            ct = conn_cache.get(cp_data.get("connection_type"))
            if ct:
                cp.connector_ids.add(ct)
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {created} charging points, {len(SEED_OPERATORS)} operators, {len(SEED_CONNECTORS)} connector types.'
        ))
