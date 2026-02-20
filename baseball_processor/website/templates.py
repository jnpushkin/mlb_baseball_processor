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
    <style>
        * {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}

        /* Consistent font sizes */
        .page-title {{ font-size: 2rem; }}
        .section-title {{ font-size: 1.25rem; }}
        .subsection-title {{ font-size: 1rem; }}
        .body-text {{ font-size: 0.875rem; }}
        .small-text {{ font-size: 0.75rem; }}

        /* Table and UI consistency */
        table {{ font-size: 0.875rem; }}
        thead th {{ font-size: 0.75rem; }}
        button {{ font-size: 0.875rem; }}
        input, select {{ font-size: 0.875rem; }}

        /* Loading spinner animation */
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        /* Dark mode styles */
        .dark body {{
            background-color: #111827;
            color: #e5e7eb;
        }}
        .dark .bg-white {{
            background-color: #1f2937 !important;
        }}
        .dark .bg-gray-50 {{
            background-color: #111827 !important;
        }}
        .dark .bg-gray-100 {{
            background-color: #1f2937 !important;
        }}
        .dark .text-gray-600 {{
            color: #9ca3af !important;
        }}
        .dark .text-gray-700 {{
            color: #d1d5db !important;
        }}
        .dark .text-gray-900 {{
            color: #f3f4f6 !important;
        }}
        .dark .border-gray-200 {{
            border-color: #374151 !important;
        }}
        .dark .border-gray-300 {{
            border-color: #4b5563 !important;
        }}
        .dark table {{
            color: #e5e7eb;
        }}
        .dark thead {{
            background-color: #374151 !important;
        }}
        .dark tbody tr {{
            border-color: #374151;
        }}
        .dark tbody tr:hover {{
            background-color: #374151 !important;
        }}
        /* Colored tint backgrounds in dark mode */
        .dark .bg-blue-50 {{ background-color: rgba(59, 130, 246, 0.15) !important; }}
        .dark .bg-green-50 {{ background-color: rgba(34, 197, 94, 0.15) !important; }}
        .dark .bg-orange-50 {{ background-color: rgba(249, 115, 22, 0.15) !important; }}
        .dark .bg-purple-50 {{ background-color: rgba(168, 85, 247, 0.15) !important; }}
        .dark .bg-red-50 {{ background-color: rgba(239, 68, 68, 0.15) !important; }}
        .dark .bg-amber-50 {{ background-color: rgba(245, 158, 11, 0.15) !important; }}
        .dark .bg-yellow-50 {{ background-color: rgba(234, 179, 8, 0.15) !important; }}

        /* Mobile responsive */
        @media (max-width: 640px) {{
            .page-title {{ font-size: 1.25rem; }}
            .section-title {{ font-size: 1.1rem; }}
            table {{ font-size: 0.75rem; }}
            thead th {{ font-size: 0.65rem; }}
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
