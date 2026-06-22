"""
Models for UK Charge.
ChargingPoint, Operator, and ConnectorType models.
"""
import json
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings

# Use GIS if available, otherwise regular fields
if "django.contrib.gis" in settings.INSTALLED_APPS:
    from django.contrib.gis.db import models as gis_models
    LocationField = gis_models.PointField
else:
    LocationField = None


class Operator(models.Model):
    """Charging network operator (e.g., InstaVolt, GridCharge)."""
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    website = models.URLField(blank=True, default="")
    phone = models.CharField(max_length=100, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    logo_url = models.URLField(blank=True, default="")
    is_private = models.BooleanField(default=False)
    ocm_operator_id = models.IntegerField(null=True, blank=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("operator_detail", kwargs={"slug": self.slug})

    @property
    def charging_point_count(self):
        return self.chargingpoint_set.count()


class ConnectorType(models.Model):
    """Connector type (e.g., CCS, Type 2, CHAdeMO)."""
    name = models.CharField(max_length=255, unique=True)
    formal_name = models.CharField(max_length=255, blank=True, default="")
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    power_kw = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    ocm_connection_type_id = models.IntegerField(null=True, blank=True, db_index=True)
    icon_name = models.CharField(max_length=100, blank=True, default="plug")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ChargingPoint(models.Model):
    """A charging location from Open Charge Map."""
    STATUS_CHOICES = [
        ("available", "Available"),
        ("in_use", "In Use"),
        ("out_of_service", "Out of Service"),
        ("unknown", "Unknown"),
    ]

    ocm_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=500, db_index=True)
    slug = models.SlugField(max_length=600, blank=True, default="")

    # Location
    location = LocationField(srid=4326, null=True, blank=True) if LocationField else None
    lat = models.FloatField(db_index=True)
    lon = models.FloatField(db_index=True)
    address = models.CharField(max_length=500, blank=True, default="")
    town = models.CharField(max_length=255, blank=True, default="", db_index=True)
    county = models.CharField(max_length=255, blank=True, default="")
    postcode = models.CharField(max_length=20, blank=True, default="", db_index=True)
    country = models.CharField(max_length=100, default="GB", db_index=True)
    country_code = models.CharField(max_length=5, default="GB")

    # Operator
    operator = models.ForeignKey(
        Operator, on_delete=models.SET_NULL, null=True, blank=True
    )
    operator_name = models.CharField(max_length=255, blank=True, default="", db_index=True)

    # Connections / connectors
    connection_type = models.CharField(max_length=255, blank=True, default="")
    connector_types = models.JSONField(default=list, blank=True)
    connector_ids = models.ManyToManyField(ConnectorType, blank=True)

    # Power
    power_kw = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    max_power_kw = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    # Quantity
    number_of_points = models.IntegerField(default=1)

    # Usage / Access / Cost
    usage_type = models.CharField(max_length=255, blank=True, default="")
    access_type = models.CharField(max_length=255, blank=True, default="")
    cost_type = models.CharField(max_length=255, blank=True, default="")
    usage_cost = models.CharField(max_length=500, blank=True, default="")

    # Live status
    is_live_status = models.BooleanField(default=False)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="unknown", db_index=True
    )
    last_verified = models.DateTimeField(null=True, blank=True)
    last_status_update = models.DateTimeField(null=True, blank=True)

    # Metadata
    ocm_data = models.JSONField(default=dict, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["power_kw"]),
            models.Index(fields=["operator_name"]),
            models.Index(fields=["town"]),
            models.Index(fields=["postcode"]),
            models.Index(fields=["country"]),
            models.Index(fields=["is_live_status"]),
            models.Index(fields=["lat", "lon"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.town})" if self.town else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_base = f"{self.name}-{self.ocm_id}"
            self.slug = slugify(slug_base)[:600]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("point_detail", kwargs={"ocm_id": self.ocm_id})

    @property
    def coordinates(self):
        return (self.lat, self.lon)

    @property
    def has_live_status(self):
        return self.is_live_status and self.status != "unknown"

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, "Unknown")

    @property
    def status_color(self):
        return {
            "available": "green",
            "in_use": "amber",
            "out_of_service": "red",
            "unknown": "grey",
        }.get(self.status, "grey")

    @property
    def primary_connector(self):
        if self.connector_types:
            return self.connector_types[0]
        return self.connection_type

    @property
    def display_power(self):
        if self.max_power_kw:
            return f"{self.max_power_kw}kW"
        if self.power_kw:
            return f"{self.power_kw}kW"
        return "Unknown"

    @property
    def is_rapid(self):
        if self.max_power_kw and self.max_power_kw >= 50:
            return True
        if self.power_kw and self.power_kw >= 50:
            return True
        return False

    @property
    def is_ultra_rapid(self):
        if self.max_power_kw and self.max_power_kw >= 100:
            return True
        if self.power_kw and self.power_kw >= 100:
            return True
        return False

    @property
    def full_address(self):
        parts = [self.address, self.town, self.county, self.postcode]
        return ", ".join(p for p in parts if p)

    @property
    def json_ld(self):
        """JSON-LD structured data for SEO."""
        import json as _json
        data = {
            "@context": "https://schema.org",
            "@type": "ElectricVehicleChargingStation",
            "name": self.name,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": self.address,
                "addressLocality": self.town,
                "addressRegion": self.county,
                "postalCode": self.postcode,
                "addressCountry": self.country_code,
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": self.lat,
                "longitude": self.lon,
            },
            "numberOfStations": self.number_of_points,
        }
        if self.operator_name:
            data["operator"] = {
                "@type": "Organization",
                "name": self.operator_name,
            }
        if self.max_power_kw:
            data["maximumVehiclePower"] = f"{self.max_power_kw} kW"
        if self.usage_cost:
            data["priceRange"] = self.usage_cost
        if self.is_live_status:
            data["status"] = self.status_display
        return _json.dumps(data, indent=2)