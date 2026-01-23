"""HTML template for the baseball statistics website."""
import json
from .react_app import ReactComponents

class HTMLTemplate:
    """HTML template generator for baseball statistics website."""
    
    @staticmethod
    def create_full_page(json_data):
        """Create the complete HTML page with embedded data and React app."""
        
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        react_code = ReactComponents.get_app_code()
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Baseball Statistics Portal</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://unpkg.com/recharts@2.5.0/dist/Recharts.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
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
        /* Team logo marker - override Leaflet defaults */
        .team-logo-marker {{
            background: none !important;
            border: none !important;
        }}
        /* Custom marker cluster styles */
        .marker-cluster {{
            background-color: rgba(34, 197, 94, 0.6) !important;
        }}
        .marker-cluster div {{
            background-color: rgba(34, 197, 94, 0.9) !important;
            color: white !important;
            font-weight: bold !important;
        }}
        .marker-cluster-visited {{
            background-color: rgba(34, 197, 94, 0.6) !important;
        }}
        .marker-cluster-visited div {{
            background-color: rgba(34, 197, 94, 0.9) !important;
        }}
        .marker-cluster-orioles {{
            background-color: rgba(249, 115, 22, 0.6) !important;
        }}
        .marker-cluster-orioles div {{
            background-color: rgba(249, 115, 22, 0.9) !important;
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
    <script>const BASEBALL_DATA = {json_str};</script>
    <script type="text/babel">{react_code}</script>
</body>
</html>"""


