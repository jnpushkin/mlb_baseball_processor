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
    <meta property="og:title" content="Baseball Statistics Portal">
    <meta property="og:description" content="Interactive baseball statistics portal with game logs, milestones, player comparisons, and stadium maps.">
    <meta property="og:type" content="website">
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
        .dark table {{ color: var(--color-text); }}
        .dark thead {{ background-color: #1e293b !important; }}
        .dark tbody tr {{ border-color: var(--color-border); }}
        .dark tbody tr:hover {{ background-color: rgba(255,255,255,0.04) !important; }}
        .dark .divide-slate-100 > * + * {{ border-color: var(--color-border); }}

        /* Colored tint backgrounds in dark mode */
        .dark .bg-blue-50 {{ background-color: rgba(59, 130, 246, 0.12) !important; }}
        .dark .bg-green-50 {{ background-color: rgba(34, 197, 94, 0.12) !important; }}
        .dark .bg-orange-50 {{ background-color: rgba(249, 115, 22, 0.12) !important; }}
        .dark .bg-purple-50 {{ background-color: rgba(168, 85, 247, 0.12) !important; }}
        .dark .bg-red-50 {{ background-color: rgba(239, 68, 68, 0.12) !important; }}
        .dark .bg-amber-50 {{ background-color: rgba(245, 158, 11, 0.12) !important; }}
        .dark .bg-yellow-50 {{ background-color: rgba(234, 179, 8, 0.12) !important; }}
        .dark .bg-teal-50 {{ background-color: rgba(20, 184, 166, 0.12) !important; }}

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
        .stadium-popup .leaflet-popup-content-wrapper {{
            border-radius: 8px;
        }}
        .stadium-popup .leaflet-popup-content {{
            margin: 8px 12px;
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
    <div id="root"></div>
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

        fetch('data.json')
            .then(function(response) {{
                if (!response.ok) throw new Error('HTTP ' + response.status);
                return response.json();
            }})
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
