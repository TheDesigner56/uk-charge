/* ──────────────────────────────────────────────
   UK Charge — Main JavaScript
   Theme toggle, nav toggle, search enhancement
   ────────────────────────────────────────────── */

(function() {
    'use strict';

    // ── Theme Toggle ──
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const html = document.documentElement;
            const current = html.classList.contains('dark') ? 'dark' : 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            html.classList.remove(current);
            html.classList.add(next);
            document.cookie = `darkmode=${next === 'dark' ? 'on' : 'off'};max-age=31536000;path=/`;
        });
    }

    // ── Nav Toggle (mobile) ──
    const navToggle = document.getElementById('navToggle');
    const siteNav = document.getElementById('siteNav');
    if (navToggle && siteNav) {
        navToggle.addEventListener('click', () => {
            siteNav.classList.toggle('open');
        });
        // Close on link click
        siteNav.querySelectorAll('a').forEach(a => {
            a.addEventListener('click', () => siteNav.classList.remove('open'));
        });
    }

    // ── Search Input Enhancement ──
    const heroSearch = document.getElementById('heroSearch');
    if (heroSearch) {
        let debounceTimer;
        heroSearch.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            if (query.length < 2) return;
            debounceTimer = setTimeout(() => {
                // Could add live search results here via HTMX
            }, 300);
        });
    }

    // ── Map Sidebar Toggle (mobile) ──
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mapSidebar = document.getElementById('mapSidebar');
    const sidebarClose = document.getElementById('sidebarClose');
    if (sidebarToggle && mapSidebar) {
        sidebarToggle.addEventListener('click', () => {
            mapSidebar.classList.add('open');
        });
    }
    if (sidebarClose && mapSidebar) {
        sidebarClose.addEventListener('click', () => {
            mapSidebar.classList.remove('open');
        });
    }

    // ── HTMX global events ──
    document.addEventListener('htmx:afterRequest', (e) => {
        console.debug('HTMX request complete:', e.detail.pathInfo);
    });
})();