"""
Views for UK Charge.
"""
import math
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db.models import Q, Count, Avg, Max
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import ChargingPoint, Operator, ConnectorType
from .services import ocm_client

logger = logging.getLogger("ukcharge")

# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_stats():
    """Cached aggregate stats for the site."""
    cached = cache.get("uk_charge_stats")
    if cached:
        return cached
    total = ChargingPoint.objects.count()
    live_count = ChargingPoint.objects.filter(is_live_status=True).count()
    available = ChargingPoint.objects.filter(status="available").count()
    operators = Operator.objects.count()
    rapid_count = ChargingPoint.objects.filter(power_kw__gte=50).count()
    ultra_rapid = ChargingPoint.objects.filter(power_kw__gte=100).count()
    towns = (
        ChargingPoint.objects.exclude(town="")
        .values_list("town", flat=True)
        .distinct()
        .count()
    )
    stats = {
        "total": total,
        "live_count": live_count,
        "available": available,
        "operators": operators,
        "rapid_count": rapid_count,
        "ultra_rapid_count": ultra_rapid,
        "towns": towns,
    }
    cache.set("uk_charge_stats", stats, 300)
    return stats


def get_nearby_points(lat, lon, radius_miles=10, limit=50):
    """Find charging points within radius_miles of lat/lon."""
    radius_km = radius_miles * 1.60934
    lat_diff = radius_km / 111.0
    lon_diff = radius_km / (111.0 * math.cos(math.radians(lat)))

    points = ChargingPoint.objects.filter(
        lat__range=(lat - lat_diff, lat + lat_diff),
        lon__range=(lon - lon_diff, lon + lon_diff),
        country_code="GB",
    )
    scored = []
    for p in points:
        dist = haversine(lat, lon, p.lat, p.lon)
        if dist <= radius_km:
            scored.append((p, dist))
    scored.sort(key=lambda x: x[1])
    return scored[:limit]


# ──────────────────────────────────────────────
# Page Views
# ──────────────────────────────────────────────

def homepage(request):
    """Homepage with hero search, map preview, stats, and nearby chargers."""
    stats = get_stats()
    recent_points = ChargingPoint.objects.filter(country_code="GB").order_by("-created")[:6]
    top_operators = Operator.objects.annotate(
        point_count=Count("chargingpoint")
    ).order_by("-point_count")[:8]
    connector_types = ConnectorType.objects.all().order_by("name")

    context = {
        "stats": stats,
        "recent_points": recent_points,
        "top_operators": top_operators,
        "connector_types": connector_types,
        "meta_title": "UK Charge — Find EV Charging Points Near You",
        "meta_description": (
            "Find electric vehicle charging points across the UK. "
            "Real-time availability, filters by connector type, power output, and operator. "
            f"Search {stats['total']}+ charging locations nationwide."
        ),
        "og_title": "UK Charge — EV Charging Point Finder",
        "og_description": "Find EV charging points near you with live availability status.",
    }
    return render(request, "ukcharge/homepage.html", context)


def map_view(request):
    """Full-screen map with sidebar filters."""
    connector_types = ConnectorType.objects.all().order_by("name")
    operators = Operator.objects.values_list("name", flat=True).order_by("name").distinct()

    context = {
        "connector_types": connector_types,
        "operators": list(operators),
        "meta_title": "Map of UK EV Charging Points — UK Charge",
        "meta_description": "Interactive map of all UK electric vehicle charging points with filters.",
    }
    return render(request, "ukcharge/map.html", context)


def search_results(request):
    """Search by postcode, town, or operator name."""
    query = request.GET.get("q", "").strip()
    results = []
    total = 0

    if query:
        q_obj = Q(name__icontains=query) | Q(town__icontains=query) | \
               Q(postcode__icontains=query) | Q(operator_name__icontains=query) | \
               Q(county__icontains=query)
        qs = ChargingPoint.objects.filter(q_obj, country_code="GB")
        total = qs.count()
        paginator = Paginator(qs, 20)
        page_num = request.GET.get("page", 1)
        results = paginator.get_page(page_num)

    context = {
        "query": query,
        "results": results,
        "total": total,
        "meta_title": f"Search: {query} — UK Charge" if query else "Search — UK Charge",
        "meta_description": "Search UK EV charging points by location, postcode, or operator.",
    }
    return render(request, "ukcharge/search_results.html", context)


def nearby_results(request):
    """Nearby chargers by lat/lon with radius."""
    try:
        lat = float(request.GET.get("lat", 0))
        lon = float(request.GET.get("lon", 0))
    except (ValueError, TypeError):
        lat, lon = 51.5074, -0.1278  # Default to London

    try:
        radius = float(request.GET.get("radius", "10"))
    except (ValueError, TypeError):
        radius = 10

    if not lat or not lon:
        # Try geolocation from request
        return render(request, "ukcharge/nearby_results.html", {
            "results": [],
            "lat": 0, "lon": 0, "radius": radius,
            "needs_location": True,
            "meta_title": "Nearby EV Charging Points — UK Charge",
            "meta_description": "Find EV charging points near your location.",
        })

    scored = get_nearby_points(lat, lon, radius, limit=50)
    results = [
        {"point": p, "distance_km": round(d, 2), "distance_miles": round(d * 0.621371, 2)}
        for p, d in scored
    ]

    context = {
        "results": results,
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "needs_location": False,
        "total": len(results),
        "meta_title": f"EV Chargers within {radius} miles — UK Charge",
        "meta_description": f"Find EV charging points within {radius} miles of your location.",
    }
    return render(request, "ukcharge/nearby_results.html", context)


def point_detail(request, ocm_id):
    """Charging point detail page — main SEO landing page."""
    point = get_object_or_404(ChargingPoint, ocm_id=ocm_id)
    nearby = get_nearby_points(point.lat, point.lon, radius_miles=5, limit=10)
    nearby = [{"point": p, "distance_km": round(d, 2), "distance_miles": round(d * 0.621371, 2)} for p, d in nearby if p.ocm_id != ocm_id]

    context = {
        "point": point,
        "nearby": nearby[:6],
        "json_ld": point.json_ld,
        "meta_title": f"{point.name} — EV Charging Point — UK Charge",
        "meta_description": f"EV charging at {point.name}, {point.town}. {point.display_power} {point.primary_connector}. {point.number_of_points} charging point(s). Live status available.",
        "og_title": f"{point.name} — EV Charging Point",
        "og_description": f"Charging at {point.town}. {point.display_power}, {point.primary_connector}.",
    }
    return render(request, "ukcharge/point_detail.html", context)


def point_list(request):
    """All charging points, paginated."""
    qs = ChargingPoint.objects.filter(country_code="GB").order_by("-created")
    paginator = Paginator(qs, 30)
    page_num = request.GET.get("page", 1)
    page = paginator.get_page(page_num)

    context = {
        "page": page,
        "meta_title": "All UK EV Charging Points — UK Charge",
        "meta_description": "Browse all UK electric vehicle charging points. Complete directory with filters.",
    }
    return render(request, "ukcharge/point_list.html", context)


def operator_list(request):
    """All operators list."""
    operators = Operator.objects.annotate(
        point_count=Count("chargingpoint")
    ).filter(point_count__gt=0).order_by("-point_count")

    context = {
        "operators": operators,
        "meta_title": "EV Charging Operators in the UK — UK Charge",
        "meta_description": "Browse all UK EV charging network operators. Find charging points by operator.",
    }
    return render(request, "ukcharge/operator_list.html", context)


def operator_detail(request, slug):
    """Per-operator page with all their charge points — SEO page."""
    operator = get_object_or_404(Operator, slug=slug)
    qs = ChargingPoint.objects.filter(operator=operator, country_code="GB")
    total = qs.count()
    paginator = Paginator(qs, 30)
    page_num = request.GET.get("page", 1)
    page = paginator.get_page(page_num)

    # Stats for this operator
    live_count = qs.filter(is_live_status=True).count()
    rapid_count = qs.filter(power_kw__gte=50).count()
    avg_power = qs.aggregate(avg=Avg("power_kw"))["avg"] or 0
    max_power = qs.aggregate(mx=Max("power_kw"))["mx"] or 0

    context = {
        "operator": operator,
        "page": page,
        "total": total,
        "live_count": live_count,
        "rapid_count": rapid_count,
        "avg_power": round(avg_power, 1) if avg_power else 0,
        "max_power": round(max_power, 1) if max_power else 0,
        "meta_title": f"{operator.name} EV Charging Points — UK Charge",
        "meta_description": f"All {total} {operator.name} charging points in the UK. Find nearby {operator.name} EV chargers.",
        "og_title": f"{operator.name} EV Charging Points",
        "og_description": f"{total} charging points across the UK on the {operator.name} network.",
    }
    return render(request, "ukcharge/operator_detail.html", context)


def journey_planner(request):
    """Basic journey planner: find chargers along a route."""
    context = {
        "meta_title": "Journey Planner — Find EV Chargers Along Your Route — UK Charge",
        "meta_description": "Plan your EV journey and find charging points along your route across the UK.",
    }
    return render(request, "ukcharge/journey_planner.html", context)


@require_http_methods(["GET"])
def journey_search(request):
    """AJAX endpoint for journey planner."""
    try:
        start_lat = float(request.GET.get("start_lat"))
        start_lon = float(request.GET.get("start_lon"))
        end_lat = float(request.GET.get("end_lat"))
        end_lon = float(request.GET.get("end_lon"))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid coordinates"}, status=400)

    # Sample points along the route
    num_samples = 10
    corridor_width_km = 10  # Search within 10km of the route line

    results = []
    for i in range(num_samples + 1):
        t = i / num_samples
        lat = start_lat + (end_lat - start_lat) * t
        lon = start_lon + (end_lon - start_lon) * t
        nearby = get_nearby_points(lat, lon, radius_miles=corridor_width_km * 0.621371, limit=20)
        for p, d in nearby:
            if p.ocm_id not in [r["ocm_id"] for r in results]:
                results.append({
                    "ocm_id": p.ocm_id,
                    "name": p.name,
                    "lat": p.lat,
                    "lon": p.lon,
                    "town": p.town,
                    "power_kw": float(p.power_kw) if p.power_kw else None,
                    "status": p.status,
                    "connector_types": p.connector_types,
                    "distance_km": round(d, 2),
                    "url": p.get_absolute_url(),
                })

    results.sort(key=lambda x: x["distance_km"])
    return JsonResponse({"results": results[:50], "count": len(results)})


# ──────────────────────────────────────────────
# HTMX endpoints
# ──────────────────────────────────────────────

def htmx_map_points(request):
    """Return GeoJSON of charging points for map (HTMX/AJAX)."""
    bounds = request.GET.get("bounds", "")
    status_filter = request.GET.get("status", "")
    connector_filter = request.GET.get("connector", "")
    power_filter = request.GET.get("power", "")
    operator_filter = request.GET.get("operator", "")

    qs = ChargingPoint.objects.filter(country_code="GB")

    if status_filter and status_filter != "all":
        qs = qs.filter(status=status_filter)
    if connector_filter and connector_filter != "all":
        qs = qs.filter(connector_types__icontains=connector_filter)
    if power_filter == "rapid":
        qs = qs.filter(power_kw__gte=50)
    elif power_filter == "ultra":
        qs = qs.filter(power_kw__gte=100)
    elif power_filter == "slow":
        qs = qs.filter(power_kw__lt=50)
    if operator_filter and operator_filter != "all":
        qs = qs.filter(operator_name__icontains=operator_filter)

    # Bounds filtering: "sw_lat,sw_lon,ne_lat,ne_lon"
    if bounds:
        try:
            parts = bounds.split(",")
            if len(parts) == 4:
                sw_lat, sw_lon, ne_lat, ne_lon = [float(p) for p in parts]
                qs = qs.filter(
                    lat__range=(sw_lat, ne_lat),
                    lon__range=(sw_lon, ne_lon),
                )
        except (ValueError, IndexError):
            pass

    qs = qs[:2000]  # Cap for performance

    features = []
    for p in qs:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
            "properties": {
                "id": p.ocm_id,
                "name": p.name,
                "town": p.town,
                "status": p.status,
                "power": float(p.power_kw) if p.power_kw else None,
                "connectors": p.connector_types,
                "operator": p.operator_name,
                "url": p.get_absolute_url(),
                "number_of_points": p.number_of_points,
            },
        })

    return JsonResponse({
        "type": "FeatureCollection",
        "features": features,
    })


def htmx_nearby(request):
    """HTMX partial for nearby results."""
    try:
        lat = float(request.GET.get("lat"))
        lon = float(request.GET.get("lon"))
        radius = float(request.GET.get("radius", "10"))
    except (ValueError, TypeError):
        return HttpResponse("", status=400)

    scored = get_nearby_points(lat, lon, radius, limit=30)
    results = [
        {"point": p, "distance_km": round(d, 2), "distance_miles": round(d * 0.621371, 2)}
        for p, d in scored
    ]
    return render(request, "ukcharge/_nearby_partial.html", {
        "results": results, "total": len(results)
    })


def htmx_search(request):
    """HTMX partial for search results."""
    query = request.GET.get("q", "").strip()
    if not query:
        return HttpResponse("")
    q_obj = Q(name__icontains=query) | Q(town__icontains=query) | \
           Q(postcode__icontains=query) | Q(operator_name__icontains=query)
    qs = ChargingPoint.objects.filter(q_obj, country_code="GB")[:20]
    return render(request, "ukcharge/_search_partial.html", {
        "results": qs, "query": query
    })


def htmx_live_status(request, ocm_id):
    """HTMX endpoint to refresh live status for a charging point."""
    point = get_object_or_404(ChargingPoint, ocm_id=ocm_id)
    status_data = ocm_client.fetch_live_status(ocm_id)
    if status_data:
        point.status = status_data["status"]
        point.is_live_status = status_data["is_live"]
        point.last_status_update = status_data["last_update"]
        point.save(update_fields=["status", "is_live_status", "last_status_update", "updated"])
    return render(request, "ukcharge/_status_badge.html", {"point": point})


# ──────────────────────────────────────────────
# Error pages
# ──────────────────────────────────────────────

def custom_404(request, exception=None):
    return render(request, "ukcharge/404.html", {
        "meta_title": "Page Not Found — UK Charge"
    }, status=404)


def custom_500(request):
    return render(request, "ukcharge/500.html", {
        "meta_title": "Server Error — UK Charge"
    }, status=500)