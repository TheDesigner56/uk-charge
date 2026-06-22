/* ──────────────────────────────────────────────
   UK Charge — Map Page JavaScript
   Full-screen interactive map with filters
   ────────────────────────────────────────────── */

(function() {
    'use strict';

    const mapEl = document.getElementById('mapFull');
    if (!mapEl || typeof maplibregl === 'undefined') return;

    // ── Initialize map ──
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
    map.addControl(new maplibregl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: false,
    }), 'top-right');

    const statusColors = {
        available: '#22c55e',
        in_use: '#f59e0b',
        out_of_service: '#ef4444',
        unknown: '#6b7280',
    };

    let loaded = false;
    const popup = new maplibregl.Popup({ closeButton: false, offset: 10 });

    // ── Fetch and display charging points ──
    async function loadPoints() {
        const bounds = map.getBounds();
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        const boundsStr = `${sw.lat},${sw.lng},${ne.lat},${ne.lng}`;

        const status = document.getElementById('filterStatus')?.value || 'all';
        const power = document.getElementById('filterPower')?.value || 'all';
        const connector = document.getElementById('filterConnector')?.value || 'all';
        const operator = document.getElementById('filterOperator')?.value || '';

        const params = new URLSearchParams({ bounds: boundsStr });
        if (status !== 'all') params.set('status', status);
        if (power !== 'all') params.set('power', power);
        if (connector !== 'all') params.set('connector', connector);
        if (operator) params.set('operator', operator);

        try {
            const resp = await fetch(`/htmx/map-points/?${params.toString()}`);
            const data = await resp.json();

            // Update stats
            const statsEl = document.getElementById('mapStats');
            if (statsEl) {
                statsEl.innerHTML = `<strong>${data.features.length}</strong> charging points visible`;
            }

            // Update source
            if (map.getSource('chargers')) {
                map.getSource('chargers').setData(data);
            } else {
                map.addSource('chargers', { type: 'geojson', data });

                // Add circle layer
                map.addLayer({
                    id: 'chargers-circle',
                    type: 'circle',
                    source: 'chargers',
                    paint: {
                        'circle-radius': [
                            'interpolate', ['linear'], ['zoom'],
                            5, 4,
                            10, 6,
                            15, 10,
                        ],
                        'circle-color': ['match',
                            ['get', 'status'],
                            'available', statusColors.available,
                            'in_use', statusColors.in_use,
                            'out_of_service', statusColors.out_of_service,
                            statusColors.unknown
                        ],
                        'circle-stroke-width': 1,
                        'circle-stroke-color': '#0A0A0A',
                        'circle-opacity': 0.85,
                    },
                });

                // Cluster-like large circles for high zoom
                map.addLayer({
                    id: 'chargers-label',
                    type: 'symbol',
                    source: 'chargers',
                    minzoom: 12,
                    layout: {
                        'text-field': ['get', 'name'],
                        'text-size': 11,
                        'text-offset': [0, 1.5],
                        'text-anchor': 'top',
                    },
                    paint: {
                        'text-color': '#A0A0A0',
                        'text-halo-color': '#0A0A0A',
                        'text-halo-width': 2,
                    },
                });

                // Interaction
                map.on('click', 'chargers-circle', (e) => {
                    const f = e.features[0];
                    const props = f.properties;
                    popup.setLngLat(f.geometry.coordinates)
                        .setHTML(`
                            <a href="${props.url}"><strong>${props.name}</strong></a><br>
                            ${props.town ? props.town + '<br>' : ''}
                            ${props.operator || 'Unknown operator'}<br>
                            ${props.power ? props.power + 'kW' : 'Unknown power'} • ${props.connectors ? props.connectors.length : 0} connector(s)
                        `)
                        .addTo(map);
                });

                map.on('mouseenter', 'chargers-circle', () => {
                    map.getCanvas().style.cursor = 'pointer';
                });
                map.on('mouseleave', 'chargers-circle', () => {
                    map.getCanvas().style.cursor = '';
                });
            }
        } catch(e) {
            console.error('Error loading points:', e);
        }
    }

    // ── Load on map ready ──
    map.on('load', () => {
        loaded = true;
        loadPoints();
    });

    // ── Reload on moveend (debounced) ──
    let moveTimer;
    map.on('moveend', () => {
        if (!loaded) return;
        clearTimeout(moveTimer);
        moveTimer = setTimeout(loadPoints, 300);
    });

    // ── Filter change handlers ──
    ['filterStatus', 'filterPower', 'filterConnector'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', loadPoints);
    });

    const operatorInput = document.getElementById('filterOperator');
    if (operatorInput) {
        let opTimer;
        operatorInput.addEventListener('input', () => {
            clearTimeout(opTimer);
            opTimer = setTimeout(loadPoints, 500);
        });
    }

    // ── Reset filters ──
    const resetBtn = document.getElementById('filterReset');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            ['filterStatus', 'filterPower', 'filterConnector'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = 'all';
            });
            const opInput = document.getElementById('filterOperator');
            if (opInput) opInput.value = '';
            loadPoints();
        });
    }
})();