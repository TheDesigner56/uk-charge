/* ──────────────────────────────────────────────
   UK Charge — Journey Planner JavaScript
   Basic journey planner with map-based location picking
   ────────────────────────────────────────────── */

(function() {
    'use strict';

    const mapEl = document.getElementById('journeyMap');
    if (!mapEl || typeof maplibregl === 'undefined') return;

    let pickingMode = null; // 'start' or 'end'
    let startMarker = null;
    let endMarker = null;

    const map = new maplibregl.Map({
        container: mapEl,
        style: document.documentElement.classList.contains('dark')
            ? 'https://basemaps.cartocdn.com/gl/dark-matter-gl/style.json'
            : 'https://basemaps.cartocdn.com/gl/positron-gl/style.json',
        center: [-2.5, 54.5],
        zoom: 5.5,
        attributionControl: true,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    const statusColors = {
        available: '#22c55e',
        in_use: '#f59e0b',
        out_of_service: '#ef4444',
        unknown: '#6b7280',
    };

    // ── Location input: focus map and enable picking ──
    const startInput = document.getElementById('startLocation');
    const endInput = document.getElementById('endLocation');
    const startLat = document.getElementById('startLat');
    const startLon = document.getElementById('startLon');
    const endLat = document.getElementById('endLat');
    const endLon = document.getElementById('endLon');

    if (startInput) {
        startInput.addEventListener('focus', () => { pickingMode = 'start'; });
        startInput.addEventListener('input', async (e) => {
            // Simple geocode via Nominatim
            const results = await geocode(e.target.value);
            if (results) {
                startLat.value = results.lat;
                startLon.value = results.lon;
                placeMarker('start', results.lat, results.lon);
            }
        });
    }

    if (endInput) {
        endInput.addEventListener('focus', () => { pickingMode = 'end'; });
        endInput.addEventListener('input', async (e) => {
            const results = await geocode(e.target.value);
            if (results) {
                endLat.value = results.lat;
                endLon.value = results.lon;
                placeMarker('end', results.lat, results.lon);
            }
        });
    }

    // ── Map click for picking locations ──
    map.on('click', (e) => {
        const { lat, lng } = e.lngLat;
        if (pickingMode === 'start') {
            startLat.value = lat;
            startLon.value = lng;
            placeMarker('start', lat, lng);
            if (startInput) startInput.value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        } else if (pickingMode === 'end') {
            endLat.value = lat;
            endLon.value = lng;
            placeMarker('end', lat, lng);
            if (endInput) endInput.value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        }
    });

    function placeMarker(type, lat, lon) {
        const color = type === 'start' ? '#00D26A' : '#EF4444';
        const marker = new maplibregl.Marker({ color })
            .setLngLat([lon, lat])
            .addTo(map);

        if (type === 'start') {
            if (startMarker) startMarker.remove();
            startMarker = marker;
        } else {
            if (endMarker) endMarker.remove();
            endMarker = marker;
        }

        // Draw line between points
        if (startMarker && endMarker) {
            drawRoute();
        }
    }

    function drawRoute() {
        const startLatVal = parseFloat(startLat.value);
        const startLonVal = parseFloat(startLon.value);
        const endLatVal = parseFloat(endLat.value);
        const endLonVal = parseFloat(endLon.value);

        if (map.getSource('route')) {
            map.removeLayer('route-line');
            map.removeSource('route');
        }

        map.addSource('route', {
            type: 'geojson',
            data: {
                type: 'Feature',
                geometry: {
                    type: 'LineString',
                    coordinates: [[startLonVal, startLatVal], [endLonVal, endLatVal]],
                },
            },
        });

        map.addLayer({
            id: 'route-line',
            type: 'line',
            source: 'route',
            paint: {
                'line-color': '#4DA3FF',
                'line-width': 3,
                'line-dash-array': [2, 1],
            },
        });

        // Fit bounds
        const bounds = new maplibregl.LngLatBounds();
        bounds.extend([startLonVal, startLatVal]);
        bounds.extend([endLonVal, endLatVal]);
        map.fitBounds(bounds, { padding: 80 });
    }

    // ── Geocode via Nominatim (OpenStreetMap) ──
    async function geocode(query) {
        if (!query || query.length < 3) return null;
        try {
            const resp = await fetch(
                `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1&countrycodes=gb`
            );
            const data = await resp.json();
            if (data && data[0]) {
                return { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon) };
            }
        } catch(e) {
            console.error('Geocode error:', e);
        }
        return null;
    }

    // ── Plan journey button ──
    const planBtn = document.getElementById('planJourneyBtn');
    const resultsEl = document.getElementById('journeyResults');
    const resultsList = document.getElementById('journeyResultsList');
    const loadingEl = document.getElementById('journeyLoading');

    if (planBtn) {
        planBtn.addEventListener('click', async () => {
            const sLat = parseFloat(startLat.value);
            const sLon = parseFloat(startLon.value);
            const eLat = parseFloat(endLat.value);
            const eLon = parseFloat(endLon.value);

            if (!sLat || !sLon || !eLat || !eLon) {
                alert('Please set both start and end locations');
                return;
            }

            loadingEl.style.display = 'block';
            resultsEl.style.display = 'none';

            try {
                const resp = await fetch(
                    `/journey/search/?start_lat=${sLat}&start_lon=${sLon}&end_lat=${eLat}&end_lon=${eLon}`
                );
                const data = await resp.json();

                loadingEl.style.display = 'none';
                resultsEl.style.display = 'block';

                if (data.results && data.results.length > 0) {
                    resultsList.innerHTML = data.results.map(r => `
                        <a href="${r.url}" class="card card-clickable">
                            <div class="card-header">
                                <span class="power-badge ${r.power_kw >= 100 ? 'power-ultra' : r.power_kw >= 50 ? 'power-rapid' : 'power-slow'}">${r.power_kw ? r.power_kw + 'kW' : '—'}</span>
                                <span class="status-badge badge-${r.status || 'unknown'}">${r.status || 'Unknown'}</span>
                            </div>
                            <h3 class="card-title">${r.name}</h3>
                            <p class="card-meta">${r.town || '—'}</p>
                            <div class="card-footer">
                                <span class="card-distance">${r.distance_km}km from route</span>
                                <span class="card-connectors">${r.connector_types ? r.connector_types.length : 0} connector(s)</span>
                            </div>
                        </a>
                    `).join('');

                    // Add chargers to map
                    if (map.getSource('journey-chargers')) {
                        map.removeLayer('journey-chargers-circle');
                        map.removeSource('journey-chargers');
                    }

                    const geojson = {
                        type: 'FeatureCollection',
                        features: data.results.map(r => ({
                            type: 'Feature',
                            geometry: { type: 'Point', coordinates: [r.lon, r.lat] },
                            properties: {
                                name: r.name,
                                status: r.status,
                                power: r.power_kw,
                                url: r.url,
                            },
                        })),
                    };

                    map.addSource('journey-chargers', { type: 'geojson', data: geojson });
                    map.addLayer({
                        id: 'journey-chargers-circle',
                        type: 'circle',
                        source: 'journey-chargers',
                        paint: {
                            'circle-radius': 7,
                            'circle-color': ['match',
                                ['get', 'status'],
                                'available', statusColors.available,
                                'in_use', statusColors.in_use,
                                'out_of_service', statusColors.out_of_service,
                                statusColors.unknown
                            ],
                            'circle-stroke-width': 2,
                            'circle-stroke-color': '#FFD700',
                        },
                    });

                    const popup = new maplibregl.Popup({ closeButton: false, offset: 10 });
                    map.on('click', 'journey-chargers-circle', (e) => {
                        const f = e.features[0];
                        popup.setLngLat(f.geometry.coordinates)
                            .setHTML(`<a href="${f.properties.url}"><strong>${f.properties.name}</strong><br>${f.properties.power ? f.properties.power + 'kW' : 'Unknown power'}</a>`)
                            .addTo(map);
                    });
                } else {
                    resultsList.innerHTML = '<p class="empty-state">No charging points found along this route.</p>';
                }
            } catch(e) {
                console.error('Journey error:', e);
                loadingEl.style.display = 'none';
                resultsEl.style.display = 'block';
                resultsList.innerHTML = '<p class="empty-state">Error finding chargers. Please try again.</p>';
            }
        });
    }
})();