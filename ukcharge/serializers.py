"""
DRF serializers for UK Charge.
"""
from rest_framework import serializers
from .models import ChargingPoint, Operator, ConnectorType


class ConnectorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorType
        fields = ["id", "name", "formal_name", "power_kw", "icon_name"]


class OperatorSerializer(serializers.ModelSerializer):
    charging_point_count = serializers.SerializerMethodField()

    class Meta:
        model = Operator
        fields = [
            "id", "name", "slug", "website", "phone", "logo_url",
            "is_private", "charging_point_count",
        ]

    def get_charging_point_count(self, obj):
        return obj.chargingpoint_set.count()


class ChargingPointSerializer(serializers.ModelSerializer):
    operator = OperatorSerializer(read_only=True)
    connector_ids = ConnectorTypeSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="status_display", read_only=True)
    status_color = serializers.CharField(read_only=True)
    display_power = serializers.CharField(read_only=True)
    is_rapid = serializers.BooleanField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = ChargingPoint
        fields = [
            "ocm_id", "name", "slug", "lat", "lon", "address", "town",
            "county", "postcode", "country", "country_code",
            "operator", "operator_name", "connection_type",
            "connector_types", "connector_ids",
            "power_kw", "max_power_kw", "number_of_points",
            "usage_type", "access_type", "cost_type", "usage_cost",
            "is_live_status", "status", "status_display", "status_color",
            "display_power", "is_rapid", "full_address",
            "last_verified", "last_status_update",
            "created", "updated", "url",
        ]

    def get_url(self, obj):
        return obj.get_absolute_url()


class ChargingPointListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""
    display_power = serializers.CharField(read_only=True)
    status_color = serializers.CharField(read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = ChargingPoint
        fields = [
            "ocm_id", "name", "lat", "lon", "town", "postcode",
            "operator_name", "connector_types", "power_kw", "max_power_kw",
            "number_of_points", "status", "display_power", "status_color",
            "is_live_status", "url",
        ]

    def get_url(self, obj):
        return obj.get_absolute_url()