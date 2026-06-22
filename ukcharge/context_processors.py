"""
Context processors for UK Charge.
"""
from django.conf import settings


def ad_slots(request):
    """Provide ad slot configuration to all templates."""
    return {
        "ad_slots": {
            "header": "uk-charge-header",
            "sidebar": "uk-charge-sidebar",
            "footer": "uk-charge-footer",
            "inline": "uk-charge-inline",
        },
        "show_ads": not settings.DEBUG,
    }


def app_settings(request):
    """Provide app-wide settings to templates."""
    return {
        "OCM_BASE_URL": settings.OCM_BASE_URL,
        "IS_VERCEL": getattr(settings, "IS_VERCEL", False),
        "SITE_NAME": "UK Charge",
        "SITE_URL": "https://uk-charge.vercel.app",
    }