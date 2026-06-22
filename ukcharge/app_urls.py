"""
App-level URL configuration for UK Charge.
"""
from django.urls import path, include
from . import views

app_name = "ukcharge"

urlpatterns = [
    # Pages
    path("", views.homepage, name="homepage"),
    path("map/", views.map_view, name="map"),
    path("search/", views.search_results, name="search"),
    path("nearby/", views.nearby_results, name="nearby"),
    path("points/", views.point_list, name="point_list"),
    path("points/<int:ocm_id>/", views.point_detail, name="point_detail"),
    path("operators/", views.operator_list, name="operator_list"),
    path("operators/<slug:slug>/", views.operator_detail, name="operator_detail"),
    path("journey/", views.journey_planner, name="journey"),
    path("journey/search/", views.journey_search, name="journey_search"),

    # HTMX endpoints
    path("htmx/map-points/", views.htmx_map_points, name="htmx_map_points"),
    path("htmx/nearby/", views.htmx_nearby, name="htmx_nearby"),
    path("htmx/search/", views.htmx_search, name="htmx_search"),
    path("htmx/status/<int:ocm_id>/", views.htmx_live_status, name="htmx_live_status"),

    # API
    path("api/", include("ukcharge.api_urls")),
]