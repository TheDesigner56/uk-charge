"""
Admin configuration for UK Charge.
"""
from django.contrib import admin
from .models import ChargingPoint, Operator, ConnectorType


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ["name", "website", "phone", "is_private", "charging_point_count"]
    list_filter = ["is_private"]
    search_fields = ["name", "website", "phone"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(ConnectorType)
class ConnectorTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "formal_name", "power_kw"]
    search_fields = ["name", "formal_name"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(ChargingPoint)
class ChargingPointAdmin(admin.ModelAdmin):
    list_display = [
        "ocm_id", "name", "town", "operator_name", "power_kw",
        "number_of_points", "status", "is_live_status", "updated",
    ]
    list_filter = [
        "status", "is_live_status", "country_code", "operator_name", "town",
    ]
    search_fields = ["name", "town", "postcode", "ocm_id", "operator_name"]
    list_editable = ["status"]
    readonly_fields = ["created", "updated", "slug"]
    filter_horizontal = ["connector_ids"]
    date_hierarchy = "created"

    fieldsets = (
        ("OCM Data", {
            "fields": ["ocm_id", "slug", "ocm_data"],
        }),
        ("Location", {
            "fields": ["name", "lat", "lon", "location", "address", "town", "county", "postcode", "country", "country_code"],
        }),
        ("Operator", {
            "fields": ["operator", "operator_name"],
        }),
        ("Connections", {
            "fields": ["connection_type", "connector_types", "connector_ids", "power_kw", "max_power_kw", "number_of_points"],
        }),
        ("Usage & Cost", {
            "fields": ["usage_type", "access_type", "cost_type", "usage_cost"],
        }),
        ("Live Status", {
            "fields": ["is_live_status", "status", "last_verified", "last_status_update"],
        }),
        ("Timestamps", {
            "fields": ["created", "updated"],
            "classes": ["collapse"],
        }),
    )