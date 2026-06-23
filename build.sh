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

echo "Build complete."