#!/bin/bash
# Vercel build script for UK Charge
set -e

echo "Running collectstatic..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ukcharge.settings')
import django
django.setup()
from django.core.management import call_command
call_command('collectstatic', '--noinput', verbosity=2)
"

echo "Running migrations and loading seed data into bundled SQLite..."
python -c "
import os
os.environ['BUILD_PHASE'] = '1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ukcharge.settings')

import django
from django.conf import settings
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/db.sqlite3',
    }
}
django.setup()
from django.core.management import call_command
call_command('migrate', '--noinput', verbosity=1)
call_command('loaddata', 'ukcharge/fixtures/seed_data.json', verbosity=1)
"

echo "Build complete."