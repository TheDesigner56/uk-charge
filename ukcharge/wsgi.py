"""WSGI config for UK Charge."""
import os
import shutil
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ukcharge.settings")

# On Vercel: set up SQLite in /tmp (writable) and load seed data on cold start
if os.environ.get("VERCEL"):
    import django
    django.setup()
    from django.core.management import call_command
    
    # Run migrations (creates tables in /tmp/db.sqlite3)
    try:
        call_command("migrate", "--run-syncdb", verbosity=0, interactive=False)
    except Exception as e:
        import logging
        logging.getLogger("ukcharge").error(f"Auto-migrate failed: {e}")
    
    # Load seed data if DB is empty
    try:
        from ukcharge.models import ChargingPoint
        if ChargingPoint.objects.count() == 0:
            call_command("loaddata", "ukcharge/fixtures/seed_data.json", verbosity=0)
            import logging
            logging.getLogger("ukcharge").info(f"Loaded {ChargingPoint.objects.count()} charge points from fixture")
    except Exception as e:
        import logging
        logging.getLogger("ukcharge").error(f"Load fixture failed: {e}")

from django.core.wsgi import get_wsgi_application  # noqa: E402
application = get_wsgi_application()