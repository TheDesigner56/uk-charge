"""WSGI config for UK Charge."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ukcharge.settings")

# Auto-migrate on serverless cold start (SQLite in /tmp is ephemeral)
if os.environ.get("VERCEL"):
    import django
    django.setup()
    from django.core.management import call_command
    try:
        call_command("migrate", "--run-syncdb", verbosity=0, interactive=False)
    except Exception as e:
        import logging
        logging.getLogger("ukcharge").error(f"Auto-migrate failed: {e}")

from django.core.wsgi import get_wsgi_application  # noqa: E402
application = get_wsgi_application()