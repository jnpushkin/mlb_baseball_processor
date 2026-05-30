"""HTML template for the baseball statistics website."""
import json
from .react_app import ReactComponents

class HTMLTemplate:
    """HTML template generator for baseball statistics website."""

    @staticmethod
    def create_full_page(json_data):
        """Create the complete HTML page that loads data from a separate JSON file."""

        react_code = ReactComponents.get_app_code()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Interactive baseball statistics portal - game logs, milestones, player stats, stadium maps, and more.">
    <meta name="theme-color" content="#1e40af" media="(prefers-color-scheme: light)">
    <meta name="theme-color" content="#0f172a" media="(prefers-color-scheme: dark)">
    <meta property="og:title" content="Baseball Statistics Portal">
    <meta property="og:description" content="Interactive baseball statistics portal with game logs, milestones, player comparisons, and stadium maps.">
    <meta property="og:type" content="website">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x26be;</text></svg>">
    <title>Baseball Statistics Portal</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --color-accent: #1e40af;
            --color-accent-light: #dbeafe;
            --color-surface: #ffffff;
            --color-surface-alt: #f8fafc;
            --color-border: #e2e8f0;
            --color-text: #0f172a;
            --color-text-secondary: #64748b;
            --color-text-muted: #94a3b8;
            --radius: 8px;
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.07);
        }}

        * {{
            font-family: var(--font-sans);
        }}

        /* Typography scale */
        .page-title {{ font-size: 1.5rem; font-weight: 700; letter-spacing: -0.025em; }}
        .section-title {{ font-size: 1.125rem; font-weight: 600; letter-spacing: -0.015em; }}
        .subsection-title {{ font-size: 0.9375rem; font-weight: 600; }}
        .body-text {{ font-size: 0.8125rem; }}
        .small-text {{ font-size: 0.6875rem; }}

        /* Tabular numbers for stats */
        td, .stat-num {{ font-variant-numeric: tabular-nums; }}

        /* Table and UI consistency */
        table {{ font-size: 0.8125rem; }}
        thead th {{ font-size: 0.6875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-secondary); }}
        button {{ font-size: 0.8125rem; }}
        input, select {{ font-size: 0.8125rem; }}

        /* Smooth transitions everywhere */
        *, *::before, *::after {{ transition-property: color, background-color, border-color, opacity; transition-duration: 150ms; }}

        /* Loading spinner animation */
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        /* Dark mode */
        .dark {{
            --color-surface: #1e293b;
            --color-surface-alt: #0f172a;
            --color-border: #334155;
            --color-text: #f1f5f9;
            --color-text-secondary: #94a3b8;
            --color-text-muted: #64748b;
            --color-accent: #3b82f6;
            --color-accent-light: rgba(59, 130, 246, 0.15);
            color-scheme: dark;
        }}
        .dark body {{
            background-color: var(--color-surface-alt);
            color: var(--color-text);
        }}
        .dark .bg-white {{
            background-color: var(--color-surface) !important;
        }}
        .dark .bg-slate-50, .dark .bg-slate-100 {{
            background-color: var(--color-surface-alt) !important;
        }}
        .dark .bg-slate-200, .dark .bg-slate-300 {{
            background-color: #334155 !important;
        }}
        .dark .text-slate-300 {{
            color: #cbd5e1 !important;
        }}
        .dark .text-slate-400, .dark .text-slate-500, .dark .text-slate-600 {{
            color: var(--color-text-secondary) !important;
        }}
        .dark .text-slate-700, .dark .text-slate-800 {{
            color: #cbd5e1 !important;
        }}
        .dark .text-slate-900 {{
            color: var(--color-text) !important;
        }}
        .dark .border-slate-100, .dark .border-slate-200, .dark .border-slate-300 {{
            border-color: var(--color-border) !important;
        }}
        .dark .border {{
            border-color: var(--color-border);
        }}
        .dark .shadow-lg,
        .dark .shadow-md,
        .dark .shadow-sm {{
            box-shadow: 0 1px 0 rgba(148, 163, 184, 0.08), 0 14px 28px rgba(0, 0, 0, 0.22) !important;
        }}
        .dark table {{ color: var(--color-text); }}
        .dark thead {{ background-color: #1e293b !important; }}
        .dark tbody tr {{ border-color: var(--color-border); }}
        .dark tbody tr:hover {{ background-color: rgba(255,255,255,0.04) !important; }}
        .dark tbody tr.bg-slate-50\\/50 {{
            background-color: rgba(15, 23, 42, 0.36) !important;
        }}
        .dark .divide-slate-100 > * + * {{ border-color: var(--color-border); }}
        .dark .divide-y > * + * {{
            border-color: var(--color-border) !important;
        }}

        /* Native controls and generated table classes need explicit dark rules. */
        .dark input:not([type="checkbox"]):not([type="radio"]):not([class*="bg-"]),
        .dark select:not([class*="bg-"]),
        .dark textarea:not([class*="bg-"]) {{
            background-color: #0f172a !important;
            border-color: #475569 !important;
            color: #e2e8f0 !important;
        }}
        .dark input::placeholder,
        .dark textarea::placeholder {{
            color: #64748b !important;
            opacity: 1;
        }}
        .dark select option {{
            background-color: #0f172a;
            color: #e2e8f0;
        }}
        .dark .bg-slate-50\\/50 {{
            background-color: rgba(15, 23, 42, 0.45) !important;
        }}
        .dark .hover\\:bg-slate-50:hover,
        .dark .hover\\:bg-slate-100:hover,
        .dark .hover\\:bg-blue-50:hover,
        .dark .hover\\:bg-blue-50\\/50:hover {{
            background-color: rgba(148, 163, 184, 0.08) !important;
        }}

        /* Colored tint backgrounds in dark mode */
        .dark .bg-blue-50 {{ background-color: rgba(59, 130, 246, 0.12) !important; }}
        .dark .bg-green-50 {{ background-color: rgba(34, 197, 94, 0.12) !important; }}
        .dark .bg-emerald-50 {{ background-color: rgba(16, 185, 129, 0.12) !important; }}
        .dark .bg-orange-50 {{ background-color: rgba(249, 115, 22, 0.12) !important; }}
        .dark .bg-purple-50 {{ background-color: rgba(168, 85, 247, 0.12) !important; }}
        .dark .bg-red-50 {{ background-color: rgba(239, 68, 68, 0.12) !important; }}
        .dark .bg-amber-50 {{ background-color: rgba(245, 158, 11, 0.12) !important; }}
        .dark .bg-yellow-50 {{ background-color: rgba(234, 179, 8, 0.12) !important; }}
        .dark .bg-teal-50 {{ background-color: rgba(20, 184, 166, 0.12) !important; }}

        /* Badge chips use 100-level palettes; keep them tinted, not glowing. */
        .dark .bg-blue-100, .dark .bg-sky-100 {{ background-color: rgba(59, 130, 246, 0.18) !important; }}
        .dark .bg-green-100 {{ background-color: rgba(34, 197, 94, 0.18) !important; }}
        .dark .bg-emerald-100 {{ background-color: rgba(16, 185, 129, 0.18) !important; }}
        .dark .bg-orange-100 {{ background-color: rgba(249, 115, 22, 0.18) !important; }}
        .dark .bg-purple-100, .dark .bg-violet-100 {{ background-color: rgba(168, 85, 247, 0.18) !important; }}
        .dark .bg-red-100, .dark .bg-rose-100 {{ background-color: rgba(239, 68, 68, 0.18) !important; }}
        .dark .bg-amber-100, .dark .bg-yellow-100 {{ background-color: rgba(245, 158, 11, 0.18) !important; }}
        .dark .bg-teal-100 {{ background-color: rgba(20, 184, 166, 0.18) !important; }}
        .dark .bg-indigo-100 {{ background-color: rgba(99, 102, 241, 0.18) !important; }}
        .dark .bg-pink-100 {{ background-color: rgba(236, 72, 153, 0.18) !important; }}
        .dark .border-blue-300, .dark .border-sky-300 {{ border-color: rgba(96, 165, 250, 0.35) !important; }}
        .dark .border-green-300 {{ border-color: rgba(74, 222, 128, 0.35) !important; }}
        .dark .border-emerald-200, .dark .border-emerald-300 {{ border-color: rgba(52, 211, 153, 0.35) !important; }}
        .dark .border-orange-300 {{ border-color: rgba(251, 146, 60, 0.35) !important; }}
        .dark .border-purple-300, .dark .border-violet-300 {{ border-color: rgba(192, 132, 252, 0.35) !important; }}
        .dark .border-red-300, .dark .border-rose-300 {{ border-color: rgba(248, 113, 113, 0.35) !important; }}
        .dark .border-amber-300, .dark .border-yellow-300 {{ border-color: rgba(251, 191, 36, 0.35) !important; }}
        .dark .border-teal-300 {{ border-color: rgba(45, 212, 191, 0.35) !important; }}
        .dark .border-indigo-300 {{ border-color: rgba(129, 140, 248, 0.35) !important; }}
        .dark .border-pink-300 {{ border-color: rgba(244, 114, 182, 0.35) !important; }}
        .dark .text-blue-600, .dark .text-blue-700, .dark .text-blue-800 {{ color: #60a5fa !important; }}
        .dark .text-green-600, .dark .text-green-700, .dark .text-green-800 {{ color: #86efac !important; }}
        .dark .text-emerald-600, .dark .text-emerald-700, .dark .text-emerald-800 {{ color: #6ee7b7 !important; }}
        .dark .text-orange-600, .dark .text-orange-700, .dark .text-orange-800 {{ color: #fdba74 !important; }}
        .dark .text-purple-600, .dark .text-purple-700, .dark .text-purple-800, .dark .text-violet-600, .dark .text-violet-700, .dark .text-violet-800 {{ color: #c4b5fd !important; }}
        .dark .text-red-600, .dark .text-red-700, .dark .text-red-800, .dark .text-rose-600, .dark .text-rose-700, .dark .text-rose-800 {{ color: #fca5a5 !important; }}
        .dark .text-amber-600, .dark .text-amber-700, .dark .text-amber-800, .dark .text-yellow-600, .dark .text-yellow-700, .dark .text-yellow-800 {{ color: #fcd34d !important; }}
        .dark .text-teal-600, .dark .text-teal-700, .dark .text-teal-800 {{ color: #5eead4 !important; }}
        .dark .text-sky-600, .dark .text-sky-700, .dark .text-sky-800 {{ color: #7dd3fc !important; }}
        .dark .text-indigo-600, .dark .text-indigo-700, .dark .text-indigo-800 {{ color: #a5b4fc !important; }}
        .dark .text-pink-600, .dark .text-pink-700, .dark .text-pink-800 {{ color: #f9a8d4 !important; }}

        .dark [class*="from-blue-50"],
        .dark [class*="to-indigo-50"],
        .dark [class*="from-slate-50"],
        .dark [class*="to-white"] {{
            background-image: linear-gradient(to right, rgba(30, 41, 59, 0.96), rgba(15, 23, 42, 0.92)) !important;
        }}
        .dark [class*="from-amber-50"] {{
            background-image: linear-gradient(to bottom, rgba(69, 48, 12, 0.34), rgba(30, 41, 59, 0.96)) !important;
        }}
        .dark .backdrop-blur {{
            border-color: rgba(148, 163, 184, 0.18);
        }}

        /* Scrollbar styling */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
        .dark ::-webkit-scrollbar-thumb {{ background: #475569; }}

        /* Mobile responsive */
        @media (max-width: 640px) {{
            .page-title {{ font-size: 1.125rem; }}
            .section-title {{ font-size: 1rem; }}
            table {{ font-size: 0.6875rem; }}
            thead th {{ font-size: 0.625rem; }}
        }}

        /* Ensure tables scroll horizontally on small screens */
        .overflow-x-auto {{ -webkit-overflow-scrolling: touch; }}

        /* Map styles */
        .leaflet-container {{
            font-family: inherit;
        }}
        .dark .leaflet-container {{
            filter: invert(1) hue-rotate(180deg);
        }}
        .dark .leaflet-container .leaflet-marker-icon,
        .dark .leaflet-container .leaflet-popup-content-wrapper,
        .dark .leaflet-container .leaflet-popup-tip {{
            filter: invert(1) hue-rotate(180deg);
        }}
        .stadium-popup .leaflet-popup-content-wrapper {{
            border-radius: 8px;
        }}
        .stadium-popup .leaflet-popup-content {{
            margin: 8px 12px;
        }}
        .stadium-logo-marker-shell {{
            background: transparent;
            border: 0;
        }}
        .stadium-logo-marker {{
            width: var(--marker-size);
            height: var(--marker-size);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: var(--marker-bg);
            border: 2px solid var(--marker-ring);
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.24), 0 0 0 2px rgba(255, 255, 255, 0.94);
            overflow: hidden;
            transform-origin: center;
            transition: transform 120ms ease, opacity 120ms ease;
        }}
        .stadium-logo-marker.is-unvisited {{
            opacity: 0.58;
            filter: grayscale(0.25) saturate(0.82);
        }}
        .stadium-logo-marker:hover {{
            opacity: 1;
            transform: scale(1.18);
            z-index: 1000;
        }}
        .stadium-logo-marker-img,
        .stadium-flag-marker-img {{
            width: calc(var(--marker-size) - 6px);
            height: calc(var(--marker-size) - 6px);
            display: block;
            object-fit: contain;
            padding: 2px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.9);
        }}
        .stadium-logo-marker-code,
        .stadium-logo-cluster-code,
        .stadium-logo-split-code {{
            font-size: max(7px, calc(var(--marker-size) * 0.28));
            line-height: 1;
            font-weight: 800;
            color: #334155;
        }}
        .stadium-logo-split,
        .stadium-logo-cluster {{
            width: 100%;
            height: 100%;
            display: grid;
            gap: 1px;
            padding: 3px;
            align-items: center;
            justify-items: center;
        }}
        .stadium-logo-split {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
            grid-template-rows: minmax(0, 1fr);
        }}
        .stadium-logo-cluster {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
            grid-template-rows: repeat(2, minmax(0, 1fr));
        }}
        .stadium-logo-split-half {{
            width: 100%;
            height: 100%;
            min-width: 0;
            min-height: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .stadium-logo-split-img,
        .stadium-logo-cluster-img {{
            width: 100%;
            height: 100%;
            min-width: 0;
            min-height: 0;
            display: block;
            object-fit: contain;
        }}
        .stadium-popup-logo {{
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            --marker-size: 30px;
        }}
        .stadium-popup-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }}
        .stadium-popup-title {{
            margin: 0;
            font-size: 14px;
            font-weight: 700;
            color: #0f172a;
        }}
        .stadium-popup-meta {{
            font-size: 11px;
            color: #64748b;
        }}
        .journey-path {{
            stroke-dasharray: 10, 5;
            animation: dash 1s linear infinite;
        }}
        @keyframes dash {{
            to {{
                stroke-dashoffset: -15;
            }}
        }}
    </style>
</head>
<body>
    <div id="root">
        <div id="initial-loader" style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f8fafc;">
            <div style="width:40px;height:40px;border:3px solid #e2e8f0;border-top-color:#1e40af;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:16px;"></div>
            <div style="font-size:15px;font-weight:500;color:#334155;">Loading baseball data...</div>
            <div id="loader-status" style="font-size:12px;color:#94a3b8;margin-top:6px;"></div>
        </div>
    </div>
    <script>
        // Load data from separate JSON file
        var BASEBALL_DATA = null;
        var DATA_LOADED = false;
        var DATA_LOAD_ERROR = null;

        function initApp() {{
            if (DATA_LOADED) return;
            DATA_LOADED = true;
            if (window.__onDataReady) window.__onDataReady(BASEBALL_DATA);
        }}

        function showLoadError(msg) {{
            DATA_LOAD_ERROR = msg;
            if (window.__onDataError) window.__onDataError(msg);
        }}

        function loadAwardData(data) {{
            return fetch('award-data.json?v=' + Date.now(), {{ cache: 'no-store' }})
                .then(function(response) {{
                    if (!response.ok) return null;
                    return response.json();
                }})
                .then(function(awardData) {{
                    if (!awardData) return data;
                    return loadDataSidecars(awardData).then(function(fullAwardData) {{
                        data.awardChecklists = fullAwardData;
                        return data;
                    }});
                }})
                .catch(function() {{
                    return data;
                }});
        }}

        function loadDataSidecars(data) {{
            const sidecars = data.__dataSidecars || [];
            delete data.__dataSidecars;
            if (!sidecars.length) return Promise.resolve(data);

            return Promise.all(sidecars.map(function(sidecar) {{
                return fetch(sidecar.path + '?v=' + Date.now(), {{ cache: 'no-store' }})
                    .then(function(response) {{
                        if (!response.ok) throw new Error(sidecar.path + ' HTTP ' + response.status);
                        return response.json();
                    }});
            }})).then(function(payloads) {{
                payloads.forEach(function(payload) {{
                    if (payload.mode === 'append') {{
                        if (!Array.isArray(data[payload.key])) data[payload.key] = [];
                        data[payload.key] = data[payload.key].concat(payload.items || []);
                    }} else {{
                        data[payload.key] = payload.value;
                    }}
                }});
                return data;
            }});
        }}

        fetch('data.json?v=' + Date.now(), {{ cache: 'no-store' }})
            .then(function(response) {{
                if (!response.ok) throw new Error('HTTP ' + response.status);
                return response.json();
            }})
            .then(loadDataSidecars)
            .then(loadAwardData)
            .then(function(data) {{
                BASEBALL_DATA = data;
                initApp();
            }})
            .catch(function(err) {{
                if (window.location.protocol === 'file:') {{
                    showLoadError('file_protocol');
                }} else {{
                    showLoadError('Could not load data: ' + err.message);
                }}
            }});
    </script>
    <script type="text/babel">{react_code}</script>
</body>
</html>"""

    @staticmethod
    def create_data_json(json_data):
        """Create the JSON data file content."""
        return json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
