"""
DRF API views for UK Charge.
"""
import math
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from .models import ChargingPoint, Operator
from .serializers import (
    ChargingPointSerializer,
    ChargingPointListSerializer,
    OperatorSerializer,
)
from .views import haversine


class ChargingPointListView(generics.ListAPIView):
    """Paginated list of all charging points with filters."""
    serializer_class = ChargingPointListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "status": ["exact"],
        "operator_name": ["exact", "icontains"],
        "town": ["exact", "icontains"],
        "postcode": ["icontains"],
        "power_kw": ["gte", "lte"],
        "is_live_status": ["exact"],
        "country_code": ["exact"],
    }
    search_fields = ["name", "town", "postcode", "operator_name", "county"]
    ordering_fields = ["created", "updated", "power_kw", "name", "town"]
    ordering = ["-created"]

    def get_queryset(self):
        return ChargingPoint.objects.filter(country_code="GB").select_related("operator")


class ChargingPointDetailView(generics.RetrieveAPIView):
    """Single charging point detail."""
    serializer_class = ChargingPointSerializer
    lookup_field = "ocm_id"
    queryset = ChargingPoint.objects.select_related("operator").prefetch_related("connector_ids")


class NearbySearchView(APIView):
    """Nearby search API endpoint."""

    def get(self, request):
        try:
            lat = float(request.GET.get("lat"))
            lon = float(request.GET.get("lon"))
        except (ValueError, TypeError):
            return Response(
                {"error": "lat and lon parameters are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        radius_miles = float(request.GET.get("radius", "10"))
        limit = min(int(request.GET.get("limit", "50")), 200)
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

        results = []
        for p, d in scored[:limit]:
            results.append({
                "ocm_id": p.ocm_id,
                "name": p.name,
                "lat": p.lat,
                "lon": p.lon,
                "town": p.town,
                "postcode": p.postcode,
                "operator_name": p.operator_name,
                "power_kw": float(p.power_kw) if p.power_kw else None,
                "max_power_kw": float(p.max_power_kw) if p.max_power_kw else None,
                "connector_types": p.connector_types,
                "status": p.status,
                "number_of_points": p.number_of_points,
                "distance_km": round(d, 2),
                "distance_miles": round(d * 0.621371, 2),
                "url": p.get_absolute_url(),
            })

        return Response({
            "count": len(results),
            "lat": lat,
            "lon": lon,
            "radius_miles": radius_miles,
            "results": results,
        })


class OperatorListView(generics.ListAPIView):
    """List all operators."""
    serializer_class = OperatorSerializer
    queryset = Operator.objects.all().order_by("name")


class OperatorDetailView(generics.RetrieveAPIView):
    """Single operator detail."""
    serializer_class = OperatorSerializer
    lookup_field = "slug"
    queryset = Operator.objects.all()


class MapDataView(APIView):
    """GeoJSON data for map rendering."""

    def get(self, request):
        status_filter = request.GET.get("status", "")
        power_filter = request.GET.get("power", "")
        connector_filter = request.GET.get("connector", "")

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

        qs = qs[:3000]

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
                },
            })

        return Response({
            "type": "FeatureCollection",
            "count": len(features),
            "features": features,
        })