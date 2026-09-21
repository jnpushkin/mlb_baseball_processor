"""
Local web server for adding games via browser/phone.

Usage:
    python3 -m baseball_processor.server              # Start on port 5555
    python3 -m baseball_processor.server --port 8080   # Custom port
    python3 -m baseball_processor.server --lan         # Allow phone access on same wifi

Access from browser: http://localhost:5555
Access from phone (same wifi): use --lan and open the printed phone URL
"""

import argparse
import json
import secrets
import subprocess
from datetime import datetime, timedelta
from http.cookies import SimpleCookie, CookieError
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

from .parsers.mlb_api_parser import parse_mlb_game
from .utils.http import create_retry_session, get_with_retry
from .jobs import JobStore
from .main import deploy_to_surge, load_surge_domain
from .companion_manager import CompanionConflict, read_records, save_edit, validate_edit

CACHE_DIR = Path(__file__).parent.parent / 'cache'
PROJECT_DIR = Path(__file__).parent.parent
MLB_API_BASE = 'https://statsapi.mlb.com/api/v1'

_session = create_retry_session()
_processing = False
_server_token = ""
_job_store = None
_job_store_lock = __import__('threading').Lock()

def get_job_store():
    global _job_store
    with _job_store_lock:
        if _job_store is None:
            _job_store = JobStore(CACHE_DIR / 'add_game_jobs.json', add_game, update_companions)
        return _job_store



def build_url(host, port, token):
    token_query = f"?token={quote(token)}" if token else ""
    return f"http://{host}:{port}/{token_query}"


def bind_host_for_mode(lan_enabled):
    return '0.0.0.0' if lan_enabled else '127.0.0.1'


def get_request_token(parsed, headers):
    params = parse_qs(parsed.query)
    explicit = (
        params.get('token', [''])[0]
        or headers.get('X-Add-Game-Token', '')
        or headers.get('Authorization', '').removeprefix('Bearer ').strip()
    )
    if explicit:
        return explicit
    # Cookies let a connected browser open another manager tab. Never use them
    # to authorize requests originating from another site or localhost port.
    origin = headers.get('Origin', '')
    if ((origin and origin != f"http://{headers.get('Host', '')}")
            or headers.get('Sec-Fetch-Site') == 'cross-site'):
        return ''
    try:
        cookies = SimpleCookie(headers.get('Cookie', ''))
        session = cookies.get('passport_manager')
        return session.value if session else ''
    except CookieError:
        return ''


def is_authorized(parsed, headers, expected_token):
    if not expected_token:
        return True
    return secrets.compare_digest(get_request_token(parsed, headers), expected_token)


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
                # 'N' = not a doubleheader, 'S' = split-admission DH, 'Y' = single-admission DH
                'doubleHeader': game.get('doubleHeader', 'N'),
                'gameNumber': game.get('gameNumber', 1),
                'gameDate': game.get('gameDate', ''),  # ISO timestamp; first pitch
            })
    return games


def find_cached_game(game_pk):
    skip = ('career', 'player_bios')
    for f in CACHE_DIR.glob('*.json'):
        if f.name.startswith(skip):
            continue
        try:
            with f.open() as source:
                d = json.load(source)
            if d.get('mlb_game_pk') == game_pk:
                return d
        except (OSError, ValueError, AttributeError):
            continue
    return None


def is_game_cached(game_pk):
    return find_cached_game(game_pk) is not None


def add_game(game_pk, on_progress=None):
    """Save, build, then deploy; preserve completed stages for safe retries."""
    global _processing
    _processing = True
    result = {'ok': False, 'gameId': None, 'saved': False, 'processed': False,
              'deployed': False, 'stage': 'save', 'error': None}
    try:
        # Retry from the saved game instead of overwriting it or fetching again.
        game_data = find_cached_game(game_pk)
        if game_data is None:
            game_data = parse_mlb_game(game_pk, verbose=True)
            if not game_data or not game_data.get('game_id'):
                raise ValueError('Failed to parse game')
            cache_path = CACHE_DIR / f"{game_data['game_id']}.json"
            temp = cache_path.with_suffix('.tmp')
            with temp.open('w') as target:
                json.dump(game_data, target, indent=2)
            temp.replace(cache_path)
        result.update(gameId=game_data['game_id'], saved=True, stage='build')
        if on_progress: on_progress({**result, 'message': 'Game saved. Building website…'})

        # Build and deploy separately so an upload failure cannot masquerade as
        # a successful add, and a failed build never uploads stale artifacts.
        subprocess.run(
            ['python3', '-m', 'baseball_processor', '--website-only', '--no-deploy',
             '--output-excel', str(PROJECT_DIR / 'MLB Game Passport - BREF.xlsx')],
            cwd=str(PROJECT_DIR), timeout=300, check=True
        )
        result.update(processed=True, stage='deploy')
        if on_progress: on_progress({**result, 'message': 'Website built. Deploying…'})
        domain = load_surge_domain()
        if not domain:
            raise RuntimeError('No Surge domain configured')
        if not deploy_to_surge(str(PROJECT_DIR / 'MLB Game Passport - BREF.html'), domain):
            raise RuntimeError('Surge deployment failed; check the server log')
        result.update(ok=True, deployed=True, stage='complete',
                      message='Game saved, website built and deployed.')
    except Exception as e:
        prefixes = {'save': 'Game could not be saved.',
                    'build': 'Game saved. Website build failed.',
                    'deploy': 'Game saved and website built. Deployment failed.'}
        if isinstance(e, subprocess.CalledProcessError):
            detail = 'Check the server log, then retry.'
        elif isinstance(e, subprocess.TimeoutExpired):
            detail = 'Processing exceeded five minutes. Check the server log, then retry.'
        else:
            detail = str(e)
        result.update(error=str(e), message=f"{prefixes[result['stage']]} {detail}")
    finally:
        _processing = False
    return result


def update_companions(payload, on_progress=None):
    result = {'ok': False, 'saved': False, 'processed': False, 'deployed': False, 'stage': 'save'}
    try:
        result['gameId'] = save_edit(PROJECT_DIR, payload)
        result.update(saved=True, stage='build', message='Companions saved. Updating website…')
        if on_progress:
            on_progress(dict(result))
        subprocess.run(['python3', str(PROJECT_DIR / 'scripts/rebuild_website.py'), '--refresh-companions'],
                       cwd=str(PROJECT_DIR), timeout=300, check=True)
        result.update(processed=True, stage='deploy', message='Website updated. Publishing…')
        if on_progress:
            on_progress(dict(result))
        domain = load_surge_domain()
        if not domain or not deploy_to_surge(str(PROJECT_DIR / 'MLB Game Passport - BREF.html'), domain):
            raise RuntimeError('Publishing failed. The saved companions are safe; retry to publish.')
        result.update(ok=True, deployed=True, stage='complete', message='Companions saved and published. Ballpark goals are updated.')
    except Exception as error:
        prefix = 'Companions saved; website update failed.' if result['saved'] else 'Companions were not saved.'
        result.update(error=str(error), message=f'{prefix} {error}')
    return result


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
.game.cached { background: #f1f5f9; }
.game-action { width: 100%; text-align: left; font: inherit; color: inherit; }
.retry-label { margin-top: 8px; font-size: 12px; color: #2563eb; }
.game .teams { font-size: 16px; font-weight: 600; }
.game .venue { font-size: 13px; color: #64748b; margin-top: 2px; }
.game .status { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.game .badge { display: inline-block; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; margin-left: 8px; }
.badge.cached { background: #dbeafe; color: #2563eb; }
.badge.final { background: #dcfce7; color: #16a34a; }
.badge.live { background: #fef3c7; color: #d97706; }
.badge.dh { background: #ffedd5; color: #c2410c; }
.toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: min(560px, calc(100% - 32px)); background: #1e293b; color: white; padding: 16px; border-radius: 12px; font-size: 14px; display: none; z-index: 100; }
.toast button { margin: 12px 8px 0 0; padding: 10px 14px; border: 0; border-radius: 6px; cursor: pointer; }
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
    <p style="margin-bottom:16px"><a id="companionLink" href="/companions">Edit companions for attended games</a></p>
    <div class="date-nav">
        <button aria-label="Previous day" onclick="changeDate(-1)">&larr;</button>
        <div class="date-label" id="dateLabel"></div>
        <button aria-label="Next day" onclick="changeDate(1)">&rarr;</button>
    </div>
    <div id="games"></div>
</div>
<div class="spinner" id="spinner" role="status"><div class="spinner-inner">Saving game, building website and deploying...<br><small>This may take a few minutes.</small></div></div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>
let currentDate = new Date();
let adding = false;
const ADD_GAME_TOKEN = new URLSearchParams(window.location.search).get('token') || '';
document.getElementById('companionLink').href = '/companions?token=' + encodeURIComponent(ADD_GAME_TOKEN);
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
            // Group same-teams pairs to figure out DH total (most pairs are 2)
            const dhTotalByPair = {};
            data.games.forEach(g => {
                if (g.doubleHeader && g.doubleHeader !== 'N') {
                    const k = g.away_abbr + '@' + g.home_abbr;
                    dhTotalByPair[k] = (dhTotalByPair[k] || 0) + 1;
                }
            });
            const fmtTime = (iso) => {
                if (!iso) return '';
                try {
                    const d = new Date(iso);
                    return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
                } catch { return ''; }
            };
            el.innerHTML = data.games.map((g, i) => {
                const badges = [];
                if (g.doubleHeader && g.doubleHeader !== 'N') {
                    const k = g.away_abbr + '@' + g.home_abbr;
                    const total = dhTotalByPair[k] || 2;
                    const dhKind = g.doubleHeader === 'S' ? ' (split)' : '';
                    badges.push(`<span class="badge dh">Game ${g.gameNumber} of ${total}${dhKind}</span>`);
                }
                if (g.cached) badges.push('<span class="badge cached">Saved locally</span>');
                else if (g.status === 'Final') badges.push('<span class="badge final">Final</span>');
                else if (g.status.includes('Progress')) badges.push('<span class="badge live">Live</span>');
                const cls = g.cached ? 'game game-action cached' : 'game game-action';
                const startTime = fmtTime(g.gameDate);
                const statusLine = g.status + (g.gameType !== 'R' ? ' [' + g.gameType + ']' : '') + (startTime ? ' • ' + startTime : '');
                return `<button type="button" class="${cls}" onclick="addGame(${g.gamePk})">
                    <div class="teams">${g.away_name} @ ${g.home_name}${badges.join('')}</div>
                    <div class="venue">${g.venue}</div>
                    <div class="status">${statusLine}</div>
                    ${g.cached ? '<div class="retry-label">Rebuild and retry deployment</div>' : ''}
                </button>`;
            }).join('');
        }).catch(() => {
            document.getElementById('games').textContent = 'Could not load games. Try another date or reload the page.';
        });
}
function showResult(message, retryPk) {
    const toast = document.getElementById('toast');
    toast.replaceChildren();
    const text = document.createElement('div');
    text.textContent = message;
    toast.append(text);
    if (retryPk) {
        const retry = document.createElement('button');
        retry.textContent = 'Retry';
        retry.onclick = () => addGame(retryPk);
        toast.append(retry);
    }
    const dismiss = document.createElement('button');
    dismiss.textContent = 'Dismiss';
    dismiss.onclick = () => toast.classList.remove('show');
    toast.append(dismiss);
    toast.classList.add('show');
}
function followJob(id) {
    localStorage.setItem('passport-add-job', id);
    fetch('/api/jobs/' + encodeURIComponent(id), {headers:{'X-Add-Game-Token':ADD_GAME_TOKEN}})
        .then(r => { if(!r.ok) throw new Error('Could not read job status'); return r.json(); })
        .then(job => {
            document.querySelector('.spinner-inner').textContent = job.message || job.stage;
            if(job.state === 'queued' || job.state === 'running') {
                adding=true; document.getElementById('spinner').classList.add('show');
                setTimeout(() => followJob(id), 1500);
            } else {
                adding=false; document.getElementById('spinner').classList.remove('show');
                localStorage.removeItem('passport-add-job');
                showResult(job.message, job.state==='failed' ? job.gamePk : null);
                if(job.saved) loadGames();
            }
        }).catch(() => {
            adding=false; document.getElementById('spinner').classList.remove('show');
            showResult('Connection lost. Your job is saved; reconnect or reload this page to check its progress.');
        });
}
function addGame(pk) {
    if (adding) return;
    adding = true;
    document.getElementById('toast').classList.remove('show');
    document.getElementById('spinner').classList.add('show');
    fetch('/api/add?gamePk=' + pk, {method:'POST',headers:{'X-Add-Game-Token':ADD_GAME_TOKEN}})
        .then(r => r.json().then(data => {if(!r.ok) throw new Error(data.error || 'Could not queue game'); return data;}))
        .then(job => followJob(job.id))
        .catch(error => {adding=false;document.getElementById('spinner').classList.remove('show');showResult(error.message,pk);});
}
const previousJob=localStorage.getItem('passport-add-job');
if(previousJob)followJob(previousJob);
window.addEventListener('online',()=>{const id=localStorage.getItem('passport-add-job');if(id)followJob(id);});
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/companions':
            self._html((Path(__file__).parent / 'companion_manager.html').read_text())
        elif parsed.path == '/api/companions':
            if not is_authorized(parsed, self.headers, _server_token):
                self._json({'error': 'Open the manager link printed at startup, or enter its token.'}, status=403)
                return
            try:
                self._json(read_records(PROJECT_DIR))
            except (OSError, ValueError, KeyError):
                self._json({'error': 'Build the website once before editing companions.'}, status=503)
        elif parsed.path.startswith('/api/jobs/'):
            if not is_authorized(parsed, self.headers, _server_token):
                self._json({'error': 'Invalid or missing token'}, status=403)
                return
            job = get_job_store().get(parsed.path.rsplit('/', 1)[-1])
            self._json(job or {'error':'Job not found'}, status=200 if job else 404)
        elif parsed.path == '/api/games':
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
        if parsed.path == '/api/companions':
            if not is_authorized(parsed, self.headers, _server_token):
                self._json({'error': 'Invalid or missing token'}, status=403)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16384:
                    raise ValueError('Invalid edit size')
                payload = validate_edit(PROJECT_DIR, json.loads(self.rfile.read(length)))
                self._json(get_job_store().submit_companions(payload), status=202)
            except CompanionConflict as error:
                self._json({'error': str(error)}, status=409)
            except (ValueError, TypeError, KeyError) as error:
                self._json({'error': str(error)}, status=400)
        elif parsed.path == '/api/add':
            if not is_authorized(parsed, self.headers, _server_token):
                self._json({'ok': False, 'error': 'Invalid or missing token'}, status=403)
                return
            params = parse_qs(parsed.query)
            try:
                game_pk = int(params.get('gamePk', [0])[0])
            except (TypeError, ValueError):
                game_pk = 0
            if not game_pk:
                self._json({'ok': False, 'error': 'No gamePk'})
                return
            self._json(get_job_store().submit(game_pk), status=202)
        else:
            self._respond(404, 'Not found')

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        if status < 400:
            self._manager_session()
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, content):
        body = content.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self._manager_session()
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _manager_session(self):
        if _server_token and is_authorized(urlparse(self.path), self.headers, _server_token):
            cookie = SimpleCookie()
            cookie['passport_manager'] = _server_token
            cookie['passport_manager']['httponly'] = True
            cookie['passport_manager']['samesite'] = 'Strict'
            cookie['passport_manager']['path'] = '/'
            # No expiry: the session ends with the browser or manager token.
            self.send_header('Set-Cookie', cookie.output(header='').strip())

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
    global _server_token

    parser = argparse.ArgumentParser(description='Local manager for adding games and editing companions')
    parser.add_argument('--port', type=int, default=5555)
    parser.add_argument(
        '--lan',
        action='store_true',
        help='Allow access from other devices on the same network'
    )
    parser.add_argument(
        '--token',
        default=None,
        help='Token required for adding games and editing companions. Defaults to a random token printed at startup.'
    )
    args = parser.parse_args()

    _server_token = args.token or secrets.token_urlsafe(18)
    bind_host = bind_host_for_mode(args.lan)

    print(f"Starting server on port {args.port}...")
    print(f"  Mode:   {'LAN enabled' if args.lan else 'local only'}")
    print(f"  Local:  {build_url('localhost', args.port, _server_token)}")
    print(f"  Edit companions: {build_url('localhost', args.port, _server_token).replace('/?', '/companions?')}")
    if args.lan:
        local_ip = get_local_ip()
        print(f"  Phone:  {build_url(local_ip, args.port, _server_token)}")
        print("  Note:   LAN mode allows devices on the same network to reach this server.")
    else:
        print("  Phone:  disabled (restart with --lan to allow same-wifi access)")
    print("  Token:  required for adding games and editing companions")
    print(f"  Press Ctrl+C to stop\n")

    server = ThreadingHTTPServer((bind_host, args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == '__main__':
    main()
