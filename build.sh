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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ukcharge.settings')

db_path = os.path.join(os.getcwd(), 'db.sqlite3')

import django
from django.conf import settings
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
    }
}
django.setup()
from django.core.management import call_command
call_command('migrate', '--noinput', verbosity=1)
call_command('loaddata', 'ukcharge/fixtures/seed_data.json', verbosity=1)
print(f'Database created at: {db_path}')
"

echo "Build complete."