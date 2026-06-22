"""
Custom template tags for UK Charge.
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def status_badge(status):
    """Render a status badge with appropriate colour."""
    colours = {
        "available": "badge-available",
        "in_use": "badge-in-use",
        "out_of_service": "badge-out-of-service",
        "unknown": "badge-unknown",
    }
    labels = {
        "available": "Available",
        "in_use": "In Use",
        "out_of_service": "Out of Service",
        "unknown": "Unknown",
    }
    css_class = colours.get(status, "badge-unknown")
    label = labels.get(status, "Unknown")
    return mark_safe(f'<span class="status-badge {css_class}">{label}</span>')


@register.simple_tag
def power_badge(power_kw):
    """Render a power output badge."""
    if not power_kw:
        return mark_safe('<span class="power-badge power-unknown">—</span>')
    power = float(power_kw)
    if power >= 100:
        css = "power-ultra"
    elif power >= 50:
        css = "power-rapid"
    elif power >= 22:
        css = "power-fast"
    else:
        css = "power-slow"
    return mark_safe(f'<span class="power-badge {css}">{power:g}kW</span>')


@register.simple_tag
def connector_badge(connector_type):
    """Render a connector type badge."""
    icons = {
        "CCS (Type 2)": "⚡",
        "Type 2 (Mennekes)": "🔌",
        "Type 1 (J1772)": "🔌",
        "CHAdeMO": "🔋",
        "Tesla (Model S/X)": "🚗",
        "Tesla Supercharger": "🚗",
        "Three Phase AC": "🔌",
    }
    icon = icons.get(connector_type, "🔌")
    return mark_safe(
        f'<span class="connector-badge">{icon} {connector_type}</span>'
    )


@register.simple_tag
def distance_badge(distance_km):
    """Format distance nicely."""
    if distance_km < 1:
        return f"{int(distance_km * 1000)}m"
    if distance_km < 10:
        return f"{distance_km:.1f}km"
    return f"{int(distance_km)}km"


@register.filter
def miles_from_km(km_value):
    """Convert km to miles."""
    if km_value is None:
        return ""
    return f"{km_value * 0.621371:.1f}mi"