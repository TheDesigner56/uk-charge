"""
Open Charge Map API client service.
Handles fetching charging point data from the OCM v3 API.
"""
import logging
import requests
import time
from datetime import datetime, timezone
from django.core.cache import cache

logger = logging.getLogger("ukcharge")

OCM_BASE_URL = "https://api.openchargemap.io/v3"


class OCMAPIClient:
    """Client for the Open Charge Map v3 API with caching and error handling."""

    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or ""
        self.base_url = base_url or OCM_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "UK-Charge/1.0 (https://uk-charge.vercel.app)",
        })

    def _build_params(self, extra=None):
        params = {"key": self.api_key, "compact": "true", "verbose": "false"}
        if extra:
            params.update(extra)
        return params

    def _fetch(self, endpoint, params=None, cache_key=None, cache_ttl=300):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        full_params = self._build_params(params)
        if cache_key:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
        try:
            response = self.session.get(url, params=full_params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if cache_key:
                cache.set(cache_key, data, cache_ttl)
            return data
        except requests.exceptions.Timeout:
            logger.error(f"OCM API timeout for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"OCM API error for {url}: {e}")
            return None
        except ValueError as e:
            logger.error(f"OCM API JSON parse error for {url}: {e}")
            return None

    def fetch_uk_charge_points(self, max_results=5000, offset=0):
        """Fetch all UK charging points from OCM."""
        all_points = []
        batch_size = 200
        current_offset = offset
        remaining = max_results

        while remaining > 0:
            batch = min(batch_size, remaining)
            cache_key = f"ocm_uk_points_{current_offset}_{batch}"
            params = {
                "countrycode": "GB",
                "maxresults": str(batch),
                "offset": str(current_offset),
            }
            data = self._fetch("poi", params=params, cache_key=cache_key, cache_ttl=600)

            if data is None:
                logger.error(
                    f"Failed fetching batch at offset {current_offset}"
                )
                break
            if not data:
                logger.info("No more results from OCM")
                break

            all_points.extend(data)
            current_offset += len(data)
            remaining -= len(data)

            if len(data) < batch:
                logger.info(
                    f"Reached end of OCM results at offset {current_offset}"
                )
                break

            # Rate limiting
            time.sleep(0.3)

        logger.info(
            f"Fetched {len(all_points)} UK charge points from OCM"
        )
        return all_points

    def fetch_charge_point(self, ocm_id):
        """Fetch a single charging point by OCM ID."""
        cache_key = f"ocm_poi_{ocm_id}"
        params = {"chargepointid": str(ocm_id)}
        data = self._fetch("poi", params=params, cache_key=cache_key, cache_ttl=300)
        if data and len(data) > 0:
            return data[0]
        return None

    def fetch_nearby(self, lat, lon, distance_km=10, max_results=50):
        """Fetch nearby charging points by distance."""
        cache_key = f"ocm_nearby_{lat}_{lon}_{distance_km}_{max_results}"
        params = {
            "latitude": str(lat),
            "longitude": str(lon),
            "distance": str(distance_km),
            "distanceunit": "KM",
            "maxresults": str(max_results),
            "countrycode": "GB",
        }
        return self._fetch(
            "poi", params=params, cache_key=cache_key, cache_ttl=120
        )

    def fetch_operators(self, country_code="GB"):
        """Fetch all operators from OCM."""
        cache_key = f"ocm_operators_{country_code}"
        params = {"countrycode": country_code}
        return self._fetch(
            "referencedata", params=params, cache_key=cache_key, cache_ttl=3600
        )

    def fetch_live_status(self, ocm_id):
        """Fetch live status for a charging point."""
        cache_key = f"ocm_live_{ocm_id}"
        params = {
            "chargepointid": str(ocm_id),
            "includestatus": "true",
        }
        data = self._fetch(
            "poi", params=params, cache_key=cache_key, cache_ttl=60
        )
        if data and len(data) > 0:
            return self._parse_live_status(data[0])
        return None

    def _parse_live_status(self, poi_data):
        """Parse live status from OCM POI data."""
        status = "unknown"
        is_live = False
        last_update = None

        connections = poi_data.get("Connections", [])
        if connections:
            statuses = []
            for conn in connections:
                conn_status = conn.get("StatusType", {})
                if conn_status:
                    is_operational = conn_status.get("IsOperational", True)
                    is_user_selectable = conn_status.get(
                        "IsUserSelectable", False
                    )
                    title = conn_status.get("Title", "").lower()
                    if "operational" in title and is_operational:
                        statuses.append("available")
                    elif "in use" in title:
                        statuses.append("in_use")
                    elif not is_operational:
                        statuses.append("out_of_service")
                    else:
                        statuses.append("unknown")
                    is_live = True

            if statuses:
                if all(s == "available" for s in statuses):
                    status = "available"
                elif all(s == "out_of_service" for s in statuses):
                    status = "out_of_service"
                elif "in_use" in statuses:
                    status = "in_use"
                else:
                    status = "unknown"

        verified_date = poi_data.get("DateLastVerified")
        if verified_date:
            try:
                last_update = datetime.fromisoformat(
                    verified_date.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        return {
            "status": status,
            "is_live": is_live,
            "last_update": last_update,
        }

    def parse_poi(self, poi_data):
        """Parse a single OCM POI into our database format."""
        address_info = poi_data.get("AddressInfo", {}) or {}
        operator_info = poi_data.get("OperatorInfo", {}) or {}
        connections = poi_data.get("Connections", []) or []
        usage_type = poi_data.get("UsageType", {}) or {}
        status_type = poi_data.get("StatusType", {}) or {}
        media_items = poi_data.get("MediaItems", []) or []

        lat = address_info.get("Latitude")
        lon = address_info.get("Longitude")

        if lat is None or lon is None:
            return None

        connector_types = []
        connector_formal_names = []
        max_power = 0
        for conn in connections:
            ct = conn.get("ConnectionType", {})
            if ct:
                title = ct.get("Title", "")
                if title:
                    connector_types.append(title)
                formal = ct.get("FormalName", "")
                if formal:
                    connector_formal_names.append(formal)
            power = conn.get("PowerKW")
            if power and power > max_power:
                max_power = power

        # Determine live status
        is_live = False
        status = "unknown"
        if status_type and status_type.get("IsOperational") is not None:
            is_live = True
            is_op = status_type.get("IsOperational", True)
            title = status_type.get("Title", "").lower()
            if not is_op:
                status = "out_of_service"
            elif "in use" in title:
                status = "in_use"
            elif is_op:
                status = "available"

        verified_date = poi_data.get("DateLastVerified")
        last_verified = None
        if verified_date:
            try:
                last_verified = datetime.fromisoformat(
                    verified_date.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        operator_name = operator_info.get("Title", "") if operator_info else ""
        ocm_operator_id = operator_info.get("ID") if operator_info else None

        return {
            "ocm_id": poi_data.get("ID"),
            "name": address_info.get("Title", f"Charging Point {poi_data.get('ID')}"),
            "lat": lat,
            "lon": lon,
            "address": address_info.get("AddressLine1", ""),
            "town": address_info.get("Town", ""),
            "county": address_info.get("StateOrProvince", ""),
            "postcode": address_info.get("Postcode", ""),
            "country": address_info.get("Country", {}).get("Title", "United Kingdom"),
            "country_code": address_info.get("Country", {}).get("ISOCode", "GB"),
            "operator_name": operator_name,
            "ocm_operator_id": ocm_operator_id,
            "connection_type": ", ".join(set(connector_types)) if connector_types else "",
            "connector_types": connector_types,
            "connector_formal_names": connector_formal_names,
            "power_kw": max_power if max_power > 0 else None,
            "max_power_kw": max_power if max_power > 0 else None,
            "number_of_points": poi_data.get("NumberOfPoints", 1) or 1,
            "usage_type": usage_type.get("Title", "") if usage_type else "",
            "access_type": poi_data.get("AddressInfo", {}).get("AccessComments", ""),
            "cost_type": "",
            "usage_cost": poi_data.get("UsageCost", "") or "",
            "is_live_status": is_live,
            "status": status,
            "last_verified": last_verified,
            "raw_data": poi_data,
        }


ocm_client = OCMAPIClient()