"""
Local web server for adding games via browser/phone.

Usage:
    python3 -m baseball_processor.server              # Start on port 5555
    python3 -m baseball_processor.server --port 8080   # Custom port

Access from browser: http://localhost:5555
Access from phone (same wifi): http://<your-mac-ip>:5555
"""

import argparse
import json
import subprocess
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .parsers.mlb_api_parser import parse_mlb_game
from .utils.http import create_retry_session, get_with_retry

CACHE_DIR = Path(__file__).parent.parent / 'cache'
PROJECT_DIR = Path(__file__).parent.parent
MLB_API_BASE = 'https://statsapi.mlb.com/api/v1'

_session = create_retry_session()
_processing = False


def fetch_schedule(date_str):
    url = f'{MLB_API_BASE}/schedule?date={date_str}&sportId=1&hydrate=team'
    resp = get_with_retry(_session, url, timeout=30)
    if resp.status_code != 200:
        return []
    data = resp.json()
    games = []
    for date in data.get('dates', []):
        for game in date.get('games', []):
            away = game.get('teams', {}).get('away', {}).get('team', {})
            home = game.get('teams', {}).get('home', {}).get('team', {})
            games.append({
                'gamePk': game['gamePk'],
                'away_name': away.get('name', ''),
                'away_abbr': away.get('abbreviation', ''),
                'home_name': home.get('name', ''),
                'home_abbr': home.get('abbreviation', ''),
                'status': game.get('status', {}).get('detailedState', ''),
                'venue': game.get('venue', {}).get('name', ''),
                'gameType': game.get('gameType', 'R'),
            })
    return games


def is_game_cached(game_pk):
    skip = ('career', 'player_bios')
    for f in CACHE_DIR.glob('*.json'):
        if f.name.startswith(skip):
            continue
        try:
            d = json.load(open(f))
            if d.get('mlb_game_pk') == game_pk:
                return True
        except:
            continue
    return False


def add_game(game_pk):
    """Fetch game from API, save to cache, run processor."""
    global _processing
    _processing = True
    try:
        game_data = parse_mlb_game(game_pk, verbose=True)
        if not game_data:
            return False, "Failed to parse game"

        game_id = game_data.get('game_id', '')
        cache_path = CACHE_DIR / f"{game_id}.json"
        temp = cache_path.with_suffix('.tmp')
        with open(temp, 'w') as f:
            json.dump(game_data, f, indent=2)
        temp.replace(cache_path)

        # Run processor
        subprocess.run(
            ['python3', '-m', 'baseball_processor', '--website-only'],
            cwd=str(PROJECT_DIR), timeout=300
        )
        return True, game_id
    except Exception as e:
        return False, str(e)
    finally:
        _processing = False


PAGE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Add Game</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; color: #1e293b; }
.container { max-width: 600px; margin: 0 auto; padding: 16px; }
h1 { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
.date-nav { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.date-nav button { background: #e2e8f0; border: none; border-radius: 8px; padding: 8px 16px; font-size: 16px; cursor: pointer; }
.date-nav button:active { background: #cbd5e1; }
.date-label { font-size: 16px; font-weight: 600; flex: 1; text-align: center; }
.game { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; margin-bottom: 10px; cursor: pointer; transition: all 0.15s; }
.game:active { transform: scale(0.98); background: #f1f5f9; }
.game.cached { opacity: 0.5; }
.game .teams { font-size: 16px; font-weight: 600; }
.game .venue { font-size: 13px; color: #64748b; margin-top: 2px; }
.game .status { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.game .badge { display: inline-block; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; margin-left: 8px; }
.badge.cached { background: #dbeafe; color: #2563eb; }
.badge.final { background: #dcfce7; color: #16a34a; }
.badge.live { background: #fef3c7; color: #d97706; }
.toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #1e293b; color: white; padding: 12px 24px; border-radius: 12px; font-size: 14px; display: none; z-index: 100; }
.toast.show { display: block; }
.spinner { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.3); z-index: 50; align-items: center; justify-content: center; }
.spinner.show { display: flex; }
.spinner-inner { background: white; border-radius: 16px; padding: 32px; text-align: center; font-size: 16px; font-weight: 600; }
.empty { text-align: center; color: #94a3b8; padding: 40px; }
</style>
</head>
<body>
<div class="container">
    <h1>Add Game</h1>
    <div class="date-nav">
        <button onclick="changeDate(-1)">&larr;</button>
        <div class="date-label" id="dateLabel"></div>
        <button onclick="changeDate(1)">&rarr;</button>
    </div>
    <div id="games"></div>
</div>
<div class="spinner" id="spinner"><div class="spinner-inner">Adding game...</div></div>
<div class="toast" id="toast"></div>
<script>
let currentDate = new Date();
// Start with today
loadGames();

function fmt(d) {
    return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
}
function fmtDisplay(d) {
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
}
function changeDate(delta) {
    currentDate.setDate(currentDate.getDate() + delta);
    loadGames();
}
function loadGames() {
    document.getElementById('dateLabel').textContent = fmtDisplay(currentDate);
    document.getElementById('games').innerHTML = '<div class="empty">Loading...</div>';
    fetch('/api/games?date=' + fmt(currentDate))
        .then(r => r.json())
        .then(data => {
            const el = document.getElementById('games');
            if (!data.games.length) { el.innerHTML = '<div class="empty">No games</div>'; return; }
            el.innerHTML = data.games.map((g, i) => {
                const badges = [];
                if (g.cached) badges.push('<span class="badge cached">Added</span>');
                else if (g.status === 'Final') badges.push('<span class="badge final">Final</span>');
                else if (g.status.includes('Progress')) badges.push('<span class="badge live">Live</span>');
                const cls = g.cached ? 'game cached' : 'game';
                const onclick = g.cached ? '' : `onclick="addGame(${g.gamePk})"`;
                return `<div class="${cls}" ${onclick}>
                    <div class="teams">${g.away_name} @ ${g.home_name}${badges.join('')}</div>
                    <div class="venue">${g.venue}</div>
                    <div class="status">${g.status}${g.gameType !== 'R' ? ' [' + g.gameType + ']' : ''}</div>
                </div>`;
            }).join('');
        });
}
function addGame(pk) {
    document.getElementById('spinner').classList.add('show');
    fetch('/api/add?gamePk=' + pk, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            document.getElementById('spinner').classList.remove('show');
            const toast = document.getElementById('toast');
            toast.textContent = data.ok ? 'Game added and deployed!' : 'Error: ' + data.error;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
            if (data.ok) loadGames();
        })
        .catch(() => {
            document.getElementById('spinner').classList.remove('show');
        });
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/games':
            params = parse_qs(parsed.query)
            date_str = params.get('date', [datetime.now().strftime('%Y-%m-%d')])[0]
            games = fetch_schedule(date_str)
            for g in games:
                g['cached'] = is_game_cached(g['gamePk'])
            self._json({'games': games})
        elif parsed.path == '/' or parsed.path == '':
            self._html(PAGE_HTML)
        else:
            self._respond(404, 'Not found')

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/add':
            if _processing:
                self._json({'ok': False, 'error': 'Already processing a game'})
                return
            params = parse_qs(parsed.query)
            game_pk = int(params.get('gamePk', [0])[0])
            if not game_pk:
                self._json({'ok': False, 'error': 'No gamePk'})
                return
            # Run in thread so we don't block
            def process():
                ok, result = add_game(game_pk)
                return ok, result
            ok, result = process()
            self._json({'ok': ok, 'gameId': result if ok else None, 'error': None if ok else result})
        else:
            self._respond(404, 'Not found')

    def _json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, content):
        body = content.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _respond(self, code, message):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(message.encode())

    def log_message(self, format, *args):
        print(f"  {args[0]}")


def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'


def main():
    parser = argparse.ArgumentParser(description='Local web server for adding games')
    parser.add_argument('--port', type=int, default=5555)
    args = parser.parse_args()

    local_ip = get_local_ip()
    print(f"Starting server on port {args.port}...")
    print(f"  Local:  http://localhost:{args.port}")
    print(f"  Phone:  http://{local_ip}:{args.port}")
    print(f"  Press Ctrl+C to stop\n")

    server = HTTPServer(('0.0.0.0', args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == '__main__':
    main()
