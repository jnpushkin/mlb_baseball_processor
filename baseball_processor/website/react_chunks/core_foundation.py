"""React app chunk: core foundation."""

CODE = r'''const { useState, useMemo, useEffect, useRef } = React;

// ── Global utilities (shared across all components) ──
const toSortableDate = (d) => {
    if (!d) return '';
    const text = String(d).trim();
    if (/^\d{8}$/.test(text)) return text;
    if (text.includes('/')) { const [m, dd, y] = text.split('/'); return `${y}${(m||'').padStart(2,'0')}${(dd||'').padStart(2,'0')}`; }
    const parsed = Date.parse(text);
    if (!Number.isNaN(parsed)) {
        const date = new Date(parsed);
        return `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`;
    }
    return text;
};
const formatLongDate = (d) => {
    const key = toSortableDate(d);
    if (!/^\d{8}$/.test(key)) return d || '';
    const year = Number(key.slice(0, 4));
    const month = Number(key.slice(4, 6)) - 1;
    const day = Number(key.slice(6, 8));
    return new Date(Date.UTC(year, month, day)).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        timeZone: 'UTC',
    });
};
const isFirstCareerEvent = (m) => /^(first|1st)\s+career/i.test(m || '');
const shortenMilestone = (m) => (m || '').replace('First Career ', '1st Career ').replace('Home Run', 'HR').replace('Stolen Base', 'SB').replace('Run Scored', 'Run').replace('Strikeout', 'K').replace('Inning Pitched', 'IP').replace('Double', '2B').replace('Triple', '3B');
const getLastName = (name) => {
    const suffixes = ['jr.', 'jr', 'sr.', 'sr', 'ii', 'iii', 'iv'];
    const parts = (name || '').split(' ').filter(p => !suffixes.includes(p.toLowerCase()));
    const particles = ['de', 'la', 'del', 'van', 'von', 'di', 'el', 'al', 'dos', 'das', 'le', 'da'];
    if (parts.length >= 3 && particles.includes(parts[parts.length - 2].toLowerCase())) return parts.slice(-2).join(' ');
    return parts[parts.length - 1] || name || '?';
};
const getHrCount = (detail) => { const match = detail?.match(/(\d+)\s*HR/); return match ? parseInt(match[1], 10) : 0; };
// Returns true when a cell value should always sink to the bottom of a sort,
// regardless of direction. Covers nulls, blanks, dash placeholders, and the
// stringified-NaN that some renders produce for missing numbers.
const isMissingValue = (v) => v === null || v === undefined || v === '' || v === '-' || v === 'NaN' || (typeof v === 'number' && Number.isNaN(v));

// Aggregation utilities
const aggregateHitterStats = (playerGames) => {
    const grouped = {};
    
    playerGames.forEach(game => {
        const key = game.playerId;
        if (!grouped[key]) {
            grouped[key] = {
                playerId: game.playerId,
                name: game.name,
                teams: new Set(),
                games: 0,
                ab: 0, pa: 0, h: 0, r: 0, rbi: 0, hr: 0,
                doubles: 0, triples: 0, sb: 0, cs: 0, bb: 0, so: 0, hbp: 0, gidp: 0,
                _maxEV: 0, _evSum: 0, _evCount: 0, _maxDist: 0
            };
        }

        grouped[key].teams.add(game.team);
        grouped[key].games += 1;
        grouped[key].ab += game.ab;
        grouped[key].pa += game.pa;
        grouped[key].h += game.h;
        grouped[key].r += game.r;
        grouped[key].rbi += game.rbi;
        grouped[key].hr += (game.hr || 0);
        grouped[key].doubles += (game.doubles || 0);
        grouped[key].triples += (game.triples || 0);
        grouped[key].sb += (game.sb || 0);
        grouped[key].cs += (game.cs || 0);
        grouped[key].bb += (game.bb || 0);
        grouped[key].so += (game.so || 0);
        grouped[key].hbp += (game.hbp || 0);
        grouped[key].gidp += (game.gidp || 0);
        // Exit velo aggregation
        if (game.maxExitVelo) {
            grouped[key]._maxEV = Math.max(grouped[key]._maxEV, game.maxExitVelo);
        }
        if (game.avgExitVelo) {
            const balls = game.battedBalls || 1;
            grouped[key]._evSum += game.avgExitVelo * balls;
            grouped[key]._evCount += balls;
        }
        if (game.maxDistance) {
            grouped[key]._maxDist = Math.max(grouped[key]._maxDist, game.maxDistance);
        }
    });

    return Object.values(grouped).map(p => {
        const singles = p.h - p.doubles - p.triples - p.hr;
        const tb = singles + (p.doubles * 2) + (p.triples * 3) + (p.hr * 4);
        const xbh = p.doubles + p.triples + p.hr;
        const avg = p.ab > 0 ? (p.h / p.ab).toFixed(3) : '0.000';
        const obp = p.pa > 0 ? ((p.h + p.bb + p.hbp) / p.pa).toFixed(3) : '0.000';
        const slg = p.ab > 0 ? (tb / p.ab).toFixed(3) : '0.000';
        const ops = (parseFloat(obp) + parseFloat(slg)).toFixed(3);
        const maxExitVelo = p._maxEV > 0 ? p._maxEV : null;
        const avgExitVelo = p._evCount > 0 ? Math.round(p._evSum / p._evCount * 10) / 10 : null;
        const maxDistance = p._maxDist > 0 ? p._maxDist : null;

        return {
            ...p,
            team: Array.from(p.teams).join(', '),
            tb, xbh, avg, obp, slg, ops, maxExitVelo, avgExitVelo, maxDistance
        };
    });
};

const aggregatePitcherStats = (pitcherGames) => {
    const grouped = {};

    pitcherGames.forEach(game => {
        const key = game.playerId;
        if (!grouped[key]) {
            grouped[key] = {
                playerId: game.playerId,
                name: game.name,
                teams: new Set(),
                games: 0, gameStarts: 0, wins: 0, losses: 0, saves: 0,
                outs: 0, h: 0, r: 0, er: 0, bb: 0, so: 0, hr: 0,
                _maxSpeed: 0, _speedSum: 0, _speedCount: 0,
                _spinSum: 0, _spinCount: 0, _totalPitches: 0
            };
        }

        grouped[key].teams.add(game.team);
        grouped[key].games += 1;
        grouped[key].gameStarts += (game.gameStarts || 0);
        grouped[key].wins += (game.wins || 0);
        grouped[key].losses += (game.losses || 0);
        grouped[key].saves += (game.saves || 0);
        grouped[key].outs += (game.outs || 0);
        grouped[key].h += (game.h || 0);
        grouped[key].r += (game.r || 0);
        grouped[key].er += (game.er || 0);
        grouped[key].bb += (game.bb || 0);
        grouped[key].so += (game.so || 0);
        grouped[key].hr += (game.hr || 0);
        // Pitch data aggregation
        if (game.maxSpeed) {
            grouped[key]._maxSpeed = Math.max(grouped[key]._maxSpeed, game.maxSpeed);
        }
        if (game.avgSpeed) {
            const pitches = game.totalPitches || 1;
            grouped[key]._speedSum += game.avgSpeed * pitches;
            grouped[key]._speedCount += pitches;
        }
        if (game.avgSpinRate) {
            const pitches = game.totalPitches || 1;
            grouped[key]._spinSum += game.avgSpinRate * pitches;
            grouped[key]._spinCount += pitches;
        }
        grouped[key]._totalPitches += (game.totalPitches || 0);
    });

    return Object.values(grouped).map(p => {
        const innings = p.outs / 3;
        const ip = `${Math.floor(innings)}.${p.outs % 3}`;
        const era = innings > 0 ? ((p.er * 9) / innings).toFixed(2) : 'N/A';
        const whip = innings > 0 ? ((p.h + p.bb) / innings).toFixed(3) : 'N/A';
        const maxSpeed = p._maxSpeed > 0 ? p._maxSpeed : null;
        const avgSpeed = p._speedCount > 0 ? Math.round(p._speedSum / p._speedCount * 10) / 10 : null;
        const avgSpinRate = p._spinCount > 0 ? Math.round(p._spinSum / p._spinCount) : null;

        return {
            ...p,
            team: Array.from(p.teams).join(', '),
            ip, era, whip, maxSpeed, avgSpeed, avgSpinRate,
            totalPitches: p._totalPitches
        };
    });
};

const exportToJSON = (data, filename) => {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
};

const usePagination = (data, rowsPerPage = 50) => {
    const [page, setPage] = useState(1);
    const totalPages = Math.ceil(data.length / rowsPerPage);
    const paginatedData = data.slice((page - 1) * rowsPerPage, page * rowsPerPage);

    useEffect(() => { setPage(1); }, [data.length]);

    return { page, setPage, totalPages, paginatedData, totalItems: data.length };
};

const PaginationControls = ({ page, setPage, totalPages, totalItems, rowsPerPage = 50 }) => {
    if (totalPages <= 1) return null;
    const start = (page - 1) * rowsPerPage + 1;
    const end = Math.min(page * rowsPerPage, totalItems);
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', fontSize: '0.8rem', color: '#6b7280' }}>
            <span>Showing {start}-{end} of {totalItems}</span>
            <div style={{ display: 'flex', gap: '4px' }}>
                <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    style={{ padding: '4px 8px', border: '1px solid #d1d5db', borderRadius: '4px', cursor: page === 1 ? 'default' : 'pointer', opacity: page === 1 ? 0.5 : 1 }}
                >← Prev</button>
                <span style={{ padding: '4px 8px' }}>{page} / {totalPages}</span>
                <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    style={{ padding: '4px 8px', border: '1px solid #d1d5db', borderRadius: '4px', cursor: page === totalPages ? 'default' : 'pointer', opacity: page === totalPages ? 0.5 : 1 }}
                >Next →</button>
            </div>
        </div>
    );
};

const exportToCSV = (data, columns, filename) => {
    const headers = columns.map(col => col.label).join(',');
    const rows = data.map(row => 
        columns.map(col => {
            let val = row[col.key];
            if (typeof val === 'string' && val.includes(',')) {
                val = `"${val}"`;
            }
            return val;
        }).join(',')
    );
    const csv = [headers, ...rows].join('\\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
};

const PlayerLink = ({ playerId, name, external }) => {
    if (!playerId || playerId === 'UNKNOWN') return <span>{name}</span>;
    const isRegisterFormat = playerId.length >= 10 && /\d{3}/.test(playerId.substring(5, 9));
    const brefUrl = isRegisterFormat
        ? `https://www.baseball-reference.com/register/player.fcgi?id=${playerId}`
        : `https://www.baseball-reference.com/players/${playerId.charAt(0).toLowerCase()}/${playerId}.shtml`;

    if (external) {
        return <a href={brefUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{name}</a>;
    }

    // Default: navigate to Players tab and open timeline
    const handleClick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        window._pendingPlayerSelect = { id: playerId, name };
        if (window.__navigateTab) window.__navigateTab('players');
    };

    return (
        <span className="inline-flex items-center gap-1">
            <a href="#players" onClick={handleClick} className="text-blue-600 hover:underline">{name}</a>
            <a href={brefUrl} target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-slate-600 text-[10px]" title="View on Baseball Reference">↗</a>
        </span>
    );
};

const requestGameDetails = (gameId, options = {}) => {
    if (!gameId) return;
    const request = {
        gameId,
        focus: options.focus || null,
        tab: options.tab || options.focus?.tab || null,
    };
    window.__pendingGameDetailsRequest = request;
    window.dispatchEvent(new CustomEvent('gameDetailsRequest', { detail: request }));
    if (window.__navigateTab) window.__navigateTab('gamelog');
};

const consumePendingGameDetailsRequest = () => {
    const request = window.__pendingGameDetailsRequest || null;
    window.__pendingGameDetailsRequest = null;
    return request;
};

const GameLink = ({ gameId, mlbGamePk, source }) => {
    if (!gameId || gameId === 'UNKNOWN') return <span className="small-text">{gameId}</span>;

    // Use MLB.com for spring training games (source='mlb') that have a game_pk
    if (mlbGamePk && source === 'mlb') {
        const url = `https://www.mlb.com/gameday/${mlbGamePk}/final/box`;
        return <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-mono small-text">{gameId}</a>;
    }

    // Default to Baseball Reference
    const teamCode = gameId.substring(0, 3);
    const url = `https://www.baseball-reference.com/boxes/${teamCode}/${gameId}.shtml`;
    return <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-mono small-text">{gameId}</a>;
};

const TEAM_LOGO_IDS = {
    ARI: 109,
    ATL: 144,
    BAL: 110,
    BOS: 111,
    CHC: 112, CHN: 112,
    CIN: 113,
    CLE: 114,
    COL: 115,
    CWS: 145, CHA: 145, CHW: 145,
    DET: 116,
    HOU: 117,
    KC: 118, KCA: 118,
    LAA: 108, ANA: 108,
    LAD: 119, LAN: 119, LA: 119,
    MIA: 146, FLA: 146,
    MIL: 158,
    MIN: 142,
    MTY: 562,
    NYM: 121, NYN: 121,
    NYY: 147, NYA: 147,
    OAK: 133, ATH: 133,
    PHI: 143,
    PIT: 134,
    SD: 135, SDN: 135,
    SEA: 136,
    SF: 137, SFN: 137,
    STL: 138, SLN: 138,
    TB: 139, TBA: 139,
    TEX: 140,
    TOR: 141,
    WSH: 120, WAS: 120, WSN: 120
};

const getTeamLogoUrl = (code) => {
    const id = TEAM_LOGO_IDS[String(code || '').trim().toUpperCase()];
    return id ? `https://www.mlbstatic.com/team-logos/${id}.svg` : null;
};

const TeamLogo = ({ code, size = 22, className = '' }) => {
    const [failed, setFailed] = useState(false);
    const cleanCode = String(code || '').trim().toUpperCase();
    const url = failed ? null : getTeamLogoUrl(cleanCode);
    const style = { width: size, height: size };
    const wrapperClass = `inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-white/95 ring-1 ring-slate-200 ${className}`;

    if (!url) {
        return (
            <span className={wrapperClass} style={style} title={cleanCode || 'Team'}>
                <span className="text-[9px] font-bold leading-none text-slate-500">{(cleanCode || '?').slice(0, 3)}</span>
            </span>
        );
    }

    return (
        <span className={wrapperClass} style={style} title={`${cleanCode} logo`}>
            <img
                src={url}
                alt={`${cleanCode} logo`}
                loading="lazy"
                className="h-full w-full object-contain p-0.5"
                onError={() => setFailed(true)}
            />
        </span>
    );
};

const TeamToken = ({ code, logoSize = 20, className = '' }) => (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
        <TeamLogo code={code} size={logoSize} />
        <span>{code}</span>
    </span>
);

const escapeHtml = (value) => String(value || '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
}[char]));

const getStadiumMarkerCode = (stadium) => {
    const rawCode = String(stadium?.team || '').trim().toUpperCase();
    if (!rawCode || stadium?.springTraining) return 'ST';
    if (stadium?.international) return 'INT';
    return rawCode;
};

const getFlagUrl = (countryCode) => {
    const cleanCode = String(countryCode || '').trim().toLowerCase();
    return cleanCode ? `https://flagcdn.com/w80/${cleanCode}.png` : null;
};

const getTeamLogoHtml = (code, className = 'stadium-logo-marker-img', fallbackClassName = 'stadium-logo-cluster-code') => {
    const cleanCode = String(code || '').trim().toUpperCase();
    const logoUrl = getTeamLogoUrl(cleanCode);

    if (logoUrl) {
        return `<img class="${className}" src="${logoUrl}" alt="${escapeHtml(cleanCode)} logo" loading="lazy">`;
    }

    return `<span class="${fallbackClassName}">${escapeHtml((cleanCode || '?').slice(0, 3))}</span>`;
};

const getStadiumLogoInnerHtml = (stadium) => {
    const springTeams = Array.isArray(stadium?.teams)
        ? stadium.teams.map(t => String(t || '').trim().toUpperCase()).filter(Boolean)
        : [];

    if (stadium?.springTraining && springTeams.length > 0) {
        if (springTeams.length === 1) {
            return getTeamLogoHtml(springTeams[0]);
        }

        if (springTeams.length === 2) {
            return `
                <span class="stadium-logo-split">
                    ${springTeams.map(code => `
                        <span class="stadium-logo-split-half">
                            ${getTeamLogoHtml(code, 'stadium-logo-split-img', 'stadium-logo-split-code')}
                        </span>
                    `).join('')}
                </span>
            `;
        }

        const visibleTeams = springTeams.slice(0, 4);
        return `
            <span class="stadium-logo-cluster team-count-${visibleTeams.length}">
                ${visibleTeams.map(code => getTeamLogoHtml(code, 'stadium-logo-cluster-img')).join('')}
            </span>
        `;
    }

    if (stadium?.international) {
        const flagUrl = getFlagUrl(stadium.countryCode);
        const label = stadium.flagLabel || stadium.city || 'International';

        if (flagUrl) {
            return `<img class="stadium-logo-marker-img stadium-flag-marker-img" src="${flagUrl}" alt="${escapeHtml(label)} flag" loading="lazy">`;
        }

        return `<span class="stadium-logo-marker-code">${escapeHtml(String(label).slice(0, 3).toUpperCase() || 'INT')}</span>`;
    }

    const code = getStadiumMarkerCode(stadium);
    return getTeamLogoHtml(code);
};

const getStadiumLogoMarkerSize = (stadium, hasVisited, zoom = 4) => {
    const hasTeamCluster = stadium?.springTraining && Array.isArray(stadium.teams) && stadium.teams.length > 1;
    const baseSize = hasVisited ? (hasTeamCluster ? 30 : 26) : (hasTeamCluster ? 24 : 20);
    const zoomScale = zoom <= 3 ? 0.72 : zoom <= 4 ? 0.84 : zoom === 5 ? 1 : Math.min(1.28, 1 + ((zoom - 5) * 0.08));
    return Math.round(baseSize * zoomScale);
};

const createStadiumLogoMarker = (stadium, { hasVisited, fillColor, borderColor, zoom = 4 }) => {
    const markerSize = getStadiumLogoMarkerSize(stadium, hasVisited, zoom);
    const markerHtml = `
        <div
            class="stadium-logo-marker ${hasVisited ? 'is-visited' : 'is-unvisited'}"
            style="--marker-size: ${markerSize}px; --marker-bg: ${fillColor}; --marker-ring: ${borderColor};"
            title="${escapeHtml(stadium?.name || '')}"
        >
            ${getStadiumLogoInnerHtml(stadium)}
        </div>
    `;

    return L.marker([stadium.lat, stadium.lng], {
        icon: L.divIcon({
            className: 'stadium-logo-marker-shell',
            html: markerHtml,
            iconSize: [markerSize, markerSize],
            iconAnchor: [markerSize / 2, markerSize / 2],
            popupAnchor: [0, -(markerSize / 2)],
        }),
        keyboard: true,
        title: stadium?.name || '',
        zIndexOffset: hasVisited ? 200 : 0,
    });
};

const getStadiumPopupHeaderHtml = (stadium, teamLabel, metaSuffix = '') => `
    <div class="stadium-popup-header">
        <span class="stadium-popup-logo">${getStadiumLogoInnerHtml(stadium)}</span>
        <div>
            <h3 class="stadium-popup-title">${escapeHtml(stadium?.name || '')}</h3>
            <div class="stadium-popup-meta">${escapeHtml(teamLabel || '')}${metaSuffix}</div>
        </div>
    </div>
`;

const EmptyState = ({ icon = '📭', title = 'No data', message = 'There is nothing to display.' }) => (
    <div className="flex flex-col items-center justify-center p-12 text-center">
        <span className="text-5xl mb-4">{icon}</span>
        <h3 className="subsection-title font-bold text-slate-700 mb-2">{title}</h3>
        <p className="body-text text-slate-500 max-w-md">{message}</p>
    </div>
);

const isDark = () => document.documentElement.classList.contains('dark');
const chartColors = () => {
    const dark = isDark();
    return {
        text: dark ? '#cbd5e1' : '#334155',
        grid: dark ? 'rgba(148,163,184,0.15)' : 'rgba(0,0,0,0.06)',
        legend: dark ? '#e2e8f0' : '#334155',
        tooltip: { bg: dark ? '#1e293b' : '#fff', border: dark ? '#475569' : '#e2e8f0', text: dark ? '#f1f5f9' : '#0f172a' }
    };
};

const MilestoneChart = ({ milestones }) => {
    const canvasRef = useRef(null);
    useEffect(() => {
        if (!canvasRef.current || !milestones?.length) return;
        const ctx = canvasRef.current.getContext('2d');
        const cc = chartColors();
        const typeCounts = {};
        milestones.forEach(m => { typeCounts[m.type] = (typeCounts[m.type] || 0) + 1; });

        // Only top 5 for performance
        const sortedTypes = Object.entries(typeCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedTypes.map(([type]) => type),
                datasets: [{
                    label: 'Count',
                    data: sortedTypes.map(([, count]) => count),
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(147, 51, 234, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(251, 146, 60, 0.8)'
                    ]
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: cc.tooltip.bg, titleColor: cc.tooltip.text, bodyColor: cc.tooltip.text,
                        borderColor: cc.tooltip.border, borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.x} milestone${context.parsed.x !== 1 ? 's' : ''}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { font: { size: 11 }, color: cc.text },
                        grid: { color: cc.grid }
                    },
                    y: {
                        ticks: { font: { size: 12 }, color: cc.text },
                        grid: { color: cc.grid }
                    }
                }
            }
        });
        return () => chart.destroy();
    }, [milestones]);
    return <canvas ref={canvasRef} className="w-full" style={{ height: '220px' }} />;
};

const TeamChart = ({ teams }) => {
    const canvasRef = useRef(null);
    useEffect(() => {
        if (!canvasRef.current || !teams?.length) return;
        const ctx = canvasRef.current.getContext('2d');
        const cc = chartColors();

        // Top 8 teams by games attended
        const topTeams = teams.slice(0, 8);

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: topTeams.map(t => t.team),
                datasets: [
                    {
                        label: 'Runs Scored',
                        data: topTeams.map(t => t.runs),
                        backgroundColor: 'rgba(34, 197, 94, 0.8)',
                        borderColor: 'rgba(34, 197, 94, 1)',
                        borderWidth: 2
                    },
                    {
                        label: 'Runs Allowed',
                        data: topTeams.map(t => t.runsAllowed),
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: 'rgba(239, 68, 68, 1)',
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: { size: 12 },
                            padding: 12,
                            usePointStyle: true,
                            color: cc.legend
                        }
                    },
                    tooltip: {
                        backgroundColor: cc.tooltip.bg, titleColor: cc.tooltip.text, bodyColor: cc.tooltip.text,
                        borderColor: cc.tooltip.border, borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { font: { size: 11 }, color: cc.text },
                        grid: { color: cc.grid }
                    },
                    x: {
                        ticks: { font: { size: 12, weight: 'bold' }, color: cc.text },
                        grid: { color: cc.grid }
                    }
                }
            }
        });
        return () => chart.destroy();
    }, [teams]);
    return <canvas ref={canvasRef} className="w-full" style={{ height: '280px' }} />;
};

const StatCard = ({ title, value, subtitle, color = 'blue', onClick }) => {
    const accents = {
        blue: 'border-blue-600', green: 'border-emerald-600',
        purple: 'border-violet-600', orange: 'border-amber-600'
    };
    return (
        <div onClick={onClick} className={`bg-white rounded-lg border border-slate-200 border-l-[3px] ${accents[color]} p-4 ${onClick ? 'cursor-pointer hover:border-slate-300' : ''}`} style={{ boxShadow: 'var(--shadow)' }}>
            <div className="small-text font-medium text-slate-500 mb-1">{title}</div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
            {subtitle && <div className="small-text text-slate-400 mt-0.5">{subtitle}</div>}
        </div>
    );
};


'''
