"""
Project URL configuration for UK Charge.
"""
from django.urls import path, include
from django.contrib import admin
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from .sitemaps import sitemaps


urlpatterns = [
    path("admin/", admin.site.urls),

    # App URLs
    path("", include("ukcharge.app_urls")),

    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),

    # Robots
    path("robots.txt", lambda r: HttpResponse(
        "User-agent: *\nAllow: /\nSitemap: https://uk-charge.vercel.app/sitemap.xml\n",
        content_type="text/plain"
    ), name="robots"),
]

# Error handlers
handler404 = "ukcharge.views.custom_404"
handler500 = "ukcharge.views.custom_500"