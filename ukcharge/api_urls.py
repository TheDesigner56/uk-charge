"""
API URL configuration for UK Charge DRF endpoints.
"""
from django.urls import path
from .api_views import (
    ChargingPointListView,
    ChargingPointDetailView,
    NearbySearchView,
    OperatorListView,
    OperatorDetailView,
    MapDataView,
)

urlpatterns = [
    path("points/", ChargingPointListView.as_view(), name="api_points"),
    path("points/<int:ocm_id>/", ChargingPointDetailView.as_view(), name="api_point_detail"),
    path("nearby/", NearbySearchView.as_view(), name="api_nearby"),
    path("operators/", OperatorListView.as_view(), name="api_operators"),
    path("operators/<slug:slug>/", OperatorDetailView.as_view(), name="api_operator_detail"),
    path("map-data/", MapDataView.as_view(), name="api_map_data"),
]