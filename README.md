# UK Charge

A real-time UK EV charging point finder with live availability status, built with Django and modelled on bustimes.org's architecture.

## Features

- **Location-based search** — by postcode, lat/lon, or town
- **Interactive map** — all UK charging points with filters (connector, power, operator, status)
- **Charging point detail pages** — SEO-optimised landing pages per location
- **Operator pages** — per-operator listings with stats
- **Nearby search** — find chargers within X miles of your location
- **Journey planner** — find chargers along a route (basic version)
- **Live status** — available/in-use/out-of-service where data available
- **API** — DRF endpoints for integration
- **SEO** — sitemaps, structured data (JSON-LD), meta tags, per-location/operator pages
- **Dark mode** — dark-first design with toggle
- **Mobile-first** — responsive, big touch targets, sticky search
- **Fast** — sub-200ms TTFB target, cached API calls

## Tech Stack

- **Backend:** Django 5.x, Python 3.12+
- **Database:** PostgreSQL with PostGIS (Neon for production, SpatiaLite for dev)
- **Frontend:** HTMX, MapLibre GL, Inter font
- **Data:** Open Charge Map API (https://openchargemap.org)
- **Deployment:** Vercel (serverless), Whitenoise for static files

## Quick Start

### Prerequisites

- Python 3.12+
- An OCM API key (free — get one at https://openchargemap.org/site/loginprovider/)
- (Optional) Neon PostgreSQL account for production

### Setup

1. **Clone and install:**
   ```bash
   cd ~/Projects/uk-charge
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OCM API key
   ```

3. **Database:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Import data:**
   ```bash
   python manage.py import_chargepoints --max 5000
   ```

5. **Run:**
   ```bash
   python manage.py runserver
   ```

Visit http://127.0.0.1:8000

## Management Commands

### Import charging points
```bash
python manage.py import_chargepoints --max 5000
python manage.py import_chargepoints --update  # Update existing
python manage.py import_chargepoints --dry-run  # Test without saving
python manage.py import_chargepoints --offset 5000 --max 5000  # Pagination
```

### Update live status
```bash
python manage.py update_live_status --limit 500
python manage.py update_live_status --ocm-id 12345  # Specific point
python manage.py update_live_status --all  # All points, not just live ones
```

## URL Structure

| URL | Description |
|-----|-------------|
| `/` | Homepage with search, map preview, stats |
| `/map/` | Full-screen map with filters |
| `/search/?q=` | Search by postcode/town/operator |
| `/nearby/?lat=&lon=&radius=` | Nearby chargers |
| `/points/` | All charging points (paginated) |
| `/points/{ocm_id}/` | Charging point detail (SEO page) |
| `/operators/` | All operators |
| `/operators/{slug}/` | Per-operator page (SEO) |
| `/journey/` | Journey planner |
| `/api/points/` | DRF API (paginated, filterable) |
| `/api/nearby/` | DRF API for nearby search |
| `/sitemap.xml` | XML sitemap |
| `/robots.txt` | Robots.txt |

## API Endpoints

### GET `/api/points/`
Paginated list of charging points with filters:
- `status` — available, in_use, out_of_service, unknown
- `town` — filter by town
- `operator_name` — filter by operator
- `power_kw__gte` — minimum power
- `search` — full-text search
- `ordering` — created, updated, power_kw, name, town

### GET `/api/points/{ocm_id}/`
Single charging point detail.

### GET `/api/nearby/?lat=&lon=&radius=&limit=`
Nearby search returning sorted results by distance.

### GET `/api/map-data/`
GeoJSON for map rendering with optional filters.

## Deployment

### Vercel

1. Push to GitHub
2. Import to Vercel
3. Set environment variables:
   - `SECRET_KEY` — Django secret key
   - `DEBUG` — False
   - `ALLOWED_HOSTS` — your domain
   - `DATABASE_URL` — Neon Postgres URL (with PostGIS)
   - `OCM_API_KEY` — your Open Charge Map key
   - `VERCEL` — 1
4. Deploy

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Set `SECRET_KEY` to a strong random value
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up Neon PostgreSQL with PostGIS extension
- [ ] Run `import_chargepoints` to populate data
- [ ] Set up cron job for `update_live_status` (e.g., every 15 minutes)
- [ ] Configure CDN for static files (optional)

## Data Source

All charging point data comes from [Open Charge Map](https://openchargemap.org), a free, open-source, community-driven map of charging infrastructure.

Data is licensed under the Open Data Commons Open Database License (ODbL).

## Design

- **Font:** Inter (Google Fonts)
- **Background:** Dark #0A0A0A / Light white
- **Status colours:** Green (available), Amber (in-use), Red (out-of-service), Grey (unknown)
- **Power badges:** Ultra-rapid (100kW+), Rapid (50kW+), Fast (22kW+), Slow (<50kW)
- **Mobile-first:** 88% of traffic is mobile — big touch targets, sticky search

## License

MIT — see LICENSE file (if present). Data © Open Charge Map contributors.