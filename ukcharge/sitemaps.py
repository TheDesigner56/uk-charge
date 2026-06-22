"""
Sitemap definitions for UK Charge.
"""
from django.contrib.sitemaps import Sitemap
from .models import ChargingPoint, Operator


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0
    protocol = "https"

    def items(self):
        return [
            "ukcharge:homepage", "ukcharge:map", "ukcharge:point_list",
            "ukcharge:operator_list", "ukcharge:search", "ukcharge:journey",
            "ukcharge:nearby",
        ]

    def location(self, item):
        from django.urls import reverse
        return reverse(item)


class ChargingPointSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = "https"

    def items(self):
        return ChargingPoint.objects.filter(
            country_code="GB"
        ).only("ocm_id", "updated")

    def location(self, obj):
        return f"/points/{obj.ocm_id}/"

    def lastmod(self, obj):
        return obj.updated


class OperatorSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return Operator.objects.only("slug", "updated")

    def location(self, obj):
        return f"/operators/{obj.slug}/"

    def lastmod(self, obj):
        return obj.updated


sitemaps = {
    "static": StaticSitemap,
    "charging_points": ChargingPointSitemap,
    "operators": OperatorSitemap,
}