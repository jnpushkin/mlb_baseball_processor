"""React component code for the baseball statistics website."""

class ReactComponents:
    """React component templates."""
    
    @staticmethod
    def get_app_code():
        """Get the complete React app code with enhanced interactive insights."""
        return r"""const { useState, useMemo, useEffect, useRef } = React;

// ── Global utilities (shared across all components) ──
const toSortableDate = (d) => {
    if (!d) return '';
    if (d.includes('/')) { const [m, dd, y] = d.split('/'); return `${y}${(m||'').padStart(2,'0')}${(dd||'').padStart(2,'0')}`; }
    return d;
};
const shortenMilestone = (m) => (m || '').replace('First Career ', '1st Career ').replace('Home Run', 'HR').replace('Stolen Base', 'SB').replace('Run Scored', 'Run').replace('Strikeout', 'K').replace('Inning Pitched', 'IP').replace('Double', '2B').replace('Triple', '3B');
const getLastName = (name) => {
    const suffixes = ['jr.', 'jr', 'sr.', 'sr', 'ii', 'iii', 'iv'];
    const parts = (name || '').split(' ').filter(p => !suffixes.includes(p.toLowerCase()));
    const particles = ['de', 'la', 'del', 'van', 'von', 'di', 'el', 'al', 'dos', 'das', 'le', 'da'];
    if (parts.length >= 3 && particles.includes(parts[parts.length - 2].toLowerCase())) return parts.slice(-2).join(' ');
    return parts[parts.length - 1] || name || '?';
};
const getHrCount = (detail) => { const match = detail?.match(/(\d+)\s*HR/); return match ? parseInt(match[1], 10) : 0; };

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


const GameDetailsModal = ({ game, playerGames, pitcherGames, careerFirsts, allTimePassings, badges, onClose, onPrev, onNext, gameIndex, totalGames }) => {
    const [activeTab, setActiveTab] = useState('boxscore');

    useEffect(() => {
        const onKey = (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'ArrowLeft' && onPrev) { e.stopPropagation(); onPrev(); }
            if (e.key === 'ArrowRight' && onNext) { e.stopPropagation(); onNext(); }
        };
        window.addEventListener('keydown', onKey, true);
        return () => window.removeEventListener('keydown', onKey, true);
    }, [onPrev, onNext]);

    const gameData = useMemo(() => {
        if (!game) return null;

        // Get all players/pitchers from this game
        const gamePlayers = playerGames.filter(pg => pg.gameId === game.gameId);
        const gamePitchers = pitcherGames.filter(pg => pg.gameId === game.gameId);

        // Separate by team
        const homeHitters = gamePlayers.filter(p => p.team === game.homeTeam && (p.pa > 0 || p.ab > 0)).sort((a, b) => b.pa - a.pa);
        const awayHitters = gamePlayers.filter(p => p.team === game.awayTeam && (p.pa > 0 || p.ab > 0)).sort((a, b) => b.pa - a.pa);
        const homePitchers = gamePitchers.filter(p => p.team === game.homeTeam).sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
        const awayPitchers = gamePitchers.filter(p => p.team === game.awayTeam).sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
        
        // Calculate team totals
        const homeHittingTotals = homeHitters.reduce((acc, p) => ({
            ab: acc.ab + p.ab,
            h: acc.h + p.h,
            r: acc.r + p.r,
            rbi: acc.rbi + p.rbi,
            hr: acc.hr + p.hr,
            doubles: acc.doubles + (p.doubles || 0),
            triples: acc.triples + (p.triples || 0),
            bb: acc.bb + p.bb,
            so: acc.so + p.so
        }), { ab: 0, h: 0, r: 0, rbi: 0, hr: 0, doubles: 0, triples: 0, bb: 0, so: 0 });

        const awayHittingTotals = awayHitters.reduce((acc, p) => ({
            ab: acc.ab + p.ab,
            h: acc.h + p.h,
            r: acc.r + p.r,
            rbi: acc.rbi + p.rbi,
            hr: acc.hr + p.hr,
            doubles: acc.doubles + (p.doubles || 0),
            triples: acc.triples + (p.triples || 0),
            bb: acc.bb + p.bb,
            so: acc.so + p.so
        }), { ab: 0, h: 0, r: 0, rbi: 0, hr: 0, doubles: 0, triples: 0, bb: 0, so: 0 });
        
        // Build annotations from career firsts and superlatives
        const playerAnnotations = {};
        (careerFirsts || []).forEach(f => {
            if (!playerAnnotations[f.player_id]) playerAnnotations[f.player_id] = [];
            playerAnnotations[f.player_id].push(f.milestone);
        });

        // Players seen live for the first time in this game (precomputed
        // by the serializer by walking attended games chronologically).
        const firstSeenSet = new Set(game.firstSeenPlayerIds || []);

        // Find game superlatives from pitch/hit data
        let fastestPitch = null, hardestHit = null, mostKs = null;
        if (game.pitchData) {
            Object.entries(game.pitchData).forEach(([pid, pd]) => {
                if (pd.maxSpeed && (!fastestPitch || pd.maxSpeed > fastestPitch.speed)) {
                    fastestPitch = { playerId: pid, name: pd.name, speed: pd.maxSpeed };
                }
            });
        }
        if (game.hitData) {
            Object.entries(game.hitData).forEach(([pid, hd]) => {
                if (hd.maxExitVelo && (!hardestHit || hd.maxExitVelo > hardestHit.velo)) {
                    hardestHit = { playerId: pid, name: hd.name, velo: hd.maxExitVelo, dist: hd.maxDistance };
                }
            });
        }
        const allPitchers = [...homePitchers, ...awayPitchers];
        allPitchers.forEach(p => {
            if (p.so > 0 && (!mostKs || p.so > mostKs.so)) {
                mostKs = { playerId: p.playerId, name: p.name, so: p.so };
            }
        });

        return {
            homeHitters, awayHitters, homePitchers, awayPitchers,
            homeHittingTotals, awayHittingTotals,
            playerAnnotations, fastestPitch, hardestHit, mostKs,
            firstSeenSet
        };
    }, [game, playerGames, pitcherGames, careerFirsts]);

    if (!game || !gameData) return null;

    const CareerHighBadges = ({ data }) => {
        if (!data.careerHighs?.length) return null;
        return <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">Career-high {data.careerHighs.join(', ')}</span>;
    };

    const HitterRow = ({ player }) => {
        const annotations = gameData.playerAnnotations[player.playerId] || [];
        const isHardestHit = gameData.hardestHit?.playerId === player.playerId;
        const isFirstSeen = gameData.firstSeenSet?.has(player.playerId);
        return (
        <tr className="hover:bg-slate-50">
            <td className="px-3 py-2">
                <div className="flex items-center gap-1 flex-wrap">
                    <PlayerLink playerId={player.playerId} name={player.name} />
                    {isFirstSeen && <span title="First time seeing this player live" className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">1st seen</span>}
                    {annotations.length > 0 && <span title={annotations.join(', ')} className="text-amber-500 text-xs">⭐</span>}
                    {isHardestHit && <span title={`Hardest hit: ${gameData.hardestHit.velo} mph`} className="text-red-500 text-xs">💪</span>}
                    <CareerHighBadges data={player} />
                </div>
            </td>
            <td className="px-2 py-2 text-center">{player.ab || 0}</td>
            <td className="px-2 py-2 text-center font-semibold">{player.h || 0}</td>
            <td className="px-2 py-2 text-center">{player.r || 0}</td>
            <td className="px-2 py-2 text-center">{player.rbi || 0}</td>
            <td className={`px-2 py-2 text-center ${player.hr > 0 ? 'font-bold text-blue-600' : ''}`}>{player.hr || 0}</td>
            <td className="px-2 py-2 text-center">{player.doubles || 0}</td>
            <td className="px-2 py-2 text-center">{player.triples || 0}</td>
            <td className="px-2 py-2 text-center">{player.bb || 0}</td>
            <td className="px-2 py-2 text-center">{player.so || 0}</td>
        </tr>
    );
    };

    const PitcherRow = ({ pitcher }) => {
        const ip = `${Math.floor(pitcher.outs / 3)}.${pitcher.outs % 3}`;
        const decision = pitcher.wins ? 'W' : pitcher.losses ? 'L' : pitcher.saves ? 'SV' : '';
        const annotations = gameData.playerAnnotations[pitcher.playerId] || [];
        const isFastest = gameData.fastestPitch?.playerId === pitcher.playerId;
        const isMostKs = gameData.mostKs?.playerId === pitcher.playerId && pitcher.so >= 6;
        const isFirstSeen = gameData.firstSeenSet?.has(pitcher.playerId);

        return (
            <tr className="hover:bg-slate-50">
                <td className="px-3 py-2">
                    <div className="flex items-center gap-2 flex-wrap">
                        <PlayerLink playerId={pitcher.playerId} name={pitcher.name} />
                        {isFirstSeen && <span title="First time seeing this player live" className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">1st seen</span>}
                        {decision && (
                            <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                                decision === 'W' ? 'bg-green-100 text-green-700' :
                                decision === 'L' ? 'bg-red-100 text-red-700' :
                                'bg-blue-100 text-blue-700'
                            }`}>
                                {decision}
                            </span>
                        )}
                        {annotations.length > 0 && <span title={annotations.join(', ')} className="text-amber-500 text-xs">⭐</span>}
                        {isFastest && <span title={`Fastest pitch: ${gameData.fastestPitch.speed} mph`} className="text-red-500 text-xs">🔥</span>}
                        {isMostKs && <span title={`Game-high ${pitcher.so} strikeouts`} className="text-orange-500 text-xs">🔥</span>}
                        <CareerHighBadges data={pitcher} />
                    </div>
                </td>
                <td className="px-2 py-2 text-center font-semibold">{ip}</td>
                <td className="px-2 py-2 text-center">{pitcher.h || 0}</td>
                <td className="px-2 py-2 text-center">{pitcher.r || 0}</td>
                <td className="px-2 py-2 text-center">{pitcher.er || 0}</td>
                <td className="px-2 py-2 text-center">{pitcher.bb || 0}</td>
                <td className="px-2 py-2 text-center font-semibold">{pitcher.so || 0}</td>
                <td className="px-2 py-2 text-center">{pitcher.hr || 0}</td>
            </tr>
        );
    };
    
    // Tab content components
    const BoxScoreTab = () => (
        <>
            {/* Away Team Hitters */}
            <div className="p-6 border-b">
                <h4 className="subsection-title font-bold mb-3">{game.awayTeam} Batting</h4>
                <div className="overflow-x-auto">
                    <table className="w-full small-text">
                        <thead className="bg-slate-50 border-b-2">
                            <tr>
                                <th className="px-3 py-2 text-left">Batter</th>
                                <th className="px-2 py-2">AB</th>
                                <th className="px-2 py-2">H</th>
                                <th className="px-2 py-2">R</th>
                                <th className="px-2 py-2">RBI</th>
                                <th className="px-2 py-2">HR</th>
                                <th className="px-2 py-2">2B</th>
                                <th className="px-2 py-2">3B</th>
                                <th className="px-2 py-2">BB</th>
                                <th className="px-2 py-2">SO</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {gameData.awayHitters.map((p) => <HitterRow key={p.playerId} player={p} />)}
                            <tr className="bg-blue-50 font-bold">
                                <td className="px-3 py-2">Team Totals</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.ab}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.h}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.r}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.rbi}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.hr}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.doubles}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.triples}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.bb}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.so}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            {/* Home Team Hitters */}
            <div className="p-6 border-b">
                <h4 className="subsection-title font-bold mb-3">{game.homeTeam} Batting</h4>
                <div className="overflow-x-auto">
                    <table className="w-full small-text">
                        <thead className="bg-slate-50 border-b-2">
                            <tr>
                                <th className="px-3 py-2 text-left">Batter</th>
                                <th className="px-2 py-2">AB</th>
                                <th className="px-2 py-2">H</th>
                                <th className="px-2 py-2">R</th>
                                <th className="px-2 py-2">RBI</th>
                                <th className="px-2 py-2">HR</th>
                                <th className="px-2 py-2">2B</th>
                                <th className="px-2 py-2">3B</th>
                                <th className="px-2 py-2">BB</th>
                                <th className="px-2 py-2">SO</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {gameData.homeHitters.map((p) => <HitterRow key={p.playerId} player={p} />)}
                            <tr className="bg-blue-50 font-bold">
                                <td className="px-3 py-2">Team Totals</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.ab}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.h}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.r}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.rbi}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.hr}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.doubles}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.triples}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.bb}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.so}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            {/* Pitching */}
            <div className="p-6 bg-slate-50">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Away Pitchers */}
                    <div>
                        <h4 className="subsection-title font-bold mb-3">{game.awayTeam} Pitching</h4>
                        <div className="overflow-x-auto">
                            <table className="w-full small-text bg-white rounded">
                                <thead className="bg-slate-50 border-b-2">
                                    <tr>
                                        <th className="px-3 py-2 text-left">Pitcher</th>
                                        <th className="px-2 py-2">IP</th>
                                        <th className="px-2 py-2">H</th>
                                        <th className="px-2 py-2">R</th>
                                        <th className="px-2 py-2">ER</th>
                                        <th className="px-2 py-2">BB</th>
                                        <th className="px-2 py-2">SO</th>
                                        <th className="px-2 py-2">HR</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {gameData.awayPitchers.map((p) => <PitcherRow key={p.playerId} pitcher={p} />)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    {/* Home Pitchers */}
                    <div>
                        <h4 className="subsection-title font-bold mb-3">{game.homeTeam} Pitching</h4>
                        <div className="overflow-x-auto">
                            <table className="w-full small-text bg-white rounded">
                                <thead className="bg-slate-50 border-b-2">
                                    <tr>
                                        <th className="px-3 py-2 text-left">Pitcher</th>
                                        <th className="px-2 py-2">IP</th>
                                        <th className="px-2 py-2">H</th>
                                        <th className="px-2 py-2">R</th>
                                        <th className="px-2 py-2">ER</th>
                                        <th className="px-2 py-2">BB</th>
                                        <th className="px-2 py-2">SO</th>
                                        <th className="px-2 py-2">HR</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {gameData.homePitchers.map((p) => <PitcherRow key={p.playerId} pitcher={p} />)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            {/* Pitch Data */}
            {game.pitchData && Object.keys(game.pitchData).length > 0 && (
                <div className="p-6 border-t">
                    <h4 className="subsection-title font-bold mb-3">Pitch Data</h4>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {Object.entries(game.pitchData).map(([pid, pd]) => (
                            <div key={pid} className="bg-slate-50 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-semibold body-text">{pd.name}</span>
                                    <span className="small-text text-slate-500">{pd.totalPitches} pitches</span>
                                </div>
                                <div className="grid grid-cols-3 gap-3 small-text mb-3">
                                    {pd.maxSpeed && (
                                        <div className="bg-white p-2 rounded text-center">
                                            <div className="text-slate-500">Max Velo</div>
                                            <div className="font-bold text-red-600">{pd.maxSpeed} mph</div>
                                        </div>
                                    )}
                                    {pd.avgSpeed && (
                                        <div className="bg-white p-2 rounded text-center">
                                            <div className="text-slate-500">Avg Velo</div>
                                            <div className="font-bold text-slate-900">{pd.avgSpeed} mph</div>
                                        </div>
                                    )}
                                    {pd.avgSpinRate && (
                                        <div className="bg-white p-2 rounded text-center">
                                            <div className="text-slate-500">Avg Spin</div>
                                            <div className="font-bold text-purple-600">{pd.avgSpinRate} rpm</div>
                                        </div>
                                    )}
                                </div>
                                {pd.pitchTypes && Object.keys(pd.pitchTypes).length > 0 && (
                                    <div className="flex flex-wrap gap-1.5">
                                        {Object.entries(pd.pitchTypes).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
                                            <span key={type} className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                                                {pd.pitchTypeNames?.[type] || type}: {count}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );

    const LineupsTab = () => {
        if (!game.lineups) {
            return (
                <div className="p-8 text-center text-slate-500 body-text">
                    Starting lineup data not available for this game
                </div>
            );
        }
        
        const LineupTable = ({ lineup, team }) => (
            <div>
                <h4 className="subsection-title font-bold mb-3">{team} Starting Lineup</h4>
                <div className="bg-white rounded-lg overflow-hidden">
                    <table className="w-full small-text">
                        <thead className="bg-slate-50 border-b-2">
                            <tr>
                                <th className="px-3 py-2 text-center">#</th>
                                <th className="px-3 py-2 text-left">Player</th>
                                <th className="px-3 py-2 text-center">Position</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {lineup.sort((a, b) => a.slot - b.slot).map((player) => (
                                <tr key={player.playerId} className="hover:bg-blue-50">
                                    <td className="px-3 py-2 text-center font-bold text-blue-600">{player.slot}</td>
                                    <td className="px-3 py-2">
                                        <div className="flex items-center gap-2">
                                            <PlayerLink playerId={player.playerId} name={player.name} />
                                            {player.jerseyNumber && <button className="text-xs text-slate-400 hover:text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('trivia', 'jerseys'); if (onClose) onClose(); }}>#{player.jerseyNumber}</button>}
                                        </div>
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                        <span className="px-2 py-1 bg-slate-100 rounded font-semibold">
                                            {player.position}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
        
        return (
            <div className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {game.lineups.away && game.lineups.away.length > 0 && (
                        <LineupTable lineup={game.lineups.away} team={game.awayTeam} />
                    )}
                    {game.lineups.home && game.lineups.home.length > 0 && (
                        <LineupTable lineup={game.lineups.home} team={game.homeTeam} />
                    )}
                </div>
            </div>
        );
    };
    
    const SubstitutionsTab = () => {
        // Derive substitutions from batting/pitching data if PBP parser didn't find any
        const derivedSubs = useMemo(() => {
            if (game.substitutions && game.substitutions.length > 0) return game.substitutions;
            const subs = [];
            ['away', 'home'].forEach(side => {
                const team = side === 'away' ? game.awayTeam : game.homeTeam;
                (game.batters?.[side] || []).forEach(p => {
                    if (p.isStarter) return;
                    const pos = p.position || '';
                    const type = pos === 'PH' ? 'pinch_hit' : pos === 'PR' ? 'pinch_run' : pos === 'P' ? 'pitching_change' : 'defensive_sub';
                    subs.push({ type, playerIn: p.name, playerOut: '', position: pos, inning: 0, half: side === 'away' ? 'top' : 'bottom', text: `${p.name} entered as ${pos} (${team})` });
                });
                (game.pitchers?.[side] || []).forEach((p, i) => {
                    if (i === 0) return; // starter
                    subs.push({ type: 'pitching_change', playerIn: p.name, playerOut: '', position: 'P', inning: 0, half: side === 'away' ? 'top' : 'bottom', text: `${p.name} entered to pitch (${team})` });
                });
            });
            return subs;
        }, [game]);

        if (!derivedSubs || derivedSubs.length === 0) {
            return (
                <div className="p-8 text-center text-slate-500 body-text">
                    No substitutions recorded for this game
                </div>
            );
        }
        
        const getSubIcon = (type) => {
            switch(type) {
                case 'pitching_change': return '⚾';
                case 'pinch_hit': return '🏏';
                case 'pinch_run': return '🏃';
                case 'defensive_sub': return '🛡️';
                case 'ph_to_defense': return '🔄';
                default: return '↔️';
            }
        };
        
        const getSubLabel = (type) => {
            switch(type) {
                case 'pitching_change': return 'Pitching Change';
                case 'pinch_hit': return 'Pinch Hitter';
                case 'pinch_run': return 'Pinch Runner';
                case 'defensive_sub': return 'Defensive Substitution';
                case 'ph_to_defense': return 'Position Change';
                default: return 'Substitution';
            }
        };
        
        return (
            <div className="p-6">
                <div className="space-y-3">
                    {derivedSubs.map((sub, idx) => (
                        <div key={`sub-${idx}-${sub.inning}-${sub.half}`} className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-blue-400 hover:shadow-md transition-all">
                            <div className="flex items-start gap-3">
                                <span className="text-2xl">{getSubIcon(sub.type)}</span>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-bold">
                                            {sub.half.toUpperCase()} {sub.inning}
                                        </span>
                                        <span className="body-text font-bold text-slate-700">
                                            {getSubLabel(sub.type)}
                                        </span>
                                    </div>
                                    <div className="body-text text-slate-800">
                                        {sub.playerIn && sub.playerOut ? (
                                            <>
                                                <span className="font-semibold text-green-600">{sub.playerIn}</span>
                                                {' '}replaces{' '}
                                                <span className="font-semibold text-red-600">{sub.playerOut}</span>
                                                {sub.position && <span className="text-slate-500"> at {sub.position}</span>}
                                            </>
                                        ) : (
                                            <span className="text-slate-600">{sub.text}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };
    
    const PlayByPlayTab = () => {
        if (!game.playByPlay || game.playByPlay.length === 0) {
            return (
                <div className="p-8 text-center text-slate-500 body-text">
                    Play-by-play data not available for this game
                </div>
            );
        }
        
        // Group plays by inning
        const playsByInning = {};
        game.playByPlay.forEach(play => {
            const key = `${play.inning}-${play.half}`;
            if (!playsByInning[key]) {
                playsByInning[key] = {
                    inning: play.inning,
                    half: play.half,
                    plays: []
                };
            }
            playsByInning[key].plays.push(play);
        });
        
        const sortedInnings = Object.values(playsByInning).sort((a, b) => {
            if (a.inning !== b.inning) return a.inning - b.inning;
            return a.half === 'top' ? -1 : 1;
        });
        
        return (
            <div className="p-6">
                <div className="space-y-6">
                    {sortedInnings.map((inning) => (
                        <div key={`${inning.half}-${inning.inning}`} className="bg-white rounded-lg shadow-sm overflow-hidden">
                            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2">
                                <span className="body-text font-bold">
                                    {inning.half.charAt(0).toUpperCase() + inning.half.slice(1)} of {inning.inning}
                                    {inning.inning === 1 ? 'st' : inning.inning === 2 ? 'nd' : inning.inning === 3 ? 'rd' : 'th'}
                                </span>
                                <span className="ml-3 small-text text-blue-100">
                                    {inning.plays.length} play{inning.plays.length !== 1 ? 's' : ''}
                                </span>
                            </div>
                            <div className="divide-y">
                                {inning.plays.map((play, playIdx) => (
                                    <div key={`play-${inning.inning}-${inning.half}-${playIdx}`} className={`p-3 hover:bg-blue-50 ${
                                        play.isHomeRun ? 'bg-orange-50' : 
                                        play.isStrikeout ? 'bg-red-50' : 
                                        play.isStolenBase ? 'bg-green-50' :
                                        play.isCaughtStealing ? 'bg-red-50' :
                                        ''
                                    }`}>
                                        <div className="flex items-start gap-3">
                                            <div className="text-center min-w-12">
                                                <div className="text-xs font-bold text-slate-500">
                                                    {play.outs !== null ? `${play.outs} out${play.outs !== 1 ? 's' : ''}` : ''}
                                                </div>
                                                {play.score && (
                                                    <div className="text-xs font-mono text-blue-600 font-bold">
                                                        {play.score}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex-1">
                                                <div className="body-text">
                                                    <span className="font-semibold text-slate-900">{play.batter}</span>
                                                    {' '}
                                                    <span className="text-slate-600">
                                                        {play.description}
                                                    </span>
                                                </div>
                                                <div className="small-text text-slate-500 mt-1">
                                                    vs {play.pitcher}
                                                    {play.pitchCount > 0 && ` • ${play.pitchCount} pitches`}
                                                </div>
                                            </div>
                                            {play.isHomeRun && (
                                                <span className="text-xl">⚾</span>
                                            )}
                                            {play.isStrikeout && (
                                                <span className="text-xl">🔥</span>
                                            )}
                                            {play.isStolenBase && (
                                                <span className="text-xl">🏃</span>
                                            )}
                                            {play.isCaughtStealing && (
                                                <span className="text-xl">❌</span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };
    
    return (
        <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div className="bg-white rounded-lg shadow-lg w-full max-h-[90vh] flex flex-col overflow-hidden" style={{ maxWidth: 'min(72rem, 95vw)' }} onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className={`p-6 border-b ${game.gameType === 'spring' ? 'bg-gradient-to-r from-green-600 to-green-700' : 'bg-gradient-to-r from-blue-600 to-blue-700'} text-white flex-shrink-0`}>
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                            <h3 className="section-title font-bold">{game.awayTeam} @ {game.homeTeam}</h3>
                            {game.gameType === 'spring' && <span className="px-2 py-0.5 bg-white/20 text-white text-xs font-semibold rounded">Spring Training</span>}
                            {game.gameType === 'postseason' && <span className="px-2 py-0.5 bg-yellow-400/30 text-white text-xs font-semibold rounded">Postseason</span>}
                        </div>
                        <button onClick={onClose} className="text-white hover:text-slate-200 text-2xl leading-none">&times;</button>
                    </div>
                    <div className="flex items-center gap-4 body-text text-blue-100">
                        <span>{game.date}</span>
                        <span>•</span>
                        <span>{game.startTime}</span>
                        <span>•</span>
                        <span className="font-mono text-2xl text-white font-bold">{game.score}</span>
                    </div>
                    <div className="body-text text-blue-100 mt-2">
                        📍 <button className="hover:underline hover:text-white" onClick={() => { if (window.__navigateTab) window.__navigateTab('venues'); if (onClose) onClose(); }}>{game.venue}</button>
                        {game.attendance > 0 && <> • 👥 {game.attendance.toLocaleString()} fans</>}
                        {game.gameLength && <> • ⏱️ {game.gameLength}</>}
                    </div>
                    {/* Weather and Temperature */}
                    {game.weather && (
                        <div className="body-text text-blue-100 mt-1">
                            <span>🌤️ {game.weather}</span>
                        </div>
                    )}
                    {/* Pitcher Decisions */}
                    {game.decisions && (game.decisions.winner || game.decisions.loser) && (
                        <div className="body-text text-blue-100 mt-1">
                            {game.decisions.winner && <span className="mr-3">W: {game.decisions.winner}</span>}
                            {game.decisions.loser && <span className="mr-3">L: {game.decisions.loser}</span>}
                            {game.decisions.save && <span>SV: {game.decisions.save}</span>}
                        </div>
                    )}
                </div>
                
                {/* Scrollable body */}
                <div className="overflow-y-auto flex-1 min-h-0">
                {/* Game Context Section */}
                <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
                    {/* Linescore */}
                    {game.linescore && (
                        <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
                            <h5 className="small-text font-bold mb-3 text-slate-700">📊 Line Score</h5>
                            <div className="overflow-x-auto">
                                <table className="w-full text-center small-text" style={{ tableLayout: 'fixed' }}>
                                    <thead className="bg-slate-50">
                                        <tr>
                                            <th className="py-2 text-left" style={{ width: '15%' }}>Team</th>
                                            {Array.from({ length: Math.max(game.linescore.away?.innings?.length || 9, game.linescore.home?.innings?.length || 9, 9) }, (_, i) => (
                                                <th key={`inning-${i}`} className="py-2">{i + 1}</th>
                                            ))}
                                            <th className="py-2 font-bold border-l-2">R</th>
                                            <th className="py-2 font-bold">H</th>
                                            <th className="py-2 font-bold">E</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="border-b">
                                            <td className="px-3 py-2 text-left font-semibold">{game.awayTeam}</td>
                                            {Array.from({ length: Math.max(game.linescore.away?.innings?.length || 9, game.linescore.home?.innings?.length || 9, 9) }, (_, i) => (
                                                <td key={`away-inning-${i}`} className="px-2 py-2">
                                                    {game.linescore.away?.innings?.[i] !== undefined ? game.linescore.away.innings[i] : '-'}
                                                </td>
                                            ))}
                                            <td className="px-3 py-2 font-bold border-l-2">{game.linescore.away?.runs || 0}</td>
                                            <td className="px-3 py-2 font-bold">{game.linescore.away?.hits || 0}</td>
                                            <td className="px-3 py-2 font-bold">{game.linescore.away?.errors || 0}</td>
                                        </tr>
                                        <tr>
                                            <td className="px-3 py-2 text-left font-semibold">{game.homeTeam}</td>
                                            {Array.from({ length: Math.max(game.linescore.away?.innings?.length || 9, game.linescore.home?.innings?.length || 9, 9) }, (_, i) => (
                                                <td key={`home-inning-${i}`} className="px-2 py-2">
                                                    {game.linescore.home?.innings?.[i] !== undefined ? game.linescore.home.innings[i] : '-'}
                                                </td>
                                            ))}
                                            <td className="px-3 py-2 font-bold border-l-2">{game.linescore.home?.runs || 0}</td>
                                            <td className="px-3 py-2 font-bold">{game.linescore.home?.hits || 0}</td>
                                            <td className="px-3 py-2 font-bold">{game.linescore.home?.errors || 0}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Umpires */}
                    {game.umpires && Object.values(game.umpires).some(u => u) && (
                        <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
                            <h5 className="small-text font-bold mb-3 text-slate-700">👨‍⚖️ Umpires</h5>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                                {['hp', '1b', '2b', '3b', 'lf', 'rf'].map(pos => game.umpires[pos] ? (
                                    <div key={pos} className="small-text">
                                        <span className="text-slate-500">{pos.toUpperCase()}:</span>{' '}
                                        <button className="font-medium text-blue-600 hover:underline" onClick={() => {
                                            window._pendingUmpireSearch = game.umpires[pos];
                                            if (window.__navigateTab) window.__navigateTab('trivia', 'umpires');
                                            if (onClose) onClose();
                                        }}>{game.umpires[pos]}</button>
                                    </div>
                                ) : null)}
                            </div>
                        </div>
                    )}

                    {/* Key Plays (Home Runs) */}
                    {game.keyPlays && game.keyPlays.length > 0 && (
                        <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
                            <h5 className="small-text font-bold mb-3 text-slate-700">⚾ Key Plays</h5>
                            <div className="space-y-2">
                                {game.keyPlays.map((play, idx) => (
                                    <div key={`keyplay-${play.inning}-${play.batter}-${idx}`} className="flex items-start gap-2 p-2 bg-orange-50 rounded border-l-4 border-orange-400">
                                        <span className="text-lg">
                                            {play.type === 'grand_slam' ? '💣' : '🏠'}
                                        </span>
                                        <div className="flex-1">
                                            <div className="body-text font-semibold">
                                                {play.batter} {play.type === 'grand_slam' ? 'Grand Slam' : 'Home Run'}
                                            </div>
                                            <div className="small-text text-slate-600">
                                                {play.inning} • off {play.pitcher}
                                                {play.rbi > 1 && ` (${play.rbi} RBI)`}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Milestones from this game */}
                    {(() => {
                        const gameMilestones = BASEBALL_DATA.milestones.filter(m => m.gameId === game.gameId);
                        if (gameMilestones.length === 0) return null;
                        return (
                            <div className="mt-4 bg-white rounded-lg p-4 shadow-sm">
                                <h5 className="small-text font-bold mb-3 text-slate-700">🏆 Milestones Achieved</h5>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {gameMilestones.map((milestone, idx) => (
                                        <div key={milestone.id || `${milestone.type}-${milestone.gameId}-${idx}`} className="bg-white rounded-lg p-3 shadow-sm border-l-4 border-purple-400">
                                            <div className="flex items-start gap-2">
                                                <span className="text-xl">
                                                    {milestone.type.includes('HR') ? '⚾' :
                                                     milestone.type.includes('K') || milestone.type.includes('Strikeout') ? '🔥' :
                                                     milestone.type.includes('Hit') ? '🎯' :
                                                     milestone.type.includes('RBI') ? '💪' :
                                                     milestone.type.includes('Walk-Off') ? '🎉' :
                                                     milestone.type.includes('Shutout') || milestone.type.includes('Complete') ? '🛡️' :
                                                     '⭐'}
                                                </span>
                                                <div className="flex-1">
                                                    <div className="body-text font-bold text-slate-900">{milestone.type}</div>
                                                    <div className="body-text text-slate-700 mt-1">{milestone.player}</div>
                                                    {milestone.detail && (
                                                        <div className="small-text text-slate-600 mt-1">{milestone.detail}</div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })()}

                    {/* Career Milestones from this game */}
                    {careerFirsts && careerFirsts.length > 0 && (
                        <div className="mt-4 bg-gradient-to-r from-amber-50 to-yellow-50 rounded-lg p-4 shadow-sm border border-amber-200">
                            <h5 className="small-text font-bold mb-3 text-amber-800">⭐ Career Milestones Witnessed</h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {careerFirsts.map((first, idx) => (
                                    <div key={`career-${first.milestone}-${first.player || idx}`} className="bg-white rounded-lg p-3 shadow-sm border-l-4 border-amber-400">
                                        <div className="flex items-start gap-2">
                                            <span className="text-xl">
                                                {first.milestone.includes('Home Run') ? '💣' :
                                                 first.milestone.includes('Hit') ? '🎯' :
                                                 first.milestone.includes('RBI') ? '💪' :
                                                 first.milestone.includes('Double') ? '2️⃣' :
                                                 first.milestone.includes('Triple') ? '3️⃣' :
                                                 first.milestone.includes('Walk') ? '🚶' :
                                                 first.milestone.includes('Stolen') ? '🏃' :
                                                 first.milestone.includes('Win') ? '🏆' :
                                                 first.milestone.includes('Save') ? '💾' :
                                                 first.milestone.includes('Strikeout') ? 'K' :
                                                 '⭐'}
                                            </span>
                                            <div className="flex-1">
                                                <div className="body-text font-bold text-amber-800">{first.milestone}</div>
                                                <div className="body-text text-slate-700 mt-1">{first.player_name}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
                
                {/* Tab Navigation */}
                <div className="border-b bg-slate-50 sticky top-0 z-10">
                    <div className="flex gap-1 px-6">
                        {['boxscore', 'lineups', 'substitutions', 'playbyplay', 'context'].map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-4 sm:px-6 py-3 body-text font-semibold transition-all whitespace-nowrap ${
                                    activeTab === tab
                                        ? 'bg-white text-blue-600 border-b-4 border-blue-600'
                                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                                }`}
                            >
                                {tab === 'boxscore' ? 'Box Score' :
                                 tab === 'lineups' ? 'Lineups' :
                                 tab === 'substitutions' ? 'Substitutions' :
                                 tab === 'playbyplay' ? 'Play-by-Play' :
                                 `Context${(careerFirsts?.length || 0) + (allTimePassings?.length || 0) + (badges?.length || 0) > 0 ? ' ✦' : ''}`}
                            </button>
                        ))}
                    </div>
                </div>
                
                {/* Tab Content */}
                <div>
                    {activeTab === 'boxscore' && <BoxScoreTab />}
                    {activeTab === 'lineups' && <LineupsTab />}
                    {activeTab === 'substitutions' && <SubstitutionsTab />}
                    {activeTab === 'playbyplay' && <PlayByPlayTab />}
                    {activeTab === 'context' && (
                        <div className="p-6 space-y-6">
                            {/* Game Superlatives */}
                            {(gameData.fastestPitch || gameData.hardestHit || gameData.mostKs) && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">Game Highlights</h4>
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                        {gameData.fastestPitch && (
                                            <div className="bg-red-50 rounded-lg p-3 border border-red-200">
                                                <div className="text-xs text-red-600 font-semibold">Fastest Pitch</div>
                                                <div className="text-lg font-bold text-red-700">{gameData.fastestPitch.speed} mph</div>
                                                <div className="text-xs text-slate-600">{gameData.fastestPitch.name}</div>
                                            </div>
                                        )}
                                        {gameData.hardestHit && (
                                            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                                                <div className="text-xs text-blue-600 font-semibold">Hardest Hit</div>
                                                <div className="text-lg font-bold text-blue-700">{gameData.hardestHit.velo} mph</div>
                                                <div className="text-xs text-slate-600">{gameData.hardestHit.name}{gameData.hardestHit.dist ? ` (${gameData.hardestHit.dist} ft)` : ''}</div>
                                            </div>
                                        )}
                                        {gameData.mostKs && gameData.mostKs.so >= 5 && (
                                            <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
                                                <div className="text-xs text-orange-600 font-semibold">Most Strikeouts</div>
                                                <div className="text-lg font-bold text-orange-700">{gameData.mostKs.so} K</div>
                                                <div className="text-xs text-slate-600">{gameData.mostKs.name}</div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {game.absChallenges?.reviews?.length > 0 && (() => {
                                const reviews = game.absChallenges.reviews;
                                // Derive team summaries from challengeTeam field
                                const awayChallenges = reviews.filter(r => r.challengeTeam === 'away');
                                const homeChallenges = reviews.filter(r => r.challengeTeam === 'home');
                                const awayOvt = awayChallenges.filter(r => r.overturned).length;
                                const homeOvt = homeChallenges.filter(r => r.overturned).length;
                                const awayFailed = awayChallenges.length - awayOvt;
                                const homeFailed = homeChallenges.length - homeOvt;
                                // Remaining: start with 2, lose 1 per failed challenge
                                const awayLeft = Math.max(0, 2 - awayFailed);
                                const homeLeft = Math.max(0, 2 - homeFailed);
                                return (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">⚖️ ABS Challenges</h4>
                                    <div className="grid grid-cols-2 gap-3 mb-3">
                                        <div className="bg-slate-50 rounded-lg p-3 text-sm">
                                            <div className="font-semibold mb-1">{game.awayTeam}</div>
                                            <div className="flex gap-3">
                                                <span className="text-green-600">✓ {awayOvt}</span>
                                                <span className="text-red-600">✗ {awayFailed}</span>
                                                <span className="text-slate-500">{awayLeft} left</span>
                                            </div>
                                        </div>
                                        <div className="bg-slate-50 rounded-lg p-3 text-sm">
                                            <div className="font-semibold mb-1">{game.homeTeam}</div>
                                            <div className="flex gap-3">
                                                <span className="text-green-600">✓ {homeOvt}</span>
                                                <span className="text-red-600">✗ {homeFailed}</span>
                                                <span className="text-slate-500">{homeLeft} left</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        {reviews.sort((a, b) => a.inning - b.inning || (a.half === 'top' ? 0 : 1) - (b.half === 'top' ? 0 : 1)).map((r, i) => (
                                            <div key={`abs-${i}`} className={`text-sm p-3 rounded-lg ${r.overturned ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                                                <div className="flex items-center justify-between">
                                                    <span className={`font-bold ${r.overturned ? 'text-green-700' : 'text-red-700'}`}>
                                                        {r.overturned ? '✓ Overturned' : '✗ Upheld'}
                                                    </span>
                                                    <span className="text-xs text-slate-500">{r.half === 'top' ? 'Top' : 'Bot'} {r.inning} • {r.count} count</span>
                                                </div>
                                                <div className="mt-1">
                                                    <span className="font-medium">{r.challengePlayer || r.batter}</span>
                                                    {' challenged call'}
                                                    {r.pitchType && <span className="text-slate-500"> ({r.pitchType})</span>}
                                                    {r.edgeDistance != null && <span className="text-xs text-slate-400 ml-2">edge: {r.edgeDistance.toFixed(3)}</span>}
                                                </div>
                                                <div className="text-xs text-slate-500 mt-0.5">{r.batter} batting vs {r.pitcher}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                );
                            })()}

                            {badges && badges.length > 0 && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">🏅 Badges Earned</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {badges.map((b, i) => (
                                            <span key={`badge-${i}`} className="px-3 py-1.5 bg-blue-50 text-blue-800 rounded-lg text-sm font-medium border border-blue-200" title={b.title}>
                                                {b.text}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {careerFirsts && careerFirsts.length > 0 && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">⭐ Career Milestones</h4>
                                    <div className="space-y-2">
                                        {careerFirsts.map((first, i) => (
                                            <div key={`first-${i}`} className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                                                <span className="text-xl">⭐</span>
                                                <div>
                                                    <div className="font-semibold body-text">
                                                        <PlayerLink playerId={first.player_id} name={first.player_name} /> — {first.milestone}
                                                    </div>
                                                    {first.opponent && <div className="small-text text-slate-600">vs {first.opponent}</div>}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {allTimePassings && allTimePassings.length > 0 && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">📜 All-Time List Passings</h4>
                                    <div className="space-y-2">
                                        {allTimePassings.map((passing, i) => (
                                            <div key={`passing-${i}`} className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                                                <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-white text-sm font-bold flex-shrink-0 ${passing.new_rank <= 10 ? 'bg-gradient-to-br from-yellow-400 to-amber-500' : 'bg-gradient-to-br from-purple-500 to-violet-600'}`}>
                                                    #{passing.new_rank}
                                                </span>
                                                <div>
                                                    <div className="font-semibold body-text">
                                                        <PlayerLink playerId={passing.player_id} name={passing.player_name} /> — #{passing.new_rank} all-time in {passing.stat_name}
                                                    </div>
                                                    <div className="small-text text-slate-600">
                                                        {passing.new_value} career {passing.stat_name.toLowerCase()}
                                                        {passing.passed_names && ` • Passed ${passing.passed_names}`}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
                </div>{/* End scrollable body */}

                {/* Footer */}
                <div className="p-3 border-t bg-slate-50 flex justify-between items-center flex-shrink-0">
                    <div className="flex items-center gap-2">
                        {onPrev && <button onClick={onPrev} className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 rounded text-sm font-medium" title="Previous game">← Prev</button>}
                        {gameIndex != null && totalGames && <span className="text-xs text-slate-500">Game {gameIndex} of {totalGames}</span>}
                        {onNext && <button onClick={onNext} className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 rounded text-sm font-medium" title="Next game">Next →</button>}
                    </div>
                    <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                    <button onClick={onClose} className="px-5 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium">
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

const PlayerTimeline = ({ playerId, playerName, playerGames, onGameClick, careerMilestones, allTimePassings, gameMilestones, debuts, finalGames }) => {
    const [showGameLog, setShowGameLog] = useState(false);
    const [sortKey, setSortKey] = useState('dateSort');
    const [sortDir, setSortDir] = useState('desc');
    const [opponentFilter, setOpponentFilter] = useState(null);
    const [showSeasons, setShowSeasons] = useState(false);

    // Get all games for this player
    const gamesForPlayer = useMemo(() => {
        return playerGames.filter(g => g.playerId === playerId).sort((a, b) => b.dateSort.localeCompare(a.dateSort));
    }, [playerId, playerGames]);

    const timelineData = useMemo(() => {
        if (gamesForPlayer.length === 0) return [];
        const byYearType = {};
        gamesForPlayer.forEach(game => {
            const year = game.dateSort.substring(0, 4);
            const isSpring = game.gameType === 'spring' || game.gameType === 'exhibition';
            const key = isSpring ? `${year}_spring` : year;
            if (!byYearType[key]) byYearType[key] = { year, isSpring, games: [] };
            byYearType[key].games.push(game);
        });
        return Object.values(byYearType).map(({ year, isSpring, games }) => {
            const aggregated = aggregateHitterStats(games)[0] || {};
            return { year, isSpring, ...aggregated };
        }).sort((a, b) => a.year !== b.year ? a.year - b.year : (a.isSpring ? -1 : 0) - (b.isSpring ? -1 : 0));
    }, [gamesForPlayer]);

    // Totals for stat cards
    const totals = useMemo(() => {
        const regGames = gamesForPlayer.filter(g => g.gameType === 'regular' || (!g.gameType));
        const agg = aggregateHitterStats(regGames)[0] || {};
        const multiHitGames = regGames.filter(g => g.h >= 3).length;
        const hrGames = regGames.filter(g => (g.hr || 0) >= 1).length;
        const multiHrGames = regGames.filter(g => (g.hr || 0) >= 2).length;
        return { ...agg, multiHitGames, hrGames, multiHrGames };
    }, [gamesForPlayer]);

    // Notable games: multi-HR, 3+ hits, HR+multi-hit, 3+ RBI, 2+ SB, 4+ R
    const notableGames = useMemo(() => {
        return gamesForPlayer.filter(g => {
            const isSpring = g.gameType === 'spring' || g.gameType === 'exhibition';
            if (isSpring) return false;
            const hr = g.hr || 0, h = g.h || 0, rbi = g.rbi || 0, sb = g.sb || 0, r = g.r || 0;
            return hr >= 2 || h >= 3 || (hr >= 1 && h >= 2) || (hr >= 1 && rbi >= 3) || rbi >= 4 || sb >= 2 || r >= 4 || g.careerHighs?.length;
        }).map(g => {
            const hr = g.hr || 0, h = g.h || 0, rbi = g.rbi || 0, sb = g.sb || 0, r = g.r || 0, bb = g.bb || 0;
            // Build compact batting line
            const parts = [`${h}-${g.ab}`];
            if (hr > 0) parts.push(`${hr} HR`);
            if (rbi > 0) parts.push(`${rbi} RBI`);
            if (r > 0) parts.push(`${r} R`);
            if (bb > 0) parts.push(`${bb} BB`);
            if (sb > 0) parts.push(`${sb} SB`);
            const line = parts.join(', ');
            // Highlight tag for the best thing about this game
            let highlight = null;
            if (hr >= 3) highlight = { label: `${hr}-HR game`, color: 'bg-red-200 text-red-800' };
            else if (hr >= 2) highlight = { label: 'Multi-HR', color: 'bg-red-100 text-red-700' };
            else if (h >= 5) highlight = { label: `${h}-hit game`, color: 'bg-emerald-100 text-emerald-700' };
            else if (h >= 4) highlight = { label: `${h}-hit game`, color: 'bg-emerald-100 text-emerald-700' };
            else if (h >= 3 && hr >= 1) highlight = { label: `${h}-hit, HR`, color: 'bg-orange-100 text-orange-700' };
            else if (h >= 3) highlight = { label: `${h}-hit game`, color: 'bg-green-100 text-green-700' };
            else if (rbi >= 5) highlight = { label: `${rbi} RBI`, color: 'bg-blue-100 text-blue-700' };
            else if (rbi >= 4) highlight = { label: `${rbi} RBI`, color: 'bg-blue-100 text-blue-700' };
            else if (hr >= 1 && rbi >= 3) highlight = { label: `HR, ${rbi} RBI`, color: 'bg-orange-100 text-orange-700' };
            else if (hr >= 1 && h >= 2) highlight = { label: `${h}-hit, HR`, color: 'bg-orange-100 text-orange-700' };
            else if (g.careerHighs?.length) highlight = { label: `Career-high ${g.careerHighs.join(', ')}`, color: 'bg-purple-100 text-purple-700' };
            else if (r >= 4) highlight = { label: `${r} runs`, color: 'bg-sky-100 text-sky-700' };
            else if (sb >= 2) highlight = { label: `${sb} SB`, color: 'bg-violet-100 text-violet-700' };
            else if (rbi >= 4) highlight = { label: `${rbi} RBI`, color: 'bg-blue-100 text-blue-700' };
            // Score for sorting (best games first)
            const score = hr * 4 + h * 1.5 + rbi * 2 + r + sb * 2 + (g.careerHighs ? 5 : 0);
            return { ...g, line, highlight, score };
        }).sort((a, b) => b.score - a.score);
    }, [gamesForPlayer]);

    // Combined milestones list
    const allMilestones = useMemo(() => {
        const toSort = (d) => { if (!d) return ''; const p = d.split('/'); return p.length === 3 ? `${p[2]}-${p[0].padStart(2,'0')}-${p[1].padStart(2,'0')}` : d; };
        const items = [];
        (debuts || []).forEach(d => items.push({ sort: toSort(d.date), badgeClass: 'bg-green-100 text-green-700', badgeText: 'DEBUT', text: `MLB Debut (${d.team})`, sub: `vs ${d.opponent || ''}`, date: d.date, gameId: d.gameId }));
        (finalGames || []).forEach(f => items.push({ sort: toSort(f.date), badgeClass: 'bg-slate-200 text-slate-700', badgeText: 'FINAL', text: `Final MLB Game (${f.team})`, date: f.date, gameId: f.gameId }));
        (gameMilestones || []).forEach(m => items.push({ sort: m._dateSort || m.date || '', badgeClass: 'bg-orange-100 text-orange-700', badgeText: m.type, text: m.detail, sub: `vs ${m.opponent}`, date: m.date, gameId: m.gameId }));
        (careerMilestones || []).forEach(m => items.push({ sort: m.date || '', badgeClass: m.category === 'first' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700', badgeText: m.category === 'first' ? 'FIRST' : 'MILESTONE', text: m.milestone, date: m.date_display || m.date, gameId: m.game_id }));
        (allTimePassings || []).forEach(p => {
            const passed = (p.passed_players || []).filter(pp => !pp.tied).map(pp => pp.name);
            const tied = (p.passed_players || []).filter(pp => pp.tied).map(pp => pp.name);
            const parts = [];
            if (passed.length) parts.push('passed ' + passed.join(', '));
            if (tied.length) parts.push('tied ' + tied.join(', '));
            items.push({ sort: p.date || '', badgeClass: 'bg-purple-100 text-purple-700', badgeText: `#${p.new_rank}`, text: parts.join(' and ') || p.milestone, sub: p.stat_name, date: p.date_display || p.date, gameId: p.game_id });
        });
        return items.sort((a, b) => (b.sort).localeCompare(a.sort));
    }, [gameMilestones, careerMilestones, allTimePassings, debuts, finalGames]);

    // Sorted game log
    const sortedGameLog = useMemo(() => {
        const filtered = opponentFilter ? gamesForPlayer.filter(g => g.opponent === opponentFilter) : gamesForPlayer;
        return [...filtered].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal || '').localeCompare(String(bVal || ''));
            return sortDir === 'asc' ? result : -result;
        });
    }, [gamesForPlayer, sortKey, sortDir, opponentFilter]);

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    if (gamesForPlayer.length === 0) {
        return (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h3 className="subsection-title font-bold mb-4">📊 Player Stats</h3>
                <p className="body-text text-slate-500 text-center py-8">No games found for this player</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Stat Cards */}
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
                {[
                    { label: 'G', value: totals.games, bold: true },
                    { label: 'AVG', value: totals.avg, bold: true },
                    { label: 'H', value: totals.h },
                    { label: 'HR', value: totals.hr, color: totals.hr > 0 ? 'text-orange-600' : '' },
                    { label: 'RBI', value: totals.rbi },
                    { label: 'SB', value: totals.sb },
                    { label: 'OPS', value: totals.ops, bold: true, color: parseFloat(totals.ops) >= 0.800 ? 'text-purple-600' : '' },
                    { label: 'BB', value: totals.bb },
                ].map(s => (
                    <div key={s.label} className="bg-slate-50 rounded-lg px-3 py-2 text-center">
                        <div className={`text-lg font-bold ${s.color || 'text-slate-800'}`}>{s.value}</div>
                        <div className="text-[10px] uppercase font-semibold text-slate-400">{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Notable Games */}
            {notableGames.length > 0 && (
                <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-2">Notable Games ({notableGames.length})</h4>
                    <div className="space-y-0.5">
                        {notableGames.map((g, i) => (
                            <button key={i} onClick={() => onGameClick && onGameClick(g.gameId)} className="w-full flex items-center gap-2 text-sm px-3 py-1.5 rounded hover:bg-slate-50 text-left transition-colors">
                                {g.highlight && <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 ${g.highlight.color}`}>{g.highlight.label}</span>}
                                <span className="text-slate-600 text-xs">{g.line}</span>
                                <span className="text-slate-400 text-xs ml-auto shrink-0">vs {g.opponent} · {g.date}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Milestones */}
            {allMilestones.length > 0 && (
                <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-2">Milestones ({allMilestones.length})</h4>
                    <div className="space-y-1">
                        {allMilestones.map((m, i) => (
                            <button key={i} onClick={() => onGameClick && onGameClick(m.gameId)} className="w-full flex items-center gap-2 text-sm px-3 py-1.5 rounded hover:bg-slate-50 text-left transition-colors">
                                <span className="text-slate-400 text-xs w-20 shrink-0">{m.date}</span>
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 ${m.badgeClass}`}>{m.badgeText}</span>
                                <span className="font-medium truncate">{m.text}</span>
                                {m.sub && <span className="text-slate-400 text-xs ml-auto shrink-0">{m.sub}</span>}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Season Breakdown (collapsible) */}
            {timelineData.length > 0 && (
                <div>
                    <button onClick={() => setShowSeasons(!showSeasons)} className="flex items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-900">
                        <span className={`transition-transform ${showSeasons ? 'rotate-90' : ''}`}>&#9656;</span>
                        Season Breakdown ({timelineData.filter(s => !s.isSpring).length} season{timelineData.filter(s => !s.isSpring).length !== 1 ? 's' : ''})
                    </button>
                    {showSeasons && (
                        <div className="mt-2 overflow-x-auto border rounded-lg">
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 border-b">
                                    <tr>
                                        {['Year','Team','G','AB','H','R','RBI','HR','2B','3B','SB','BB','SO','AVG','OPS'].map(col => (
                                            <th key={col} className="px-2 py-2 text-center text-xs font-semibold text-slate-500">{col}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {timelineData.map((s) => (
                                        <tr key={`${s.year}${s.isSpring ? '-st' : ''}`} className={s.isSpring ? 'bg-green-50' : 'hover:bg-blue-50'}>
                                            <td className="px-2 py-2 text-center font-bold text-blue-600 whitespace-nowrap">
                                                {s.year}{s.isSpring ? <span className="ml-1 text-[10px] text-green-600 font-normal">ST</span> : ''}
                                            </td>
                                            <td className="px-2 py-2 text-center text-xs">{s.team || '-'}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.games}</td>
                                            <td className="px-2 py-2 text-center">{s.ab}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.h}</td>
                                            <td className="px-2 py-2 text-center">{s.r}</td>
                                            <td className="px-2 py-2 text-center">{s.rbi}</td>
                                            <td className={`px-2 py-2 text-center ${s.hr > 0 ? 'font-bold text-orange-600' : ''}`}>{s.hr}</td>
                                            <td className="px-2 py-2 text-center">{s.doubles || 0}</td>
                                            <td className="px-2 py-2 text-center">{s.triples || 0}</td>
                                            <td className="px-2 py-2 text-center">{s.sb || 0}</td>
                                            <td className="px-2 py-2 text-center">{s.bb}</td>
                                            <td className="px-2 py-2 text-center">{s.so}</td>
                                            <td className="px-2 py-2 text-center font-bold">{s.avg}</td>
                                            <td className="px-2 py-2 text-center font-bold text-purple-600">{s.ops}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* Full Game Log (collapsible) */}
            <div>
                <button onClick={() => setShowGameLog(!showGameLog)} className="flex items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-900">
                    <span className={`transition-transform ${showGameLog ? 'rotate-90' : ''}`}>&#9656;</span>
                    Full Game Log ({gamesForPlayer.length} game{gamesForPlayer.length !== 1 ? 's' : ''})
                </button>
                {showGameLog && (
                    <div className="mt-2">
                        <div className="text-sm text-slate-500 mb-2 flex items-center gap-2">
                            {opponentFilter && (
                                <button onClick={() => setOpponentFilter(null)} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium hover:bg-blue-200">
                                    vs {opponentFilter} <span className="ml-0.5">&times;</span>
                                </button>
                            )}
                        </div>
                        <div className="overflow-x-auto border rounded-lg" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 sticky top-0">
                                    <tr>
                                        {[
                                            { key: 'dateSort', label: 'Date' },
                                            { key: 'opponent', label: 'vs' },
                                            { key: 'ab', label: 'AB' },
                                            { key: 'h', label: 'H' },
                                            { key: 'r', label: 'R' },
                                            { key: 'rbi', label: 'RBI' },
                                            { key: 'hr', label: 'HR' },
                                            { key: 'bb', label: 'BB' },
                                            { key: 'so', label: 'SO' },
                                            { key: 'sb', label: 'SB' },
                                        ].map(col => (
                                            <th key={col.key} onClick={() => handleSort(col.key)}
                                                className="px-3 py-2 text-left font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 whitespace-nowrap text-xs">
                                                {col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {sortedGameLog.map((game) => {
                                        const isMultiHit = game.h >= 2;
                                        const isHR = game.hr > 0;
                                        return (
                                            <tr key={`${game.date}-${game.opponent}-${game.team}`} className={`hover:bg-blue-50 cursor-pointer ${isHR ? 'bg-orange-50' : isMultiHit ? 'bg-green-50' : ''}`} onClick={() => onGameClick && onGameClick(game.gameId)}>
                                                <td className="px-3 py-1.5 whitespace-nowrap font-medium text-xs">
                                                    <div className="flex items-center gap-1">
                                                        {game.date}
                                                        {game.careerHighs?.length > 0 && <span className="px-1 py-0.5 rounded text-[9px] font-semibold bg-purple-100 text-purple-700" title={`Career-high ${game.careerHighs.join(', ')}`}>CH</span>}
                                                    </div>
                                                </td>
                                                <td className="px-3 py-1.5"><button className="text-blue-600 hover:underline text-xs" onClick={(e) => { e.stopPropagation(); setOpponentFilter(opponentFilter === game.opponent ? null : game.opponent); }}>{game.opponent}</button></td>
                                                <td className="px-3 py-1.5">{game.ab}</td>
                                                <td className={`px-3 py-1.5 ${isMultiHit ? 'font-bold text-green-600' : ''}`}>{game.h}</td>
                                                <td className="px-3 py-1.5">{game.r}</td>
                                                <td className="px-3 py-1.5">{game.rbi}</td>
                                                <td className={`px-3 py-1.5 ${isHR ? 'font-bold text-orange-600' : ''}`}>{game.hr || 0}</td>
                                                <td className="px-3 py-1.5">{game.bb}</td>
                                                <td className="px-3 py-1.5">{game.so}</td>
                                                <td className="px-3 py-1.5">{game.sb || 0}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const PitcherTimeline = ({ playerId, playerName, pitcherGames, onGameClick, careerMilestones, allTimePassings, gameMilestones, debuts, finalGames }) => {
    const [showGameLog, setShowGameLog] = useState(false);
    const [sortKey, setSortKey] = useState('dateSort');
    const [sortDir, setSortDir] = useState('desc');
    const [opponentFilter, setOpponentFilter] = useState(null);
    const [showSeasons, setShowSeasons] = useState(false);

    // Get all games for this pitcher with derived fields
    const gamesForPitcher = useMemo(() => {
        return pitcherGames.filter(g => g.playerId === playerId).map(g => ({
            ...g,
            ip: `${Math.floor(g.outs / 3)}.${g.outs % 3}`,
            decision: g.wins ? 'W' : g.losses ? 'L' : g.saves ? 'S' : '',
        })).sort((a, b) => b.dateSort.localeCompare(a.dateSort));
    }, [playerId, pitcherGames]);

    const timelineData = useMemo(() => {
        if (gamesForPitcher.length === 0) return [];
        const byYearType = {};
        gamesForPitcher.forEach(game => {
            const year = game.dateSort.substring(0, 4);
            const isSpring = game.gameType === 'spring' || game.gameType === 'exhibition';
            const key = isSpring ? `${year}_spring` : year;
            if (!byYearType[key]) byYearType[key] = { year, isSpring, games: [] };
            byYearType[key].games.push(game);
        });
        return Object.values(byYearType).map(({ year, isSpring, games }) => {
            const aggregated = aggregatePitcherStats(games)[0] || {};
            return { year, isSpring, ...aggregated };
        }).sort((a, b) => a.year !== b.year ? a.year - b.year : (a.isSpring ? -1 : 0) - (b.isSpring ? -1 : 0));
    }, [gamesForPitcher]);

    // Totals for stat cards (regular season only, matching the table default)
    const totals = useMemo(() => {
        const regGames = gamesForPitcher.filter(g => g.gameType === 'regular' || (!g.gameType));
        const agg = aggregatePitcherStats(regGames)[0] || {};
        const totalOuts = regGames.reduce((s, g) => s + (g.outs || 0), 0);
        const innings = totalOuts / 3;
        const totalER = regGames.reduce((s, g) => s + (g.er || 0), 0);
        const totalH = regGames.reduce((s, g) => s + (g.h || 0), 0);
        const totalBB = regGames.reduce((s, g) => s + (g.bb || 0), 0);
        const era = innings > 0 ? ((totalER * 9) / innings).toFixed(2) : '-';
        const whip = innings > 0 ? ((totalH + totalBB) / innings).toFixed(3) : '-';
        const ip = `${Math.floor(innings)}.${totalOuts % 3}`;
        return { ...agg, era, whip, ip };
    }, [gamesForPitcher]);

    // Notable games: 6+ K, QS, W, SV, low-hit games
    const notableGames = useMemo(() => {
        return gamesForPitcher.filter(g => {
            const isSpring = g.gameType === 'spring' || g.gameType === 'exhibition';
            const ipNum = parseFloat(g.ip);
            return !isSpring && (g.so >= 6 || (ipNum >= 6 && g.er <= 3) || g.decision === 'W' || g.decision === 'S' || (ipNum >= 5 && g.h <= 2));
        }).map(g => {
            const tags = [];
            const ipNum = parseFloat(g.ip);
            if (g.so >= 10) tags.push({ label: `${g.so} K`, color: 'bg-red-100 text-red-700' });
            else if (g.so >= 6) tags.push({ label: `${g.so} K`, color: 'bg-orange-100 text-orange-700' });
            if (ipNum >= 6 && g.er <= 3) tags.push({ label: 'QS', color: 'bg-blue-100 text-blue-700' });
            if (g.decision === 'W') tags.push({ label: 'W', color: 'bg-green-100 text-green-700' });
            if (g.decision === 'S') tags.push({ label: 'SV', color: 'bg-sky-100 text-sky-700' });
            if (ipNum >= 5 && g.h <= 2) tags.push({ label: `${g.h}H`, color: 'bg-violet-100 text-violet-700' });
            return { ...g, tags };
        });
    }, [gamesForPitcher]);

    // Combined milestones list
    const allMilestones = useMemo(() => {
        const toSort = (d) => { if (!d) return ''; const p = d.split('/'); return p.length === 3 ? `${p[2]}-${p[0].padStart(2,'0')}-${p[1].padStart(2,'0')}` : d; };
        const items = [];
        (debuts || []).forEach(d => items.push({ sort: toSort(d.date), badgeClass: 'bg-green-100 text-green-700', badgeText: 'DEBUT', text: `MLB Debut (${d.team})`, sub: `vs ${d.opponent || ''}`, date: d.date, gameId: d.gameId }));
        (finalGames || []).forEach(f => items.push({ sort: toSort(f.date), badgeClass: 'bg-slate-200 text-slate-700', badgeText: 'FINAL', text: `Final MLB Game (${f.team})`, date: f.date, gameId: f.gameId }));
        (gameMilestones || []).forEach(m => items.push({ sort: m._dateSort || m.date || '', badgeClass: 'bg-orange-100 text-orange-700', badgeText: m.type, text: m.detail, sub: `vs ${m.opponent}`, date: m.date, gameId: m.gameId }));
        (careerMilestones || []).forEach(m => items.push({ sort: m.date || '', badgeClass: m.category === 'first' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700', badgeText: m.category === 'first' ? 'FIRST' : 'MILESTONE', text: m.milestone, date: m.date_display || m.date, gameId: m.game_id }));
        (allTimePassings || []).forEach(p => {
            const passed = (p.passed_players || []).filter(pp => !pp.tied).map(pp => pp.name);
            const tied = (p.passed_players || []).filter(pp => pp.tied).map(pp => pp.name);
            const parts = [];
            if (passed.length) parts.push('passed ' + passed.join(', '));
            if (tied.length) parts.push('tied ' + tied.join(', '));
            items.push({ sort: p.date || '', badgeClass: 'bg-purple-100 text-purple-700', badgeText: `#${p.new_rank}`, text: parts.join(' and ') || p.milestone, sub: p.stat_name, date: p.date_display || p.date, gameId: p.game_id });
        });
        return items.sort((a, b) => (b.sort).localeCompare(a.sort));
    }, [gameMilestones, careerMilestones, allTimePassings, debuts, finalGames]);

    // Sorted game log
    const sortedGameLog = useMemo(() => {
        const filtered = opponentFilter ? gamesForPitcher.filter(g => g.opponent === opponentFilter) : gamesForPitcher;
        return [...filtered].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal || '').localeCompare(String(bVal || ''));
            return sortDir === 'asc' ? result : -result;
        });
    }, [gamesForPitcher, sortKey, sortDir, opponentFilter]);

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    if (gamesForPitcher.length === 0) {
        return (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h3 className="subsection-title font-bold mb-4">📊 Pitcher Stats</h3>
                <p className="body-text text-slate-500 text-center py-8">No games found for this pitcher</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Stat Cards */}
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
                {[
                    { label: 'G', value: totals.games, bold: true },
                    { label: 'W-L', value: `${totals.wins || 0}-${totals.losses || 0}`, color: (totals.wins || 0) > (totals.losses || 0) ? 'text-green-600' : '' },
                    { label: 'ERA', value: totals.era, bold: true, color: totals.era !== '-' && parseFloat(totals.era) <= 3.00 ? 'text-purple-600' : '' },
                    { label: 'IP', value: totals.ip },
                    { label: 'SO', value: totals.so, bold: true },
                    { label: 'WHIP', value: totals.whip },
                    { label: 'SV', value: totals.saves || 0 },
                    { label: 'BB', value: totals.bb },
                ].map(s => (
                    <div key={s.label} className="bg-slate-50 rounded-lg px-3 py-2 text-center">
                        <div className={`text-lg font-bold ${s.color || 'text-slate-800'}`}>{s.value}</div>
                        <div className="text-[10px] uppercase font-semibold text-slate-400">{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Notable Games */}
            {notableGames.length > 0 && (
                <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-2">Notable Games ({notableGames.length})</h4>
                    <div className="space-y-1">
                        {notableGames.map((g, i) => (
                            <button key={i} onClick={() => onGameClick && onGameClick(g.gameId)} className="w-full flex items-center gap-2 text-sm px-3 py-1.5 rounded hover:bg-slate-50 text-left transition-colors">
                                <span className="text-slate-400 text-xs w-20 shrink-0">{g.date}</span>
                                <span className="text-slate-500 w-8 shrink-0 text-xs">vs</span>
                                <span className="font-medium w-12 shrink-0">{g.opponent}</span>
                                <span className="flex gap-1 flex-wrap">
                                    {g.tags.map((t, j) => (
                                        <span key={j} className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${t.color}`}>{t.label}</span>
                                    ))}
                                </span>
                                <span className="text-slate-400 text-xs ml-auto">{g.ip} IP, {g.er} ER</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Milestones */}
            {allMilestones.length > 0 && (
                <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-2">Milestones ({allMilestones.length})</h4>
                    <div className="space-y-1">
                        {allMilestones.map((m, i) => (
                            <button key={i} onClick={() => onGameClick && onGameClick(m.gameId)} className="w-full flex items-center gap-2 text-sm px-3 py-1.5 rounded hover:bg-slate-50 text-left transition-colors">
                                <span className="text-slate-400 text-xs w-20 shrink-0">{m.date}</span>
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 ${m.badgeClass}`}>{m.badgeText}</span>
                                <span className="font-medium truncate">{m.text}</span>
                                {m.sub && <span className="text-slate-400 text-xs ml-auto shrink-0">{m.sub}</span>}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Season Breakdown (collapsible) */}
            {timelineData.length > 0 && (
                <div>
                    <button onClick={() => setShowSeasons(!showSeasons)} className="flex items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-900">
                        <span className={`transition-transform ${showSeasons ? 'rotate-90' : ''}`}>&#9656;</span>
                        Season Breakdown ({timelineData.filter(s => !s.isSpring).length} season{timelineData.filter(s => !s.isSpring).length !== 1 ? 's' : ''})
                    </button>
                    {showSeasons && (
                        <div className="mt-2 overflow-x-auto border rounded-lg">
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 border-b">
                                    <tr>
                                        {['Year','Team','G','GS','W','L','SV','IP','H','ER','BB','SO','ERA','WHIP'].map(col => (
                                            <th key={col} className="px-2 py-2 text-center text-xs font-semibold text-slate-500">{col}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {timelineData.map((s) => (
                                        <tr key={`${s.year}${s.isSpring ? '-st' : ''}`} className={s.isSpring ? 'bg-green-50' : 'hover:bg-purple-50'}>
                                            <td className="px-2 py-2 text-center font-bold text-purple-600 whitespace-nowrap">
                                                {s.year}{s.isSpring ? <span className="ml-1 text-[10px] text-green-600 font-normal">ST</span> : ''}
                                            </td>
                                            <td className="px-2 py-2 text-center text-xs">{s.team || '-'}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.games}</td>
                                            <td className="px-2 py-2 text-center">{s.gameStarts || 0}</td>
                                            <td className="px-2 py-2 text-center font-bold text-green-600">{s.wins}</td>
                                            <td className="px-2 py-2 text-center text-red-600">{s.losses}</td>
                                            <td className="px-2 py-2 text-center">{s.saves || 0}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.ip}</td>
                                            <td className="px-2 py-2 text-center">{s.h}</td>
                                            <td className="px-2 py-2 text-center">{s.er}</td>
                                            <td className="px-2 py-2 text-center">{s.bb}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.so}</td>
                                            <td className="px-2 py-2 text-center font-bold text-purple-700">{s.era}</td>
                                            <td className="px-2 py-2 text-center font-bold">{s.whip}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* Full Game Log (collapsible) */}
            <div>
                <button onClick={() => setShowGameLog(!showGameLog)} className="flex items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-900">
                    <span className={`transition-transform ${showGameLog ? 'rotate-90' : ''}`}>&#9656;</span>
                    Full Game Log ({gamesForPitcher.length} game{gamesForPitcher.length !== 1 ? 's' : ''})
                </button>
                {showGameLog && (
                    <div className="mt-2">
                        <div className="text-sm text-slate-500 mb-2 flex items-center gap-2">
                            {opponentFilter && (
                                <button onClick={() => setOpponentFilter(null)} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium hover:bg-blue-200">
                                    vs {opponentFilter} <span className="ml-0.5">&times;</span>
                                </button>
                            )}
                        </div>
                        <div className="overflow-x-auto border rounded-lg" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 sticky top-0">
                                    <tr>
                                        {[
                                            { key: 'dateSort', label: 'Date' },
                                            { key: 'opponent', label: 'vs' },
                                            { key: 'ip', label: 'IP' },
                                            { key: 'h', label: 'H' },
                                            { key: 'er', label: 'ER' },
                                            { key: 'bb', label: 'BB' },
                                            { key: 'so', label: 'SO' },
                                            { key: 'decision', label: 'Dec' },
                                        ].map(col => (
                                            <th key={col.key} onClick={() => handleSort(col.key)}
                                                className="px-3 py-2 text-left font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 whitespace-nowrap text-xs">
                                                {col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {sortedGameLog.map((game) => {
                                        const isWin = game.decision === 'W';
                                        const isQS = parseFloat(game.ip) >= 6 && game.er <= 3;
                                        return (
                                            <tr key={`${game.date}-${game.opponent}-${game.team}`} className={`hover:bg-blue-50 cursor-pointer ${isWin ? 'bg-green-50' : isQS ? 'bg-blue-50' : ''}`} onClick={() => onGameClick && onGameClick(game.gameId)}>
                                                <td className="px-3 py-1.5 whitespace-nowrap font-medium text-xs">
                                                    <div className="flex items-center gap-1">
                                                        {game.date}
                                                        {game.careerHighs?.length > 0 && <span className="px-1 py-0.5 rounded text-[9px] font-semibold bg-purple-100 text-purple-700" title={`Career-high ${game.careerHighs.join(', ')}`}>CH</span>}
                                                    </div>
                                                </td>
                                                <td className="px-3 py-1.5"><button className="text-blue-600 hover:underline text-xs" onClick={(e) => { e.stopPropagation(); setOpponentFilter(opponentFilter === game.opponent ? null : game.opponent); }}>{game.opponent}</button></td>
                                                <td className="px-3 py-1.5 font-medium">{game.ip}</td>
                                                <td className="px-3 py-1.5">{game.h}</td>
                                                <td className="px-3 py-1.5">{game.er}</td>
                                                <td className="px-3 py-1.5">{game.bb}</td>
                                                <td className={`px-3 py-1.5 ${game.so >= 8 ? 'font-bold text-orange-600' : ''}`}>{game.so}</td>
                                                <td className={`px-3 py-1.5 font-bold ${isWin ? 'text-green-600' : game.decision === 'L' ? 'text-red-600' : game.decision === 'S' ? 'text-blue-600' : ''}`}>
                                                    {game.decision || '-'}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};


const Calendar = ({ games }) => {
    const [selectedDate, setSelectedDate] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [selectedMonthForModal, setSelectedMonthForModal] = useState(null);

    const monthNames = ['March', 'April', 'May', 'June', 'July', 'August', 'September', 'October'];
    const monthIndices = [2, 3, 4, 5, 6, 7, 8, 9];

    const gamesByMonthDay = useMemo(() => {
        const aggregated = {};
        games.forEach(game => {
            const date = new Date(game.date);
            if (isNaN(date)) return;
            const month = date.getMonth();
            const day = date.getDate();
            const key = `${month}-${day}`;
            if (!aggregated[key]) aggregated[key] = [];
            aggregated[key].push(game);
        });
        return aggregated;
    }, [games]);

    const maxGamesOnDate = useMemo(() => {
        return Math.max(...Object.values(gamesByMonthDay).map(g => g.length), 1);
    }, [gamesByMonthDay]);

    const getHeatmapColor = (gameCount) => {
        if (gameCount === 0) return 'bg-slate-50 border-slate-200';
        const intensity = Math.min(gameCount / maxGamesOnDate, 1);
        if (intensity <= 0.25) return 'bg-blue-100 border-blue-200';
        if (intensity <= 0.5) return 'bg-blue-200 border-blue-300';
        if (intensity <= 0.75) return 'bg-blue-400 border-blue-500';
        return 'bg-blue-600 border-blue-700';
    };

    const getTextColor = (gameCount) => {
        if (gameCount === 0) return 'text-slate-700';
        const intensity = Math.min(gameCount / maxGamesOnDate, 1);
        return intensity > 0.5 ? 'text-white' : 'text-slate-700';
    };

    const year = useMemo(() => {
        const currentYear = new Date().getFullYear();
        const yearsWithGames = new Set();
        games.forEach(game => {
            const date = new Date(game.date);
            if (!isNaN(date)) yearsWithGames.add(date.getFullYear());
        });
        if (yearsWithGames.size === 0) return currentYear;
        return Math.max(...yearsWithGames);
    }, [games]);

    const getCalendarDaysForMonth = (monthIndex) => {
        const firstDay = new Date(year, monthIndex, 1);
        const lastDay = new Date(year, monthIndex + 1, 0);
        const startingDayOfWeek = firstDay.getDay();
        const daysInMonth = lastDay.getDate();
        const days = [];
        for (let i = 0; i < startingDayOfWeek; i++) days.push(null);
        for (let day = 1; day <= daysInMonth; day++) {
            const key = `${monthIndex}-${day}`;
            const gamesOnDate = gamesByMonthDay[key] || [];
            days.push({ day, games: gamesOnDate, key, month: monthIndex });
        }
        return days;
    };

    const handleDateClick = (day, monthIndex) => {
        if (day && day.games.length > 0) {
            setSelectedDate(day);
            setSelectedMonthForModal(monthIndex);
            setShowModal(true);
        }
    };

    const totalStats = useMemo(() => {
        const uniqueDates = new Set();
        games.forEach(g => {
            const date = new Date(g.date);
            if (!isNaN(date)) uniqueDates.add(g.date);
        });
        return {
            totalGames: games.length,
            uniqueDates: uniqueDates.size
        };
    }, [games]);

    const MonthCalendar = ({ monthIndex }) => {
        const days = getCalendarDaysForMonth(monthIndex);
        const gamesInMonth = games.filter(g => {
            const date = new Date(g.date);
            return !isNaN(date) && date.getMonth() === monthIndex;
        }).length;

        return (
            <div className="bg-white rounded-lg border border-slate-200 p-2">
                <div className="text-center mb-2">
                    <h3 className="font-bold text-slate-800" style={{ fontSize: '13px' }}>{monthNames[monthIndices.indexOf(monthIndex)]}</h3>
                    <span className="text-slate-500" style={{ fontSize: '11px' }}>{gamesInMonth} game{gamesInMonth !== 1 ? 's' : ''}</span>
                </div>
                <div className="grid grid-cols-7 gap-0.5">
                    {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
                        <div key={`day-header-${i}`} className="text-center text-slate-500 font-medium" style={{ fontSize: '9px' }}>{day}</div>
                    ))}
                    {days.map((day, idx) => {
                        if (!day) return <div key={`empty-${idx}`} className="aspect-square" />;
                        const hasGames = day.games.length > 0;
                        const bgColor = getHeatmapColor(day.games.length);
                        const textColor = getTextColor(day.games.length);
                        return (
                            <div
                                key={`day-${day.day}`}
                                onClick={() => handleDateClick(day, monthIndex)}
                                className={`aspect-square border rounded flex items-center justify-center transition-all ${bgColor} ${hasGames ? 'cursor-pointer hover:scale-110 hover:shadow-md' : ''}`}
                                title={hasGames ? `${day.games.length} game${day.games.length > 1 ? 's' : ''}` : ''}
                            >
                                <span className={`font-medium ${textColor}`} style={{ fontSize: '10px' }}>{day.day}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    };

    return (
        <>
            <div className="bg-white rounded-lg border border-slate-200">
                <div className="p-4 border-b">
                    <div className="flex justify-between items-center">
                        <div>
                            <h2 className="section-title font-bold">📅 Season Calendar Heatmap</h2>
                            <p className="small-text text-slate-500 mt-1">
                                {totalStats.totalGames} games • {totalStats.uniqueDates} unique dates • Click any date with games for details
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="small-text text-slate-600">Legend:</span>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-slate-50 border border-slate-200 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-slate-500">0</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-slate-500">1</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-400 border border-blue-500 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-slate-500">2-3</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-600 border border-blue-700 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-slate-500">4+</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="p-4">
                    <div className="grid grid-cols-4 gap-3">
                        {monthIndices.map((monthIndex) => (
                            <MonthCalendar key={monthIndex} monthIndex={monthIndex} />
                        ))}
                    </div>
                </div>
            </div>
            {showModal && selectedDate && (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                            <h3 className="section-title font-bold">{monthNames[monthIndices.indexOf(selectedMonthForModal)]} {selectedDate.day} • All Years</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedDate.games.length} game{selectedDate.games.length !== 1 ? 's' : ''} attended</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            <div className="divide-y">
                                {selectedDate.games.sort((a, b) => new Date(b.date) - new Date(a.date)).map((game) => (
                                    <div key={game.gameId} className="p-4 hover:bg-blue-50 transition-colors cursor-pointer"
                                        onClick={() => { window._pendingGameId = game.gameId; setShowModal(false); if (window.__navigateTab) window.__navigateTab('gamelog'); }}>
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-3">
                                                <span className="body-text font-bold text-blue-600">{game.date}</span>
                                                <span className="small-text text-slate-500">{game.startTime}</span>
                                            </div>
                                            <div onClick={(e) => e.stopPropagation()}>
                                                <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4 flex-wrap">
                                            <div className="flex items-center gap-2">
                                                <span className="body-text font-semibold w-12 text-right">{game.awayTeam}</span>
                                                <span className="body-text text-slate-500">@</span>
                                                <span className="body-text font-semibold w-12">{game.homeTeam}</span>
                                            </div>
                                            <span className="font-mono body-text bg-slate-100 px-3 py-1 rounded font-bold">{game.score}</span>
                                            <span className="body-text text-slate-600">{game.venue}</span>
                                            {game.attendance > 0 && <span className="small-text text-slate-500">👥 {game.attendance.toLocaleString()}</span>}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="p-4 border-t bg-slate-50">
                            <button onClick={() => setShowModal(false)} className="px-6 py-2 bg-blue-600 text-white body-text rounded-lg hover:bg-blue-700 font-medium w-full">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

const MatchupMatrix = ({ matchupData, games }) => {
    const [selectedMatchup, setSelectedMatchup] = useState(null);
    const [showModal, setShowModal] = useState(false);

    if (!matchupData || !matchupData.teams || matchupData.teams.length === 0) {
        return <div className="bg-white rounded-lg border border-slate-200 p-6 body-text">No matchup data available</div>;
    }

    const { teams, matrix } = matchupData;

    // Calculate matchup completion stats
    const totalPossibleMatchups = 30 * 29 / 2; // 435 unique matchups for 30 MLB teams
    const seenMatchups = new Set();

    matrix.forEach((row, i) => {
        teams.forEach((opponent, j) => {
            if (i < j) {
                const count = row[opponent];
                if (count !== 'X' && count > 0) {
                    const key = [row.team, opponent].sort().join('-');
                    seenMatchups.add(key);
                }
            }
        });
    });

    const uniqueMatchupsSeen = seenMatchups.size;
    const completionPercent = Math.round((uniqueMatchupsSeen / totalPossibleMatchups) * 100);

    // Normalize team codes for matching (e.g., ATH -> OAK)
    const normalizeCode = (code) => {
        return normalizeTeamCode(code);
    };

    const handleCellClick = (team, opponent, count) => {
        if (count === 'X' || count === 0) return;
        const nTeam = normalizeCode(team);
        const nOpp = normalizeCode(opponent);
        const matchupGames = games.filter(game => {
            const home = normalizeCode(game.homeTeam);
            const away = normalizeCode(game.awayTeam);
            return (home === nTeam && away === nOpp) ||
                   (home === nOpp && away === nTeam);
        }).sort((a, b) => new Date(b.date) - new Date(a.date));
        setSelectedMatchup({ team, opponent, games: matchupGames, count });
        setShowModal(true);
    };

    return (
        <>
            <div className="bg-white rounded-lg border border-slate-200">
                <div className="p-4 border-b">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h2 className="section-title font-bold">🎯 Team Matchup Matrix</h2>
                            <p className="body-text text-slate-500 mt-1">Click any cell to see games between those teams</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="text-center px-4 py-2 bg-blue-50 rounded-lg">
                                <div className="text-xl font-bold text-blue-600">{uniqueMatchupsSeen}/{totalPossibleMatchups}</div>
                                <div className="text-xs text-slate-500">Matchups Seen</div>
                            </div>
                            <div className="text-center px-4 py-2 bg-green-50 rounded-lg">
                                <div className="text-xl font-bold text-green-600">{completionPercent}%</div>
                                <div className="text-xs text-slate-500">Complete</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="p-2">
                    <table className="w-full border-collapse" style={{ tableLayout: 'fixed' }}>
                        <thead>
                            <tr>
                                <th className="border bg-slate-100 font-bold" style={{ fontSize: '9px', padding: '2px', width: '28px' }}></th>
                                {teams.map(team => (
                                    <th key={team} className="border bg-slate-50 font-medium" style={{ fontSize: '8px', padding: '1px', width: '24px' }}>{team}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {matrix.map((row) => (
                                <tr key={row.team}>
                                    <td className="border font-bold bg-slate-100" style={{ fontSize: '8px', padding: '1px' }}>{row.team}</td>
                                    {teams.map(opponent => {
                                        const value = row[opponent];
                                        const isX = value === 'X';
                                        const hasGames = !isX && value > 0;
                                        return (
                                            <td key={opponent} onClick={() => hasGames && handleCellClick(row.team, opponent, value)} className={`border text-center ${isX ? 'bg-slate-300' : hasGames ? 'bg-blue-100 font-bold cursor-pointer hover:bg-blue-300' : 'bg-white'}`} style={{ fontSize: '9px', padding: '1px' }}>
                                                {isX ? '' : (value || '')}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="p-2 border-t bg-slate-50">
                    <div className="flex items-center gap-4 justify-center text-slate-600" style={{ fontSize: '10px' }}>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-slate-300 border rounded"></div><span>Same team</span></div>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-white border rounded"></div><span>No games</span></div>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-blue-100 border rounded"></div><span>Has games (click)</span></div>
                    </div>
                </div>
            </div>
            {showModal && selectedMatchup && (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                            <h3 className="section-title font-bold">{selectedMatchup.team} vs {selectedMatchup.opponent}</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedMatchup.count} game{selectedMatchup.count !== 1 ? 's' : ''} attended</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            {selectedMatchup.games.length > 0 ? (
                                <div className="divide-y">
                                    {selectedMatchup.games.map((game) => {
                                        const isHomeGame = game.homeTeam === selectedMatchup.team;
                                        return (
                                            <div key={game.gameId} className="p-4 hover:bg-blue-50 transition-colors cursor-pointer"
                                                onClick={() => { window._pendingGameId = game.gameId; setShowModal(false); if (window.__navigateTab) window.__navigateTab('gamelog'); }}>
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-3">
                                                        <span className="body-text font-bold text-blue-600">{game.date}</span>
                                                        <span className="small-text text-slate-500">{game.startTime}</span>
                                                    </div>
                                                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                                                        <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4 flex-wrap">
                                                    <div className="flex items-center gap-2">
                                                        <span className={`body-text w-12 text-right ${isHomeGame ? 'font-normal' : 'font-bold'}`}>{game.awayTeam}</span>
                                                        <span className="body-text text-slate-500">@</span>
                                                        <span className={`body-text w-12 ${isHomeGame ? 'font-bold' : 'font-normal'}`}>{game.homeTeam}</span>
                                                    </div>
                                                    <span className="font-mono body-text bg-slate-100 px-3 py-1 rounded font-bold">{game.score}</span>
                                                    <span className="body-text text-slate-600">{game.venue}</span>
                                                    {game.attendance > 0 && <span className="small-text text-slate-500">👥 {game.attendance.toLocaleString()}</span>}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="p-8 text-center body-text text-slate-500">No games found between these teams</div>
                            )}
                        </div>
                        <div className="p-4 border-t bg-slate-50">
                            <button onClick={() => setShowModal(false)} className="px-6 py-2 bg-blue-600 text-white body-text rounded-lg hover:bg-blue-700 font-medium w-full">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

const OriolesStadiumMap = ({ orioles }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markersRef = useRef([]);

    // Build visited stadiums data from Orioles data
    const visitedData = useMemo(() => {
        const visited = {};
        (orioles || []).forEach(o => {
            const match = matchStadiumByName(o.stadium);
            if (match) {
                visited[match.id] = {
                    ...o,
                    stadiumInfo: match,
                    hasVisited: true,
                };
            }
        });
        return visited;
    }, [orioles]);

    // Calculate stats (only count current MLB stadiums toward the goal - exclude spring training)
    const stats = useMemo(() => {
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const historicalStadiums = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining);
        const springTrainingStadiums = ALL_MLB_STADIUMS.filter(s => s.springTraining);
        const visitedCount = currentStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        const historicalVisited = historicalStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        const springVisited = springTrainingStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        return {
            currentTotal: currentStadiums.length,
            visitedCount,
            historicalVisited,
            springVisited,
            remaining: currentStadiums.length - visitedCount,
            percent: Math.round((visitedCount / currentStadiums.length) * 100),
        };
    }, [visitedData]);

    // Initialize map
    useEffect(() => {
        if (!mapRef.current || mapInstanceRef.current) return;

        const map = L.map(mapRef.current).setView([39.8283, -98.5795], 4);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        mapInstanceRef.current = map;

        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, []);

    // Update markers
    useEffect(() => {
        if (!mapInstanceRef.current) return;

        // Clear existing markers
        markersRef.current.forEach(m => m.remove());
        markersRef.current = [];

        // Show current MLB stadiums + historical that were visited + spring training that were visited
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const visitedHistorical = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining && visitedData[s.id]?.hasVisited);
        const visitedSpringTraining = ALL_MLB_STADIUMS.filter(s => s.springTraining && visitedData[s.id]?.hasVisited);
        const stadiumsToShow = [...currentStadiums, ...visitedHistorical, ...visitedSpringTraining];

        stadiumsToShow.forEach(stadium => {
            const data = visitedData[stadium.id];
            const hasVisited = data?.hasVisited;
            const isHistorical = !stadium.current && !stadium.springTraining;
            const isSpringTraining = stadium.springTraining;

            // Determine marker color
            let fillColor = '#9ca3af'; // gray - not visited
            let borderColor = '#6b7280';
            if (hasVisited && isSpringTraining) {
                fillColor = '#22c55e'; // green - spring training visited
                borderColor = '#16a34a';
            } else if (hasVisited && isHistorical) {
                fillColor = '#a855f7'; // purple - historical visited
                borderColor = '#9333ea';
            } else if (hasVisited) {
                fillColor = '#f97316'; // orange - saw Orioles (current)
                borderColor = '#ea580c';
            }

            const marker = L.circleMarker([stadium.lat, stadium.lng], {
                radius: hasVisited ? 10 : 7,
                fillColor: fillColor,
                color: borderColor,
                weight: 2,
                opacity: 1,
                fillOpacity: hasVisited ? 0.9 : 0.4
            }).addTo(mapInstanceRef.current);

            // Build popup content
            let statusText = '<span style="color: #9ca3af;">Not yet visited with Orioles</span>';
            let detailsHtml = '';
            let teamLabel = stadium.team;

            if (hasVisited && isSpringTraining) {
                statusText = '<span style="color: #22c55e; font-weight: bold;">✓ Spring Training - Saw Orioles here!</span>';
                teamLabel = 'Spring Training';
            } else if (hasVisited && isHistorical) {
                statusText = '<span style="color: #a855f7; font-weight: bold;">✓ Historical - Saw Orioles here!</span>';
                detailsHtml += `<div style="color: #666; font-size: 11px;">${stadium.years}</div>`;
            } else if (hasVisited) {
                statusText = '<span style="color: #f97316; font-weight: bold;">✓ Saw Orioles here!</span>';
            }

            if (hasVisited) {
                if (data.record) {
                    detailsHtml += `<div><strong>O's Record:</strong> ${data.record}</div>`;
                }
                if (data.games) {
                    detailsHtml += `<div><strong>Games:</strong> ${data.games}</div>`;
                }
                if (data.firstVisit) {
                    detailsHtml += `<div><strong>First:</strong> ${data.firstVisit}</div>`;
                }
                if (data.lastVisit) {
                    detailsHtml += `<div><strong>Last:</strong> ${data.lastVisit}</div>`;
                }
            }

            const popupContent = `
                <div style="min-width: 180px; font-family: system-ui, sans-serif;">
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">${stadium.name}</div>
                    <div style="color: #666; font-size: 12px; margin-bottom: 8px;">${teamLabel}${isHistorical ? ' (Historical)' : ''}</div>
                    <div style="margin-bottom: 8px;">${statusText}</div>
                    ${detailsHtml}
                </div>
            `;

            marker.bindPopup(popupContent);
            markersRef.current.push(marker);
        });
    }, [visitedData]);

    return (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <div className="p-4 border-b bg-gradient-to-r from-orange-500 to-orange-600 text-white">
                <h3 className="font-bold text-lg">🗺️ Orioles Stadium Quest</h3>
                <p className="text-sm text-orange-100 mt-1">See the Orioles at all 30 MLB stadiums</p>
            </div>
            <div ref={mapRef} style={{ height: '400px', width: '100%' }}></div>
            <div className="p-4 bg-orange-50 border-t">
                <div className="grid grid-cols-5 gap-4 text-center">
                    <div>
                        <div className="text-2xl font-bold text-orange-600">{stats.visitedCount}</div>
                        <div className="text-xs text-slate-600">Current</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-purple-600">{stats.historicalVisited}</div>
                        <div className="text-xs text-slate-600">Historical</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-slate-500">{stats.remaining}</div>
                        <div className="text-xs text-slate-600">Remaining</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-orange-600">{stats.percent}%</div>
                        <div className="text-xs text-slate-600">Complete</div>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1">
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                            <span className="text-xs text-slate-600">Current</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                            <span className="text-xs text-slate-600">Historical</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                            <span className="text-xs text-slate-600">Not yet</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const OriolesDashboard = ({ orioles, games }) => {
    // Filter to only Orioles games
    const oriolesGames = useMemo(() => {
        return (games || []).filter(g => g.homeTeam === 'BAL' || g.awayTeam === 'BAL')
            .sort((a, b) => new Date(a.date) - new Date(b.date));
    }, [games]);

    // Helper to parse score from format like "BOS 6 - 5 BAL" or "6-5"
    const parseScore = (scoreStr, homeTeam, awayTeam) => {
        if (!scoreStr) return null;
        // Try format: "AWAY # - # HOME" (e.g., "BOS 6 - 5 BAL")
        const match1 = scoreStr.match(/(\w+)\s+(\d+)\s*-\s*(\d+)\s+(\w+)/);
        if (match1) {
            const [_, team1, score1, score2, team2] = match1;
            // Determine which score belongs to home/away
            if (team2 === homeTeam || team2.includes(homeTeam)) {
                return { awayScore: parseInt(score1), homeScore: parseInt(score2) };
            } else {
                return { awayScore: parseInt(score2), homeScore: parseInt(score1) };
            }
        }
        // Try simple format: "#-#"
        const match2 = scoreStr.match(/(\d+)\s*-\s*(\d+)/);
        if (match2) {
            return { awayScore: parseInt(match2[1]), homeScore: parseInt(match2[2]) };
        }
        return null;
    };

    // Calculate summary stats
    const summaryStats = useMemo(() => {
        let wins = 0, losses = 0, runsScored = 0, runsAllowed = 0, homeRuns = 0;
        let homeWins = 0, homeLosses = 0, awayWins = 0, awayLosses = 0;

        oriolesGames.forEach(game => {
            const isHome = game.homeTeam === 'BAL';
            const scores = parseScore(game.score, game.homeTeam, game.awayTeam);
            if (!scores) return;

            const { awayScore, homeScore } = scores;
            const oRuns = isHome ? homeScore : awayScore;
            const oppRuns = isHome ? awayScore : homeScore;
            const won = oRuns > oppRuns;

            runsScored += oRuns;
            runsAllowed += oppRuns;

            if (won) {
                wins++;
                if (isHome) homeWins++; else awayWins++;
            } else {
                losses++;
                if (isHome) homeLosses++; else awayLosses++;
            }
        });

        return {
            record: `${wins}-${losses}`,
            winPct: wins + losses > 0 ? ((wins / (wins + losses)) * 100).toFixed(1) : '0.0',
            runsScored,
            runsAllowed,
            runDiff: runsScored - runsAllowed,
            homeRecord: `${homeWins}-${homeLosses}`,
            awayRecord: `${awayWins}-${awayLosses}`,
            totalGames: oriolesGames.length
        };
    }, [oriolesGames]);

    // Normalize team codes (OAK and ATH are the same franchise)
    const normalizeTeam = (code) => {
        return normalizeTeamCode(code);
    };

    // Calculate opponent breakdown
    const opponentStats = useMemo(() => {
        const stats = {};
        const alEast = ['NYY', 'NYA', 'BOS', 'TOR', 'TB', 'TBA'];

        oriolesGames.forEach(game => {
            const isHome = game.homeTeam === 'BAL';
            const rawOpponent = isHome ? game.awayTeam : game.homeTeam;
            const opponent = normalizeTeam(rawOpponent);
            const scores = parseScore(game.score, game.homeTeam, game.awayTeam);
            if (!scores) return;

            const { awayScore, homeScore } = scores;
            const oRuns = isHome ? homeScore : awayScore;
            const oppRuns = isHome ? awayScore : homeScore;
            const won = oRuns > oppRuns;

            if (!stats[opponent]) {
                stats[opponent] = { wins: 0, losses: 0, runsScored: 0, runsAllowed: 0, isAlEast: alEast.includes(opponent) };
            }
            if (won) stats[opponent].wins++;
            else stats[opponent].losses++;
            stats[opponent].runsScored += oRuns;
            stats[opponent].runsAllowed += oppRuns;
        });

        return Object.entries(stats)
            .map(([team, s]) => ({
                team,
                record: `${s.wins}-${s.losses}`,
                wins: s.wins,
                losses: s.losses,
                games: s.wins + s.losses,
                runsScored: s.runsScored,
                runsAllowed: s.runsAllowed,
                runDiff: s.runsScored - s.runsAllowed,
                isAlEast: s.isAlEast
            }))
            .sort((a, b) => b.games - a.games);
    }, [oriolesGames]);

    // Calculate streaks and timeline
    const streaksData = useMemo(() => {
        let currentStreak = { type: null, count: 0 };
        let longestWinStreak = 0, longestLossStreak = 0;
        let tempWinStreak = 0, tempLossStreak = 0;
        const recentGames = [];

        oriolesGames.forEach(game => {
            const isHome = game.homeTeam === 'BAL';
            const scores = parseScore(game.score, game.homeTeam, game.awayTeam);
            if (!scores) return;

            const { awayScore, homeScore } = scores;
            const oRuns = isHome ? homeScore : awayScore;
            const oppRuns = isHome ? awayScore : homeScore;
            const won = oRuns > oppRuns;

            recentGames.push({
                date: game.date,
                opponent: isHome ? game.awayTeam : game.homeTeam,
                result: won ? 'W' : 'L',
                score: `${oRuns}-${oppRuns}`,
                venue: game.venue,
                isHome
            });

            if (won) {
                tempWinStreak++;
                tempLossStreak = 0;
                longestWinStreak = Math.max(longestWinStreak, tempWinStreak);
            } else {
                tempLossStreak++;
                tempWinStreak = 0;
                longestLossStreak = Math.max(longestLossStreak, tempLossStreak);
            }
        });

        // Current streak from most recent games
        if (recentGames.length > 0) {
            const lastResult = recentGames[recentGames.length - 1].result;
            let streakCount = 0;
            for (let i = recentGames.length - 1; i >= 0; i--) {
                if (recentGames[i].result === lastResult) streakCount++;
                else break;
            }
            currentStreak = { type: lastResult, count: streakCount };
        }

        // Monthly breakdown - handle both YYYY-MM-DD and MM/DD/YYYY formats
        const monthlyStats = {};
        const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        recentGames.forEach(g => {
            if (!g.date) return;
            let year, monthNum;
            if (g.date.includes('/')) {
                // MM/DD/YYYY format
                const parts = g.date.split('/');
                monthNum = parseInt(parts[0]);
                year = parts[2]?.length === 2 ? '20' + parts[2] : parts[2];
            } else if (g.date.includes('-')) {
                // YYYY-MM-DD format
                const parts = g.date.split('-');
                year = parts[0];
                monthNum = parseInt(parts[1]);
            }
            if (!year || !monthNum) return;
            const monthKey = `${year}-${String(monthNum).padStart(2, '0')}`;
            if (!monthlyStats[monthKey]) monthlyStats[monthKey] = { wins: 0, losses: 0, year, monthNum };
            if (g.result === 'W') monthlyStats[monthKey].wins++;
            else monthlyStats[monthKey].losses++;
        });

        return {
            currentStreak,
            longestWinStreak,
            longestLossStreak,
            recentGames: recentGames.slice(-10).reverse(),
            monthlyStats: Object.entries(monthlyStats).map(([key, s]) => ({
                month: `${monthNames[s.monthNum]} ${s.year}`,
                sortKey: key,
                record: `${s.wins}-${s.losses}`,
                wins: s.wins,
                losses: s.losses
            })).sort((a, b) => a.sortKey.localeCompare(b.sortKey))
        };
    }, [oriolesGames]);

    const alEastOpponents = opponentStats.filter(o => o.isAlEast);
    const otherOpponents = opponentStats.filter(o => !o.isAlEast);

    return (
        <div className="space-y-6">
            {/* Summary Stats */}
            <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
                <h2 className="text-2xl font-bold mb-4">🧡 Orioles Dashboard</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.record}</div>
                        <div className="text-sm opacity-90">Record</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.winPct}%</div>
                        <div className="text-sm opacity-90">Win %</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.runsScored}</div>
                        <div className="text-sm opacity-90">Runs Scored</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.runsAllowed}</div>
                        <div className="text-sm opacity-90">Runs Allowed</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className={`text-3xl font-bold ${summaryStats.runDiff >= 0 ? 'text-green-200' : 'text-red-200'}`}>
                            {summaryStats.runDiff >= 0 ? '+' : ''}{summaryStats.runDiff}
                        </div>
                        <div className="text-sm opacity-90">Run Diff</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.homeRecord}</div>
                        <div className="text-sm opacity-90">Home</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.awayRecord}</div>
                        <div className="text-sm opacity-90">Away</div>
                    </div>
                </div>
            </div>

            {/* Stadium Map */}
            <OriolesStadiumMap orioles={orioles} />

            {/* Streaks & Recent Games */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b">
                        <h3 className="font-bold text-lg">📈 Streaks</h3>
                    </div>
                    <div className="p-4">
                        <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="text-center p-3 bg-slate-50 rounded-lg">
                                <div className={`text-2xl font-bold ${streaksData.currentStreak.type === 'W' ? 'text-green-600' : 'text-red-600'}`}>
                                    {streaksData.currentStreak.type}{streaksData.currentStreak.count}
                                </div>
                                <div className="text-xs text-slate-500">Current</div>
                            </div>
                            <div className="text-center p-3 bg-green-50 rounded-lg">
                                <div className="text-2xl font-bold text-green-600">W{streaksData.longestWinStreak}</div>
                                <div className="text-xs text-slate-500">Longest Win Streak</div>
                            </div>
                            <div className="text-center p-3 bg-red-50 rounded-lg">
                                <div className="text-2xl font-bold text-red-600">L{streaksData.longestLossStreak}</div>
                                <div className="text-xs text-slate-500">Longest Loss Streak</div>
                            </div>
                        </div>
                        <h4 className="font-semibold text-sm text-slate-600 mb-2">Last 10 Games</h4>
                        <div className="flex gap-1 flex-wrap">
                            {streaksData.recentGames.map((g) => (
                                <div key={g.gameId || `${g.date}-${g.opponent}`} className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold text-white ${g.result === 'W' ? 'bg-green-500' : 'bg-red-500'}`} title={`${g.date}: ${g.result} ${g.score} vs ${g.opponent}`}>
                                    {g.result}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b">
                        <h3 className="font-bold text-lg">📅 Monthly Breakdown</h3>
                    </div>
                    <div className="p-4">
                        <div className="space-y-2">
                            {streaksData.monthlyStats.map(m => {
                                const total = m.wins + m.losses;
                                const winPct = total > 0 ? (m.wins / total) * 100 : 0;
                                return (
                                    <div key={m.month} className="flex items-center gap-3">
                                        <span className="w-20 text-sm font-medium">{m.month}</span>
                                        <div className="flex-1 bg-slate-200 rounded-full h-4 overflow-hidden">
                                            <div className="bg-green-500 h-full" style={{ width: `${winPct}%` }}></div>
                                        </div>
                                        <span className="w-16 text-sm font-semibold text-right">{m.record}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>

            {/* Opponent Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-t-lg">
                        <h3 className="font-bold text-lg">⚔️ vs AL East</h3>
                    </div>
                    <div className="p-4">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-slate-500 border-b">
                                    <th className="pb-2">Team</th>
                                    <th className="pb-2 text-center">G</th>
                                    <th className="pb-2 text-center">Record</th>
                                    <th className="pb-2 text-center">RS</th>
                                    <th className="pb-2 text-center">RA</th>
                                    <th className="pb-2 text-center">Diff</th>
                                </tr>
                            </thead>
                            <tbody>
                                {alEastOpponents.map(o => (
                                    <tr key={o.team} className="border-b last:border-0 hover:bg-slate-50">
                                        <td className="py-2 font-semibold">{o.team}</td>
                                        <td className="py-2 text-center">{o.games}</td>
                                        <td className="py-2 text-center font-mono">{o.record}</td>
                                        <td className="py-2 text-center">{o.runsScored}</td>
                                        <td className="py-2 text-center">{o.runsAllowed}</td>
                                        <td className={`py-2 text-center font-semibold ${o.runDiff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {o.runDiff >= 0 ? '+' : ''}{o.runDiff}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b">
                        <h3 className="font-bold text-lg">🏟️ vs Other Teams</h3>
                    </div>
                    <div className="p-4 max-h-64 overflow-y-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-slate-500 border-b">
                                    <th className="pb-2">Team</th>
                                    <th className="pb-2 text-center">G</th>
                                    <th className="pb-2 text-center">Record</th>
                                    <th className="pb-2 text-center">Diff</th>
                                </tr>
                            </thead>
                            <tbody>
                                {otherOpponents.map(o => (
                                    <tr key={o.team} className="border-b last:border-0 hover:bg-slate-50">
                                        <td className="py-2 font-semibold">{o.team}</td>
                                        <td className="py-2 text-center">{o.games}</td>
                                        <td className="py-2 text-center font-mono">{o.record}</td>
                                        <td className={`py-2 text-center font-semibold ${o.runDiff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {o.runDiff >= 0 ? '+' : ''}{o.runDiff}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Stadium Table */}
            <DataTable
                title="🏟️ Orioles by Stadium"
                data={orioles || []}
                defaultSortKey="games"
                columns={[
                    { key: 'stadium', label: 'Stadium' },
                    { key: 'games', label: 'G' },
                    { key: 'record', label: 'Record' },
                    { key: 'firstVisit', label: 'First' },
                    { key: 'lastVisit', label: 'Last' },
                    { key: 'runsScored', label: 'RS' },
                    { key: 'runsAllowed', label: 'RA' },
                    { key: 'runDiff', label: 'Diff' },
                    { key: 'homeRunsHit', label: 'HR' },
                    { key: 'oneRunGames', label: '1-Run' }
                ]}
            />
        </div>
    );
};

const CompanionStadiumMap = ({ companion }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markersRef = useRef([]);

    // Build visited stadiums data from companion data
    const visitedData = useMemo(() => {
        const visited = {};
        const stadiumsList = companion?.stadiumsList || [];
        const oriolesStadiumsList = companion?.oriolesStadiumsList || [];

        // Mark all visited stadiums
        stadiumsList.forEach(stadiumName => {
            const match = matchStadiumByName(stadiumName);
            if (match) {
                visited[match.id] = {
                    stadiumInfo: match,
                    hasVisited: true,
                    sawOrioles: oriolesStadiumsList.includes(stadiumName),
                };
            }
        });
        return visited;
    }, [companion]);

    // Calculate stats (only count current MLB stadiums toward the goal - exclude spring training)
    const stats = useMemo(() => {
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const historicalStadiums = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining);
        const visitedCount = currentStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        const oriolesCount = currentStadiums.filter(s => visitedData[s.id]?.sawOrioles).length;
        const historicalVisited = historicalStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        return {
            currentTotal: currentStadiums.length,
            visitedCount,
            oriolesCount,
            historicalVisited,
            remaining: currentStadiums.length - visitedCount,
        };
    }, [visitedData]);

    // Initialize map
    useEffect(() => {
        if (!mapRef.current || mapInstanceRef.current) return;

        const map = L.map(mapRef.current).setView([39.8283, -98.5795], 4);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        mapInstanceRef.current = map;

        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, []);

    // Update markers
    useEffect(() => {
        if (!mapInstanceRef.current) return;

        // Clear existing markers
        markersRef.current.forEach(m => m.remove());
        markersRef.current = [];

        // Show current MLB stadiums + historical that were visited + spring training that were visited
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const visitedHistorical = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining && visitedData[s.id]?.hasVisited);
        const visitedSpringTraining = ALL_MLB_STADIUMS.filter(s => s.springTraining && visitedData[s.id]?.hasVisited);
        const stadiumsToShow = [...currentStadiums, ...visitedHistorical, ...visitedSpringTraining];

        stadiumsToShow.forEach(stadium => {
            const data = visitedData[stadium.id];
            const hasVisited = data?.hasVisited;
            const sawOrioles = data?.sawOrioles;
            const isHistorical = !stadium.current && !stadium.springTraining;
            const isSpringTraining = stadium.springTraining;

            // Determine marker color
            let fillColor = '#9ca3af'; // gray - not visited
            let borderColor = '#6b7280';
            if (hasVisited && isSpringTraining) {
                fillColor = '#06b6d4'; // cyan - spring training
                borderColor = '#0891b2';
            } else if (hasVisited && isHistorical) {
                fillColor = '#a855f7'; // purple - historical
                borderColor = '#9333ea';
            } else if (sawOrioles) {
                fillColor = '#f97316'; // orange - saw Orioles
                borderColor = '#ea580c';
            } else if (hasVisited) {
                fillColor = '#22c55e'; // green - visited (non-Orioles)
                borderColor = '#16a34a';
            }

            const marker = L.circleMarker([stadium.lat, stadium.lng], {
                radius: hasVisited ? 10 : 7,
                fillColor: fillColor,
                color: borderColor,
                weight: 2,
                opacity: 1,
                fillOpacity: hasVisited ? 0.9 : 0.4
            }).addTo(mapInstanceRef.current);

            // Build popup content
            let statusText = '<span style="color: #9ca3af;">Not yet visited together</span>';
            let teamLabel = stadium.team;
            if (hasVisited && isSpringTraining) {
                statusText = `<span style="color: #06b6d4; font-weight: bold;">✓ Spring Training${sawOrioles ? ' + Orioles' : ''}</span>`;
                teamLabel = 'Spring Training';
            } else if (hasVisited && isHistorical) {
                statusText = `<span style="color: #a855f7; font-weight: bold;">✓ Historical${sawOrioles ? ' + Orioles' : ''}</span>`;
            } else if (sawOrioles) {
                statusText = '<span style="color: #f97316; font-weight: bold;">✓ Visited + Saw Orioles</span>';
            } else if (hasVisited) {
                statusText = '<span style="color: #22c55e; font-weight: bold;">✓ Visited together</span>';
            }

            const popupContent = `
                <div style="min-width: 180px; font-family: system-ui, sans-serif;">
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">${stadium.name}</div>
                    <div style="color: #666; font-size: 12px; margin-bottom: 8px;">${teamLabel}${isHistorical ? ' (Historical)' : ''}</div>
                    ${isHistorical ? `<div style="color: #666; font-size: 11px; margin-bottom: 4px;">${stadium.years}</div>` : ''}
                    <div>${statusText}</div>
                </div>
            `;

            marker.bindPopup(popupContent);
            markersRef.current.push(marker);
        });
    }, [visitedData]);

    if (!companion) return null;

    return (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden mt-4">
            <div className="p-3 border-b bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                <h4 className="font-bold">🗺️ Stadiums with {companion.name}</h4>
            </div>
            <div ref={mapRef} style={{ height: '300px', width: '100%' }}></div>
            <div className="p-3 bg-slate-50 border-t">
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3 flex-wrap">
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-500"></span>
                            <span className="text-slate-600 text-xs">Visited ({stats.visitedCount - stats.oriolesCount})</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                            <span className="text-slate-600 text-xs">O's ({stats.oriolesCount})</span>
                        </div>
                        {stats.historicalVisited > 0 && (
                            <div className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                                <span className="text-slate-600 text-xs">Historical ({stats.historicalVisited})</span>
                            </div>
                        )}
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                            <span className="text-slate-600 text-xs">Not yet ({stats.remaining})</span>
                        </div>
                    </div>
                    <span className="font-bold text-blue-600">{stats.visitedCount}/30</span>
                </div>
            </div>
        </div>
    );
};

const CompanionsView = ({ companionData }) => {
    const [selectedCompanion, setSelectedCompanion] = useState(null);
    const [showGames, setShowGames] = useState(false);

    if (!companionData || !companionData.companions || Object.keys(companionData.companions).length === 0) {
        return (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h2 className="section-title font-bold mb-4">👥 Games With Companions</h2>
                <div className="text-center py-8">
                    <p className="body-text text-slate-600 mb-4">No companion data found.</p>
                    <div className="bg-slate-50 rounded-lg p-4 max-w-lg mx-auto text-left">
                        <p className="font-semibold text-slate-800 mb-2">To track games with companions:</p>
                        <ol className="list-decimal list-inside space-y-1 text-sm text-slate-600">
                            <li>Edit <code className="bg-slate-200 px-1 rounded">companions.csv</code> in your MLB Game Tracker folder</li>
                            <li>Add rows with format: <code className="bg-slate-200 px-1 rounded">GameID,Companion1|Companion2</code></li>
                            <li>Example: <code className="bg-slate-200 px-1 rounded">BAL202505090,Dad</code></li>
                            <li>Regenerate the website</li>
                        </ol>
                    </div>
                </div>
            </div>
        );
    }

    const companions = Object.values(companionData.companions);

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg border border-slate-200">
                <div className="p-4 border-b">
                    <h2 className="section-title font-bold">👥 Games With Companions</h2>
                    <p className="body-text text-slate-500 mt-1">Track who you've attended games with</p>
                </div>
                <div className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {companions.map(companion => (
                            <div key={companion.name} className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="font-bold text-lg text-blue-800">{companion.name}</h3>
                                    <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-bold">
                                        {companion.totalGames} game{companion.totalGames !== 1 ? 's' : ''}
                                    </span>
                                </div>
                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-slate-600">Stadiums visited:</span>
                                        <span className="font-semibold">{companion.uniqueStadiums}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-600">Orioles games:</span>
                                        <span className="font-semibold text-orange-600">{companion.oriolesGames}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-600">O's stadiums:</span>
                                        <span className="font-semibold text-orange-600">{companion.oriolesStadiums}</span>
                                    </div>
                                </div>
                                <div className="mt-3 pt-3 border-t border-blue-200">
                                    <button
                                        onClick={() => { setSelectedCompanion(companion); setShowGames(true); }}
                                        className="w-full text-center text-sm text-blue-600 hover:text-blue-800 font-medium"
                                    >
                                        View all games →
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Detailed stats per companion */}
            {companions.map(companion => (
                <div key={companion.name} className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
                        <h3 className="font-bold text-lg">📊 {companion.name} - Detailed Stats</h3>
                    </div>
                    <div className="p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Stadiums visited */}
                            <div>
                                <h4 className="font-semibold text-slate-800 mb-2">🏟️ Stadiums Visited ({companion.uniqueStadiums})</h4>
                                <div className="flex flex-wrap gap-1">
                                    {companion.stadiumsList.map(stadium => (
                                        <span key={stadium} className="px-2 py-1 bg-slate-100 rounded text-xs">{stadium}</span>
                                    ))}
                                </div>
                            </div>
                            {/* Orioles stadiums */}
                            <div>
                                <h4 className="font-semibold text-orange-700 mb-2">🧡 Orioles Stadiums ({companion.oriolesStadiums})</h4>
                                <div className="flex flex-wrap gap-1">
                                    {companion.oriolesStadiumsList.map(stadium => (
                                        <span key={stadium} className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">{stadium}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                        {/* Recent games */}
                        <div className="mt-4">
                            <h4 className="font-semibold text-slate-800 mb-2">📋 Recent Games (last 5)</h4>
                            <div className="space-y-1">
                                {companion.games.slice(0, 5).map(game => {
                                    const formatDate = (dateStr) => {
                                        if (!dateStr) return '';
                                        const d = new Date(dateStr.split(' ')[0]);
                                        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                                    };
                                    return (
                                        <div key={game.gameId} className="grid grid-cols-3 text-sm bg-slate-50 px-3 py-2 rounded">
                                            <span className="font-medium">{formatDate(game.date)}</span>
                                            <span className="text-center">{game.awayTeam} @ {game.homeTeam}</span>
                                            <span className="text-slate-500 text-right">{game.venue}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                        {/* Stadium Map */}
                        <CompanionStadiumMap companion={companion} />
                    </div>
                </div>
            ))}

            {/* Modal for all games */}
            {showGames && selectedCompanion && (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowGames(false)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                            <h3 className="section-title font-bold">Games with {selectedCompanion.name}</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedCompanion.totalGames} total games</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            <div className="divide-y">
                                {selectedCompanion.games.map((game) => (
                                    <div key={game.gameId || `${game.date}-${game.awayTeam}-${game.homeTeam}`}
                                        className="p-4 hover:bg-blue-50 transition-colors cursor-pointer"
                                        onClick={() => { if (game.gameId) { window._pendingGameId = game.gameId; setShowGames(false); if (window.__navigateTab) window.__navigateTab('gamelog'); } }}>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <span className="font-bold text-blue-600">{(game.date || '').split(' ')[0]}</span>
                                                <span className="font-semibold">{game.awayTeam} @ {game.homeTeam}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className="text-slate-600">{game.venue}</span>
                                                <span className="text-xs text-blue-500">View →</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="p-4 border-t bg-slate-50">
                            <button onClick={() => setShowGames(false)} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium w-full">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};


const DynamicPlayerTable = ({ allPlayers, playerGames, ncaaCrossRef, careerFirstsByPlayer, allTimePassings, milestones, debuts, finalGames }) => {
    const [search, setSearch] = useState('');
    const [sortKey, setSortKey] = useState('pa');
    const [sortDir, setSortDir] = useState('desc');
    const [activeFilter, setActiveFilter] = useState('all');
    const [gameTypeFilter, setGameTypeFilter] = useState('regular');

    // Check for pending player selection (from search/College tab)
    useEffect(() => {
        if (window._pendingPlayerSelect) {
            const pid = window._pendingPlayerSelect.id;
            if (allPlayers.some(p => p.playerId === pid)) {
                setSelectedPlayer(window._pendingPlayerSelect);
                window._pendingPlayerSelect = null;
            }
        }
    });
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [useFiltered, setUseFiltered] = useState(false);
    const [selectedPlayer, setSelectedPlayer] = useState(null);

    useEffect(() => { setUseFiltered(!!(startDate || endDate)); }, [startDate, endDate]);

    // Map game type to stat prefixes
    const getStatKey = (baseKey, gameType) => {
        if (gameType === 'all') return baseKey;
        const prefixMap = {
            'spring': 'spring',
            'regular': 'regular',
            'postseason': 'postseason'
        };
        const keyMap = {
            'games': 'Games', 'ab': 'Ab', 'pa': 'Pa', 'h': 'H', 'avg': 'Avg',
            'r': 'R', 'rbi': 'Rbi', 'hr': 'Hr', 'doubles': 'Doubles',
            'triples': 'Triples', 'sb': 'Sb', 'bb': 'Bb', 'so': 'So', 'team': 'Team'
        };
        return prefixMap[gameType] + (keyMap[baseKey] || baseKey.charAt(0).toUpperCase() + baseKey.slice(1));
    };

    // Filter playerGames by game type and date, then aggregate
    const gameTypeData = useMemo(() => {
        let games = playerGames;
        if (gameTypeFilter !== 'all') {
            games = games.filter(g => (g.gameType || 'regular') === gameTypeFilter);
        }
        if (useFiltered) {
            if (startDate) games = games.filter(g => g.dateSort >= startDate);
            if (endDate) games = games.filter(g => g.dateSort <= endDate);
        }
        return aggregateHitterStats(games);
    }, [playerGames, gameTypeFilter, startDate, endDate, useFiltered]);

    const filtered = useMemo(() => {
        let result = gameTypeData;
        if (activeFilter !== 'all') result = result.filter(row => row.team.includes(activeFilter));
        if (search) result = result.filter(row => Object.values(row).some(val => String(val).toLowerCase().includes(search.toLowerCase())));
        return result;
    }, [gameTypeData, search, activeFilter]);

    const sorted = useMemo(() => {
        if (!sortKey) return filtered;
        return [...filtered].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal).localeCompare(String(bVal));
            return sortDir === 'asc' ? result : -result;
        });
    }, [filtered, sortKey, sortDir]);

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    const filterValues = useMemo(() => {
        const teams = new Set();
        allPlayers.forEach(p => p.team.split(', ').forEach(t => teams.add(t.trim())));
        return Array.from(teams).sort();
    }, [allPlayers]);

    const columns = [
        {
            key: 'name',
            label: 'Name',
            render: (v, r) => (
                <div className="flex items-center gap-2">
                    <PlayerLink playerId={r.playerId} name={v} external />
                    <button
                        onClick={() => setSelectedPlayer({ id: r.playerId, name: v })}
                        className="px-2 py-1 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded text-xs font-semibold whitespace-nowrap"
                        title="View career timeline"
                    >
                        📊
                    </button>
                </div>
            )
        },
        { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'ab', label: 'AB' }, { key: 'pa', label: 'PA' },
        { key: 'h', label: 'H' }, { key: 'avg', label: 'AVG' }, { key: 'r', label: 'R' }, { key: 'rbi', label: 'RBI' },
        { key: 'hr', label: 'HR' }, { key: 'doubles', label: '2B' }, { key: 'triples', label: '3B' }, { key: 'sb', label: 'SB' },
        { key: 'bb', label: 'BB' }, { key: 'so', label: 'SO' }, { key: 'obp', label: 'OBP' }, { key: 'slg', label: 'SLG' }, { key: 'ops', label: 'OPS' },
        { key: 'maxExitVelo', label: 'Max EV', render: (v) => v ? `${v}` : '-' },
        { key: 'avgExitVelo', label: 'Avg EV', render: (v) => v ? `${v}` : '-' },
    ];

    const gameTypeLabels = { all: 'All Games', spring: 'Spring Training', regular: 'Regular Season', postseason: 'Postseason' };

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="section-title font-bold">👤 Hitter Statistics {gameTypeFilter !== 'all' && <span className="small-text text-green-600">({gameTypeLabels[gameTypeFilter]})</span>} {useFiltered && <span className="small-text text-blue-600">(Date Filtered)</span>}</h2>
                    <div className="flex items-center gap-2">
                        <span className="body-text text-slate-500">{sorted.length} players</span>
                        <button onClick={() => exportToCSV(sorted, columns, 'Hitter_Statistics.csv')} className="px-3 py-1 bg-green-600 text-white body-text rounded hover:bg-green-700">📥 Export</button>
                    </div>
                </div>
                <div className="flex flex-wrap gap-4">
                    <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1 min-w-[200px] px-4 py-2 body-text border rounded-lg" />
                    <select value={gameTypeFilter} onChange={(e) => setGameTypeFilter(e.target.value)} className="px-4 py-2 body-text border rounded-lg bg-green-50">
                        <option value="all">All Games</option>
                        <option value="regular">Regular Season</option>
                        <option value="spring">Spring Training</option>
                        <option value="postseason">Postseason</option>
                    </select>
                    <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="px-4 py-2 body-text border rounded-lg" />
                    <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="px-4 py-2 body-text border rounded-lg" />
                    {(startDate || endDate) && <button onClick={() => { setStartDate(''); setEndDate(''); }} className="px-3 py-2 body-text text-slate-600 hover:text-slate-900">Clear Dates</button>}
                    <select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)} className="px-4 py-2 body-text border rounded-lg">
                        <option value="all">All Teams</option>
                        {filterValues.map(val => <option key={val} value={val}>{val}</option>)}
                    </select>
                </div>
                {useFiltered && <div className="bg-yellow-50 border border-yellow-200 rounded p-3"><p className="body-text text-yellow-900">⚡ Stats recalculated for selected date range</p></div>}
            </div>
            <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="w-full">
                    <thead className="bg-slate-50 sticky top-0">
                        <tr>{columns.map(col => <th key={col.key} onClick={() => handleSort(col.key)} className="px-4 py-3 text-left small-text font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100">{col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y">
                        {sorted.map((row) => (
                            <tr key={row.playerId} className="hover:bg-blue-50">
                                {columns.map(col => <td key={col.key} className="px-4 py-3 body-text">{col.render ? col.render(row[col.key], row) : row[col.key]}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {selectedPlayer && (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPlayer(null)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-4xl max-w-[95vw] w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-purple-700 text-white">
                            <div className="flex items-center gap-3">
                                <h3 className="section-title font-bold">{selectedPlayer.name}</h3>
                                {ncaaCrossRef && ncaaCrossRef[selectedPlayer.id] && (
                                    <button onClick={() => { setSelectedPlayer(null); if (window.__navigateTab) window.__navigateTab('players', 'college'); }}
                                        className="text-xs bg-white/20 hover:bg-white/30 px-2 py-0.5 rounded text-white">Pre-MLB Stats →</button>
                                )}
                            </div>
                            <button onClick={() => setSelectedPlayer(null)} className="text-white hover:text-slate-200 text-2xl leading-none">&times;</button>
                        </div>
                        <div className="overflow-y-auto p-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>
                            <PlayerTimeline
                                playerId={selectedPlayer.id}
                                playerName={selectedPlayer.name}
                                playerGames={playerGames}
                                careerMilestones={(careerFirstsByPlayer || {})[selectedPlayer.id] || []}
                                allTimePassings={(allTimePassings || []).filter(p => p.player_id === selectedPlayer.id)}
                                gameMilestones={(milestones || []).filter(m => m.playerId === selectedPlayer.id)}
                                debuts={(debuts || []).filter(d => d.playerId === selectedPlayer.id)}
                                finalGames={(finalGames || []).filter(f => f.playerId === selectedPlayer.id)}
                                onGameClick={(gameId) => {
                                    window._pendingGameId = gameId;
                                    if (window.__navigateTab) window.__navigateTab('gamelog');
                                }}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const DynamicPitcherTable = ({ allPitchers, pitcherGames, ncaaCrossRef, careerFirstsByPlayer, allTimePassings, milestones, debuts, finalGames }) => {
    const [search, setSearch] = useState('');
    const [sortKey, setSortKey] = useState('ip');
    const [sortDir, setSortDir] = useState('desc');
    const [activeFilter, setActiveFilter] = useState('all');
    const [gameTypeFilter, setGameTypeFilter] = useState('regular');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [useFiltered, setUseFiltered] = useState(false);
    const [selectedPitcher, setSelectedPitcher] = useState(null);

    // Check for pending player selection (from search)
    useEffect(() => {
        if (window._pendingPlayerSelect) {
            const pid = window._pendingPlayerSelect.id;
            if (allPitchers.some(p => p.playerId === pid)) {
                setSelectedPitcher(window._pendingPlayerSelect);
                window._pendingPlayerSelect = null;
            }
        }
    });

    useEffect(() => { setUseFiltered(!!(startDate || endDate)); }, [startDate, endDate]);

    // Map game type to stat prefixes
    const getStatKey = (baseKey, gameType) => {
        if (gameType === 'all') return baseKey;
        const prefixMap = {
            'spring': 'spring',
            'regular': 'regular',
            'postseason': 'postseason'
        };
        const keyMap = {
            'games': 'Games', 'gameStarts': 'Gs', 'wins': 'W', 'losses': 'L',
            'saves': 'Sv', 'ip': 'Ip', 'era': 'Era', 'h': 'H', 'er': 'Er',
            'bb': 'Bb', 'so': 'So', 'team': 'Team'
        };
        return prefixMap[gameType] + (keyMap[baseKey] || baseKey.charAt(0).toUpperCase() + baseKey.slice(1));
    };

    // Filter pitcherGames by game type and date, then aggregate
    const gameTypeData = useMemo(() => {
        let games = pitcherGames;
        if (gameTypeFilter !== 'all') {
            games = games.filter(g => (g.gameType || 'regular') === gameTypeFilter);
        }
        if (useFiltered) {
            if (startDate) games = games.filter(g => g.dateSort >= startDate);
            if (endDate) games = games.filter(g => g.dateSort <= endDate);
        }
        return aggregatePitcherStats(games);
    }, [pitcherGames, gameTypeFilter, startDate, endDate, useFiltered]);

    const filtered = useMemo(() => {
        let result = gameTypeData;
        if (activeFilter !== 'all') result = result.filter(row => row.team.includes(activeFilter));
        if (search) result = result.filter(row => Object.values(row).some(val => String(val).toLowerCase().includes(search.toLowerCase())));
        return result;
    }, [gameTypeData, search, activeFilter]);

    const sorted = useMemo(() => {
        if (!sortKey) return filtered;
        return [...filtered].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal).localeCompare(String(bVal));
            return sortDir === 'asc' ? result : -result;
        });
    }, [filtered, sortKey, sortDir]);

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    const filterValues = useMemo(() => {
        const teams = new Set();
        allPitchers.forEach(p => p.team.split(', ').forEach(t => teams.add(t.trim())));
        return Array.from(teams).sort();
    }, [allPitchers]);

    const columns = [
        {
            key: 'name',
            label: 'Name',
            render: (v, r) => (
                <div className="flex items-center gap-2">
                    <PlayerLink playerId={r.playerId} name={v} external />
                    <button
                        onClick={() => setSelectedPitcher({ id: r.playerId, name: v })}
                        className="px-2 py-1 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded text-xs font-semibold whitespace-nowrap"
                        title="View career timeline"
                    >
                        📊
                    </button>
                </div>
            )
        },
        { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'gameStarts', label: 'GS' },
        { key: 'wins', label: 'W' }, { key: 'losses', label: 'L' }, { key: 'saves', label: 'SV' },
        { key: 'ip', label: 'IP' }, { key: 'h', label: 'H' }, { key: 'r', label: 'R' }, { key: 'er', label: 'ER' },
        { key: 'bb', label: 'BB' }, { key: 'so', label: 'SO' }, { key: 'hr', label: 'HR' },
        { key: 'era', label: 'ERA' }, { key: 'whip', label: 'WHIP' },
        { key: 'maxSpeed', label: 'Max Velo', render: (v) => v ? `${v}` : '-' },
        { key: 'avgSpeed', label: 'Avg Velo', render: (v) => v ? `${v}` : '-' },
        { key: 'avgSpinRate', label: 'Avg Spin', render: (v) => v ? `${v}` : '-' },
    ];

    const gameTypeLabels = { all: 'All Games', spring: 'Spring Training', regular: 'Regular Season', postseason: 'Postseason' };

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="section-title font-bold">⚾ Pitcher Statistics {gameTypeFilter !== 'all' && <span className="small-text text-green-600">({gameTypeLabels[gameTypeFilter]})</span>} {useFiltered && <span className="small-text text-blue-600">(Date Filtered)</span>}</h2>
                    <div className="flex items-center gap-2">
                        <span className="body-text text-slate-500">{sorted.length} pitchers</span>
                        <button onClick={() => exportToCSV(sorted, columns, 'Pitcher_Statistics.csv')} className="px-3 py-1 bg-green-600 text-white body-text rounded hover:bg-green-700">📥 Export</button>
                    </div>
                </div>
                <div className="flex flex-wrap gap-4">
                    <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1 min-w-[200px] px-4 py-2 body-text border rounded-lg" />
                    <select value={gameTypeFilter} onChange={(e) => setGameTypeFilter(e.target.value)} className="px-4 py-2 body-text border rounded-lg bg-green-50">
                        <option value="all">All Games</option>
                        <option value="regular">Regular Season</option>
                        <option value="spring">Spring Training</option>
                        <option value="postseason">Postseason</option>
                    </select>
                    <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="px-4 py-2 body-text border rounded-lg" />
                    <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="px-4 py-2 body-text border rounded-lg" />
                    {(startDate || endDate) && <button onClick={() => { setStartDate(''); setEndDate(''); }} className="px-3 py-2 body-text text-slate-600 hover:text-slate-900">Clear Dates</button>}
                    <select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)} className="px-4 py-2 body-text border rounded-lg">
                        <option value="all">All Teams</option>
                        {filterValues.map(val => <option key={val} value={val}>{val}</option>)}
                    </select>
                </div>
                {useFiltered && <div className="bg-yellow-50 border border-yellow-200 rounded p-3"><p className="body-text text-yellow-900">⚡ Stats recalculated for selected date range</p></div>}
            </div>
            <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="w-full">
                    <thead className="bg-slate-50 sticky top-0">
                        <tr>{columns.map(col => <th key={col.key} onClick={() => handleSort(col.key)} className="px-4 py-3 text-left small-text font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100">{col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y">
                        {sorted.map((row) => (
                            <tr key={row.playerId} className="hover:bg-blue-50">
                                {columns.map(col => <td key={col.key} className="px-4 py-3 body-text">{col.render ? col.render(row[col.key], row) : row[col.key]}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {selectedPitcher && (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPitcher(null)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-4xl max-w-[95vw] w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-purple-700 text-white">
                            <div className="flex items-center gap-3">
                                <h3 className="section-title font-bold">{selectedPitcher.name}</h3>
                                {ncaaCrossRef && ncaaCrossRef[selectedPitcher.id] && (
                                    <button onClick={() => { setSelectedPitcher(null); if (window.__navigateTab) window.__navigateTab('players', 'college'); }}
                                        className="text-xs bg-white/20 hover:bg-white/30 px-2 py-0.5 rounded text-white">Pre-MLB Stats →</button>
                                )}
                            </div>
                            <button onClick={() => setSelectedPitcher(null)} className="text-white hover:text-slate-200 text-2xl leading-none">&times;</button>
                        </div>
                        <div className="overflow-y-auto p-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>
                            <PitcherTimeline
                                playerId={selectedPitcher.id}
                                playerName={selectedPitcher.name}
                                pitcherGames={pitcherGames}
                                careerMilestones={(careerFirstsByPlayer || {})[selectedPitcher.id] || []}
                                allTimePassings={(allTimePassings || []).filter(p => p.player_id === selectedPitcher.id)}
                                gameMilestones={(milestones || []).filter(m => m.playerId === selectedPitcher.id)}
                                debuts={(debuts || []).filter(d => d.playerId === selectedPitcher.id)}
                                finalGames={(finalGames || []).filter(f => f.playerId === selectedPitcher.id)}
                                onGameClick={(gameId) => {
                                    window._pendingGameId = gameId;
                                    if (window.__navigateTab) window.__navigateTab('gamelog');
                                }}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const DataTable = ({ data, columns, title, defaultSortKey = null, filterOptions = null, enableDateFilter = false, enableExport = true, paginate = true, onRowClick = null, persistKey = null }) => {
    const loadPersisted = (key, fallback) => {
        if (!persistKey) return fallback;
        try { const v = JSON.parse(localStorage.getItem(`dt_${persistKey}_${key}`)); return v !== null ? v : fallback; } catch { return fallback; }
    };
    const [search, setSearch] = useState(() => loadPersisted('search', ''));
    const [sortKey, setSortKey] = useState(() => loadPersisted('sortKey', defaultSortKey || columns[0]?.key));
    const [sortDir, setSortDir] = useState(() => loadPersisted('sortDir', 'desc'));
    const [activeFilters, setActiveFilters] = useState(() => loadPersisted('filters', {}));
    const [startDate, setStartDate] = useState(() => loadPersisted('startDate', ''));
    const [endDate, setEndDate] = useState(() => loadPersisted('endDate', ''));

    useEffect(() => {
        if (!persistKey) return;
        const state = { search, sortKey, sortDir, filters: activeFilters, startDate, endDate };
        Object.entries(state).forEach(([k, v]) => localStorage.setItem(`dt_${persistKey}_${k}`, JSON.stringify(v)));
    }, [search, sortKey, sortDir, activeFilters, startDate, endDate, persistKey]);

    // Normalize filterOptions to always be an array
    const filters = useMemo(() => {
        if (!filterOptions) return [];
        return Array.isArray(filterOptions) ? filterOptions : [filterOptions];
    }, [filterOptions]);

    const filtered = useMemo(() => {
        let result = data;
        // Apply all active filters
        filters.forEach(filter => {
            const activeValue = activeFilters[filter.key];
            if (activeValue && activeValue !== 'all') {
                result = result.filter(row => row[filter.key] === activeValue);
            }
        });
        if (enableDateFilter && (startDate || endDate)) {
            result = result.filter(row => {
                const rowDate = new Date(row.date);
                if (isNaN(rowDate)) return true;
                if (startDate && rowDate < new Date(startDate)) return false;
                if (endDate && rowDate > new Date(endDate)) return false;
                return true;
            });
        }
        if (search) result = result.filter(row => Object.values(row).some(val => String(val).toLowerCase().includes(search.toLowerCase())));
        return result;
    }, [data, search, activeFilters, startDate, endDate, filters]);

    const sorted = useMemo(() => {
        if (!sortKey) return filtered;
        const dateToSort = (v) => { if (!v) return ''; const p = String(v).split('/'); return p.length === 3 ? `${p[2]}${p[0].padStart(2,'0')}${p[1].padStart(2,'0')}` : v; };
        return [...filtered].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            // Detect date columns (MM/DD/YYYY format)
            if (String(aVal).match(/^\d{1,2}\/\d{1,2}\/\d{4}$/) || String(bVal).match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
                const result = dateToSort(aVal).localeCompare(dateToSort(bVal));
                return sortDir === 'asc' ? result : -result;
            }
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal).localeCompare(String(bVal));
            return sortDir === 'asc' ? result : -result;
        });
    }, [filtered, sortKey, sortDir]);

    const { page, setPage, totalPages, paginatedData, totalItems } = usePagination(sorted, 50);
    const displayData = paginate ? paginatedData : sorted;

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    const handleFilterChange = (key, value) => {
        setActiveFilters(prev => ({ ...prev, [key]: value }));
    };

    // Get filter values for each filter
    const filterValuesMap = useMemo(() => {
        const map = {};
        filters.forEach(filter => {
            map[filter.key] = [...new Set(data.map(row => row[filter.key]).filter(v => v))].sort();
        });
        return map;
    }, [data, filters]);

    const hasActiveFilters = Object.values(activeFilters).some(v => v && v !== 'all') || startDate || endDate;

    return (
        <div className="bg-white rounded-lg border border-slate-200" style={{ boxShadow: 'var(--shadow)' }}>
            <div className="p-4 border-b border-slate-100 space-y-3">
                <div className="flex justify-between items-center">
                    <h2 className="section-title font-semibold text-slate-800">{title}</h2>
                    <div className="flex items-center gap-2">
                        <span className="small-text text-slate-400">{sorted.length} of {data.length}</span>
                        {enableExport && <>
                            <button onClick={() => exportToCSV(sorted, columns, `${title.replace(/[^a-z0-9]/gi, '_')}.csv`)} className="px-2.5 py-1 bg-slate-100 text-slate-600 small-text rounded hover:bg-slate-200 font-medium">CSV</button>
                            <button onClick={() => exportToJSON(sorted, `${title.replace(/[^a-z0-9]/gi, '_')}.json`)} className="px-2.5 py-1 bg-slate-100 text-slate-600 small-text rounded hover:bg-slate-200 font-medium">JSON</button>
                        </>}
                    </div>
                </div>
                <div className="flex flex-wrap gap-3">
                    <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1 min-w-[200px] px-3 py-1.5 body-text border border-slate-200 rounded-lg focus:border-blue-500 focus:outline-none" />
                    {enableDateFilter && (
                        <>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="px-4 py-2 body-text border rounded-lg" />
                            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="px-4 py-2 body-text border rounded-lg" />
                        </>
                    )}
                    {filters.map(filter => (
                        <select
                            key={filter.key}
                            value={activeFilters[filter.key] || 'all'}
                            onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                            className="px-4 py-2 body-text border rounded-lg"
                        >
                            <option value="all">All {filter.label}</option>
                            {(filterValuesMap[filter.key] || []).map(val => (
                                <option key={val} value={val}>{filter.displayFn ? filter.displayFn(val) : val}</option>
                            ))}
                        </select>
                    ))}
                    {hasActiveFilters && (
                        <button
                            onClick={() => { setActiveFilters({}); setStartDate(''); setEndDate(''); }}
                            className="px-3 py-2 body-text text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded"
                        >
                            Clear filters
                        </button>
                    )}
                </div>
            </div>
            {paginate && <PaginationControls page={page} setPage={setPage} totalPages={totalPages} totalItems={totalItems} />}
            <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="w-full">
                    <thead className="bg-slate-50 sticky top-0">
                        <tr>{columns.map(col => <th key={col.key} onClick={() => handleSort(col.key)} aria-sort={sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'} className="px-4 py-3 text-left small-text font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100">{col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y">
                        {displayData.map((row, idx) => (
                            <tr key={row.gameId || row.id || `item-${idx}`} className={`hover:bg-blue-50 ${idx % 2 === 1 ? 'bg-slate-50/50' : ''} ${onRowClick ? 'cursor-pointer' : ''}`} onClick={() => onRowClick && onRowClick(row)}>
                                {columns.map(col => <td key={col.key} className="px-4 py-3 body-text">{col.render ? col.render(row[col.key], row) : row[col.key]}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {paginate && <PaginationControls page={page} setPage={setPage} totalPages={totalPages} totalItems={totalItems} />}
        </div>
    );
};

const Leaderboards = ({ data }) => {
    const [category, setCategory] = useState('batting');
    // Auto-calculate reasonable minimums: ~2 AB per game attended, ~0.5 IP per game
    const autoMinAB = useMemo(() => Math.max(10, Math.round((data.games?.length || 50) * 0.4)), [data.games]);
    const autoMinIP = useMemo(() => Math.max(5, Math.round((data.games?.length || 50) * 0.2)), [data.games]);
    const [minAB, setMinAB] = useState(autoMinAB);
    const [minIP, setMinIP] = useState(autoMinIP);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [useFiltered, setUseFiltered] = useState(false);
    
    useEffect(() => { setUseFiltered(!!(startDate || endDate)); }, [startDate, endDate]);
    
    const playersData = useMemo(() => {
        if (!useFiltered || (!startDate && !endDate)) return data.players || [];
        const filteredGames = (data.playerGames || []).filter(game => {
            if (startDate && game.dateSort < startDate) return false;
            if (endDate && game.dateSort > endDate) return false;
            return true;
        });
        return aggregateHitterStats(filteredGames);
    }, [data.players, data.playerGames, startDate, endDate, useFiltered]);
    
    const pitchersData = useMemo(() => {
        if (!useFiltered || (!startDate && !endDate)) return data.pitchers || [];
        const filteredGames = (data.pitcherGames || []).filter(game => {
            if (startDate && game.dateSort < startDate) return false;
            if (endDate && game.dateSort > endDate) return false;
            return true;
        });
        return aggregatePitcherStats(filteredGames);
    }, [data.pitchers, data.pitcherGames, startDate, endDate, useFiltered]);
    
    const battingLeaders = useMemo(() => {
        const all = playersData;
        const qualified = all.filter(p => p.ab >= minAB);
        return {
            avg: [...qualified].sort((a, b) => parseFloat(b.avg) - parseFloat(a.avg)).slice(0, 25),
            obp: [...qualified].sort((a, b) => parseFloat(b.obp) - parseFloat(a.obp)).slice(0, 25),
            slg: [...qualified].sort((a, b) => parseFloat(b.slg) - parseFloat(a.slg)).slice(0, 25),
            ops: [...qualified].sort((a, b) => parseFloat(b.ops) - parseFloat(a.ops)).slice(0, 25),
            hr: [...all].sort((a, b) => b.hr - a.hr).slice(0, 25),
            rbi: [...all].sort((a, b) => b.rbi - a.rbi).slice(0, 25),
            hits: [...all].sort((a, b) => b.h - a.h).slice(0, 25),
            runs: [...all].sort((a, b) => b.r - a.r).slice(0, 25),
            sb: [...all].sort((a, b) => b.sb - a.sb).slice(0, 25),
            doubles: [...all].sort((a, b) => b.doubles - a.doubles).slice(0, 25),
        };
    }, [playersData, minAB]);

    const pitchingLeaders = useMemo(() => {
        const all = pitchersData;
        const qualified = all.filter(p => parseFloat(p.ip) >= minIP);
        return {
            era: [...qualified].filter(p => p.era !== 'N/A').sort((a, b) => parseFloat(a.era) - parseFloat(b.era)).slice(0, 25),
            whip: [...qualified].filter(p => p.whip !== 'N/A').sort((a, b) => parseFloat(a.whip) - parseFloat(b.whip)).slice(0, 25),
            wins: [...all].sort((a, b) => b.wins - a.wins).slice(0, 25),
            so: [...all].sort((a, b) => b.so - a.so).slice(0, 25),
            saves: [...all].sort((a, b) => b.saves - a.saves).slice(0, 25),
            ip: [...all].sort((a, b) => parseFloat(b.ip) - parseFloat(a.ip)).slice(0, 25),
        };
    }, [pitchersData, minIP]);
    
    const LeaderCard = ({ title, leaders, stat, isRateStat = false }) => {
        const [expanded, setExpanded] = useState(false);
        const shown = expanded ? leaders : leaders.slice(0, 10);
        return (
            <div className="bg-white rounded-lg border border-slate-200 p-4">
                <h3 className="subsection-title font-bold text-slate-900 mb-1">{title}</h3>
                {isRateStat && <p className="small-text text-blue-600 italic mb-2">Qualified</p>}
                <div className="space-y-2">
                    {shown.map((player, idx) => (
                        <div key={player.playerId} className="flex items-center justify-between py-1 border-b last:border-0">
                            <div className="flex items-center gap-2">
                                <span className="text-slate-500 body-text w-6">{idx + 1}.</span>
                                <PlayerLink playerId={player.playerId} name={player.name} />
                                <span className="small-text text-slate-500">({player.team})</span>
                            </div>
                            <span className="font-bold text-blue-600 body-text">{player[stat]}</span>
                        </div>
                    ))}
                </div>
                {leaders.length > 10 && (
                    <button onClick={() => setExpanded(!expanded)} className="mt-2 w-full text-center small-text text-blue-600 hover:text-blue-800 font-medium py-1">
                        {expanded ? 'Show Top 10' : `View All ${leaders.length}`}
                    </button>
                )}
            </div>
        );
    };
    
    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg border border-slate-200 p-4">
                <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex gap-4">
                        <button onClick={() => setCategory('batting')} className={`px-6 py-2 rounded body-text font-medium ${category === 'batting' ? 'bg-blue-600 text-white' : 'bg-slate-100 hover:bg-slate-200'}`}>Batting</button>
                        <button onClick={() => setCategory('pitching')} className={`px-6 py-2 rounded body-text font-medium ${category === 'pitching' ? 'bg-blue-600 text-white' : 'bg-slate-100 hover:bg-slate-200'}`}>Pitching</button>
                    </div>
                    <div className="flex items-center gap-3">
                        {category === 'batting' && (
                            <label className="flex items-center gap-2 body-text bg-blue-50 px-3 py-2 rounded border">
                                <span className="font-medium">Min AB:</span>
                                <input type="number" value={minAB} onChange={(e) => setMinAB(parseInt(e.target.value) || 0)} className="w-16 px-2 py-1 body-text border rounded" />
                            </label>
                        )}
                        {category === 'pitching' && (
                            <label className="flex items-center gap-2 body-text bg-blue-50 px-3 py-2 rounded border">
                                <span className="font-medium">Min IP:</span>
                                <input type="number" value={minIP} onChange={(e) => setMinIP(parseInt(e.target.value) || 0)} className="w-16 px-2 py-1 body-text border rounded" />
                            </label>
                        )}
                    </div>
                </div>
                <div className="mt-4 pt-4 border-t">
                    <div className="flex flex-wrap items-center gap-4">
                        <label className="flex items-center gap-2 body-text">
                            <span className="font-medium text-slate-700">Date Range:</span>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="px-3 py-2 body-text border rounded-lg" />
                        </label>
                        <span className="text-slate-400">to</span>
                        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="px-3 py-2 body-text border rounded-lg" />
                        {(startDate || endDate) && <button onClick={() => { setStartDate(''); setEndDate(''); }} className="px-3 py-2 body-text text-slate-600 hover:text-slate-900 border rounded-lg hover:bg-slate-50">Clear Dates</button>}
                        {useFiltered && <div className="ml-auto"><span className="px-3 py-2 body-text bg-yellow-100 text-yellow-900 rounded-lg border border-yellow-300">⚡ Stats recalculated for date range</span></div>}
                    </div>
                </div>
            </div>
            {category === 'batting' && (
                <div>
                    <h3 className="subsection-title font-bold mb-4">📊 Rate Stats (Min {minAB} AB)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <LeaderCard title="AVG" leaders={battingLeaders.avg} stat="avg" isRateStat={true} />
                        <LeaderCard title="OBP" leaders={battingLeaders.obp} stat="obp" isRateStat={true} />
                        <LeaderCard title="SLG" leaders={battingLeaders.slg} stat="slg" isRateStat={true} />
                        <LeaderCard title="OPS" leaders={battingLeaders.ops} stat="ops" isRateStat={true} />
                    </div>
                    <h3 className="subsection-title font-bold mb-4">🔢 Counting Stats</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <LeaderCard title="HR" leaders={battingLeaders.hr} stat="hr" />
                        <LeaderCard title="RBI" leaders={battingLeaders.rbi} stat="rbi" />
                        <LeaderCard title="Hits" leaders={battingLeaders.hits} stat="h" />
                        <LeaderCard title="Runs" leaders={battingLeaders.runs} stat="r" />
                        <LeaderCard title="SB" leaders={battingLeaders.sb} stat="sb" />
                        <LeaderCard title="2B" leaders={battingLeaders.doubles} stat="doubles" />
                    </div>
                </div>
            )}
            {category === 'pitching' && (
                <div>
                    <h3 className="subsection-title font-bold mb-4">📊 Rate Stats (Min {minIP} IP)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <LeaderCard title="ERA" leaders={pitchingLeaders.era} stat="era" isRateStat={true} />
                        <LeaderCard title="WHIP" leaders={pitchingLeaders.whip} stat="whip" isRateStat={true} />
                    </div>
                    <h3 className="subsection-title font-bold mb-4">🔢 Counting Stats</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <LeaderCard title="Wins" leaders={pitchingLeaders.wins} stat="wins" />
                        <LeaderCard title="SO" leaders={pitchingLeaders.so} stat="so" />
                        <LeaderCard title="Saves" leaders={pitchingLeaders.saves} stat="saves" />
                        <LeaderCard title="IP" leaders={pitchingLeaders.ip} stat="ip" />
                    </div>
                </div>
            )}
        </div>
    );
};

const MilestonesView = ({ milestones, games, careerFirsts, allTimePassings, onTabChange }) => {
    const [activeCategory, setActiveCategory] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [careerMilestoneSort, setCareerMilestoneSort] = useState('date'); // 'event' or 'date'
    const [viewMode, setViewMode] = useState('date'); // 'date' or 'category'

    // Build game lookup for additional context
    const gameMap = useMemo(() => {
        const map = {};
        (games || []).forEach(g => { if (g.gameId) map[g.gameId] = g; });
        return map;
    }, [games]);

    // Category configurations with icons and colors
    const categoryConfig = {
        'Walk-Offs': { icon: '🎉', color: 'green', category: 'batting' },
        '4+ Hit Games': { icon: '🔥', color: 'orange', category: 'batting' },
        '5+ RBI Games': { icon: '💪', color: 'red', category: 'batting' },
        'Grand Slams': { icon: '💣', color: 'purple', category: 'batting' },
        'Multi-HR Games': { icon: '🚀', color: 'rose', category: 'batting' },
        'Leadoff HRs': { icon: '1️⃣', color: 'blue', category: 'batting' },
        'Inside-the-Park HRs': { icon: '🏃', color: 'emerald', category: 'batting' },
        'Pinch Hit HRs': { icon: '🎯', color: 'amber', category: 'batting' },
        'Golden Sombreros': { icon: '🎩', color: 'slate', category: 'batting' },
        '10+ K Games': { icon: '🔥', color: 'indigo', category: 'pitching' },
        'Quality Starts': { icon: '✅', color: 'green', category: 'pitching' },
        '3 Strikeout Innings': { icon: '⚡', color: 'violet', category: 'pitching' },
        'Immaculate Innings': { icon: '💎', color: 'cyan', category: 'pitching' },
        'Complete Games & Shutouts': { icon: '🛡️', color: 'slate', category: 'pitching' },
        '3 Pitch Innings': { icon: '⏱️', color: 'gray', category: 'pitching' },
        'Consecutive HR Instances': { icon: '🔗', color: 'pink', category: 'team' },
    };

    // Group milestones by type
    const groupedMilestones = useMemo(() => {
        const groups = {};
        (milestones || []).forEach(m => {
            const type = m.type || 'Other';
            if (!groups[type]) groups[type] = [];
            groups[type].push(m);
        });
        // Sort each group by date (most recent first)
        Object.keys(groups).forEach(type => {
            groups[type].sort((a, b) => new Date(b.date) - new Date(a.date));
        });
        return groups;
    }, [milestones]);

    // Get sorted types by count
    const sortedTypes = useMemo(() => {
        return Object.entries(groupedMilestones)
            .sort((a, b) => b[1].length - a[1].length)
            .map(([type]) => type);
    }, [groupedMilestones]);

    // Filter milestones based on category and search
    const filteredTypes = useMemo(() => {
        return sortedTypes.filter(type => {
            if (activeCategory !== 'all') {
                const config = categoryConfig[type];
                if (activeCategory === 'batting' && config?.category !== 'batting') return false;
                if (activeCategory === 'pitching' && config?.category !== 'pitching') return false;
            }
            if (searchTerm) {
                const milestones = groupedMilestones[type] || [];
                return milestones.some(m =>
                    m.player?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    m.team?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    m.detail?.toLowerCase().includes(searchTerm.toLowerCase())
                );
            }
            return true;
        });
    }, [sortedTypes, activeCategory, searchTerm, groupedMilestones]);

    const totalCount = milestones?.length || 0;
    const battingCount = (milestones || []).filter(m => categoryConfig[m.type]?.category === 'batting').length;
    const pitchingCount = (milestones || []).filter(m => categoryConfig[m.type]?.category === 'pitching').length;
    const careerFirstsCount = careerFirsts?.length || 0;
    const allTimePassingsCount = allTimePassings?.length || 0;

    return (
        <div className="space-y-6">
            {/* Header with filters */}
            <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900">🏆 Milestones</h1>
                        <p className="text-slate-500 mt-1">Special performances you've witnessed</p>
                    </div>
                    <div className="flex items-center gap-4">
                        {activeCategory !== 'firsts' && (
                            <div className="flex rounded-lg overflow-hidden border">
                                <button onClick={() => setViewMode('date')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'date' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-100'}`}>📅 By Date</button>
                                <button onClick={() => setViewMode('category')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'category' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-100'}`}>📂 By Category</button>
                            </div>
                        )}
                        <input
                            type="text"
                            placeholder="Search player, team..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="px-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>
                </div>

                {/* Category filters */}
                <div className="flex flex-wrap gap-2 mt-4">
                    {[
                        { id: 'all', label: 'All', count: totalCount + careerFirstsCount },
                        { id: 'firsts', label: '⭐ Career Milestones', count: careerFirstsCount },
                        { id: 'batting', label: '🏏 Batting', count: battingCount },
                        { id: 'pitching', label: '⚾ Pitching', count: pitchingCount },
                    ].map(cat => (
                        <button
                            key={cat.id}
                            onClick={() => setActiveCategory(cat.id)}
                            className={`px-4 py-2 rounded-lg font-semibold text-sm transition-colors ${
                                activeCategory === cat.id
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                            }`}
                        >
                            {cat.label} <span className="ml-1 opacity-75">({cat.count})</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Career Milestones Section */}
            {careerFirsts && careerFirsts.length > 0 && (activeCategory === 'all' || activeCategory === 'firsts') && (
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                    <details open={true}>
                        <summary className="cursor-pointer p-4 bg-gradient-to-r from-yellow-500 to-amber-600 text-white hover:opacity-95 transition-opacity">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">⭐</span>
                                    <h3 className="text-lg font-bold">Career Milestones Witnessed</h3>
                                </div>
                                <span className="bg-white/20 backdrop-blur px-3 py-1 rounded-full text-sm font-bold">
                                    {Object.keys(careerFirsts.reduce((acc, f) => { acc[f.player_id] = true; return acc; }, {})).length} players
                                </span>
                            </div>
                        </summary>
                        <div className="p-4 bg-gradient-to-b from-amber-50 to-white">
                            <div className="flex items-center justify-between mb-4">
                                <p className="text-sm text-amber-700">
                                    You witnessed these players achieve career milestones!
                                </p>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-amber-600">Sort by:</span>
                                    <select
                                        value={careerMilestoneSort}
                                        onChange={(e) => setCareerMilestoneSort(e.target.value)}
                                        className="text-xs px-2 py-1 border border-amber-300 rounded bg-white text-amber-800"
                                    >
                                        <option value="event">Event Type</option>
                                        <option value="date">Date</option>
                                        <option value="player">Player Name</option>
                                    </select>
                                </div>
                            </div>
                            {(() => {
                                // Filter by search
                                const filtered = careerFirsts.filter(f => !searchTerm ||
                                    f.player_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                    f.milestone?.toLowerCase().includes(searchTerm.toLowerCase())
                                );

                                // Get event type from milestone text
                                const getEventType = (m) => {
                                    const text = m.toLowerCase();
                                    if (text.includes('home run')) return { key: 'hr', label: 'Home Runs', icon: '💣', order: 1 };
                                    if (text.includes('hit') && !text.includes('pitch')) return { key: 'hit', label: 'Hits', icon: '🏏', order: 2 };
                                    if (text.includes('rbi')) return { key: 'rbi', label: 'RBIs', icon: '🏃', order: 3 };
                                    if (text.match(/\\brun\\b/) && !text.includes('home run')) return { key: 'run', label: 'Runs Scored', icon: '🏠', order: 4 };
                                    if (text.includes('double')) return { key: '2b', label: 'Doubles', icon: '2️⃣', order: 5 };
                                    if (text.includes('triple')) return { key: '3b', label: 'Triples', icon: '3️⃣', order: 6 };
                                    if (text.includes('stolen base')) return { key: 'sb', label: 'Stolen Bases', icon: '🏃‍♂️', order: 7 };
                                    if (text.includes('walk')) return { key: 'bb', label: 'Walks', icon: '🚶', order: 8 };
                                    if (text.includes('strikeout')) return { key: 'k', label: 'Strikeouts', icon: 'K', order: 9 };
                                    if (text.includes('win')) return { key: 'w', label: 'Wins', icon: '🏆', order: 10 };
                                    if (text.includes('save')) return { key: 'sv', label: 'Saves', icon: '💾', order: 11 };
                                    if (text.includes('inning')) return { key: 'ip', label: 'Innings Pitched', icon: '⚾', order: 12 };
                                    if (text.includes('start')) return { key: 'gs', label: 'Games Started', icon: '📋', order: 13 };
                                    if (text.includes('complete game')) return { key: 'cg', label: 'Complete Games', icon: '💪', order: 14 };
                                    if (text.includes('shutout')) return { key: 'sho', label: 'Shutouts', icon: '🛡️', order: 15 };
                                    if (text.includes('total base')) return { key: 'tb', label: 'Total Bases', icon: '📊', order: 16 };
                                    if (text.includes('game') && !text.includes('complete game')) return { key: 'g', label: 'Games', icon: '🎮', order: 17 };
                                    return { key: 'other', label: 'Other', icon: '⭐', order: 99 };
                                };

                                // Extract milestone number (1st, 100th, 500th, etc.)
                                const getMilestoneNumber = (m) => {
                                    if (m.toLowerCase().includes('first career')) return { num: 1, label: '1st' };
                                    const match = m.match(/#?(\d+)/);
                                    if (match) return { num: parseInt(match[1]), label: `#${match[1]}` };
                                    return { num: 1, label: '1st' };
                                };

                                // Group by event type, then by number
                                const byEventType = {};
                                filtered.forEach(f => {
                                    const event = getEventType(f.milestone);
                                    const milestone = getMilestoneNumber(f.milestone);

                                    if (!byEventType[event.key]) {
                                        byEventType[event.key] = { ...event, numbers: {} };
                                    }
                                    if (!byEventType[event.key].numbers[milestone.num]) {
                                        byEventType[event.key].numbers[milestone.num] = { ...milestone, items: [] };
                                    }
                                    byEventType[event.key].numbers[milestone.num].items.push(f);
                                });

                                // Sort event types by order
                                const sortedEvents = Object.values(byEventType).sort((a, b) => a.order - b.order);

                                // shortenMilestone is now global

                                // DATE VIEW
                                if (careerMilestoneSort === 'date') {
                                    const sortedByDate = [...filtered].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
                                    return (
                                        <div className="space-y-2">
                                            {sortedByDate.map((m, mIdx) => {
                                                const playerUrl = m.player_id
                                                    ? `https://www.baseball-reference.com/players/${m.player_id.charAt(0).toLowerCase()}/${m.player_id}.shtml`
                                                    : null;
                                                const gameUrl = m.game_id
                                                    ? `https://www.baseball-reference.com/boxes/${m.game_id.substring(0, 3)}/${m.game_id}.shtml`
                                                    : null;
                                                const event = getEventType(m.milestone);
                                                return (
                                                    <div key={mIdx} className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                                                        <span className="text-sm font-medium text-amber-600 min-w-[100px]">{m.date_display || m.date}</span>
                                                        <span className="text-lg">{event.icon}</span>
                                                        {playerUrl ? (
                                                            <a href={playerUrl} target="_blank" rel="noopener noreferrer" className="font-medium text-amber-700 hover:text-amber-900 hover:underline">
                                                                {m.player_name}
                                                            </a>
                                                        ) : (
                                                            <span className="font-medium text-slate-800">{m.player_name}</span>
                                                        )}
                                                        <span className="text-sm text-amber-800 font-bold">{shortenMilestone(m.milestone)}</span>
                                                        {m.venue && <span className="text-xs text-slate-500 ml-auto">@ {m.venue}</span>}
                                                        {gameUrl && (
                                                            <a href={gameUrl} target="_blank" rel="noopener noreferrer" className="text-amber-500 hover:text-amber-700">→</a>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    );
                                }

                                // PLAYER VIEW
                                if (careerMilestoneSort === 'player') {
                                    // Group by player name
                                    const byPlayer = {};
                                    filtered.forEach(m => {
                                        const name = m.player_name || 'Unknown';
                                        if (!byPlayer[name]) {
                                            byPlayer[name] = { name, player_id: m.player_id, items: [] };
                                        }
                                        byPlayer[name].items.push(m);
                                    });
                                    // Sort players alphabetically by last name
                                    const sortedPlayers = Object.values(byPlayer).sort((a, b) => getLastName(a.name).toLowerCase().localeCompare(getLastName(b.name).toLowerCase()));
                                    return (
                                        <div className="space-y-3">
                                            {sortedPlayers.map((player, pIdx) => {
                                                const playerUrl = player.player_id
                                                    ? `https://www.baseball-reference.com/players/${player.player_id.charAt(0).toLowerCase()}/${player.player_id}.shtml`
                                                    : null;
                                                return (
                                                    <div key={pIdx} className="border border-amber-200 rounded-lg overflow-hidden">
                                                        <div className="bg-amber-100 px-3 py-2 flex items-center gap-2">
                                                            {playerUrl ? (
                                                                <a href={playerUrl} target="_blank" rel="noopener noreferrer" className="font-bold text-amber-800 hover:text-amber-900 hover:underline">
                                                                    {player.name}
                                                                </a>
                                                            ) : (
                                                                <span className="font-bold text-amber-800">{player.name}</span>
                                                            )}
                                                            <span className="text-xs text-amber-600 ml-auto">{player.items.length} milestone{player.items.length !== 1 ? 's' : ''}</span>
                                                        </div>
                                                        <div className="p-3 bg-white">
                                                            <div className="flex flex-wrap gap-2">
                                                                {player.items
                                                                    .sort((a, b) => (a.date || '').localeCompare(b.date || ''))
                                                                    .map((m, mIdx) => {
                                                                        const event = getEventType(m.milestone);
                                                                        const gameUrl = m.game_id
                                                                            ? `https://www.baseball-reference.com/boxes/${m.game_id.substring(0, 3)}/${m.game_id}.shtml`
                                                                            : null;
                                                                        return (
                                                                            <div key={mIdx} className="flex items-center gap-1 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                                                                                <span>{event.icon}</span>
                                                                                <span className="text-sm font-medium text-amber-800">{shortenMilestone(m.milestone)}</span>
                                                                                <span className="text-xs text-slate-500">({m.date_display || m.date})</span>
                                                                                {gameUrl && (
                                                                                    <a href={gameUrl} target="_blank" rel="noopener noreferrer" className="text-amber-500 hover:text-amber-700 ml-1">→</a>
                                                                                )}
                                                                            </div>
                                                                        );
                                                                    })}
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    );
                                }

                                // EVENT VIEW (default)
                                return (
                                    <div className="space-y-4">
                                        {sortedEvents.map((event, eventIdx) => {
                                            // Sort numbers within each event type
                                            const sortedNumbers = Object.values(event.numbers).sort((a, b) => a.num - b.num);

                                            return (
                                                <div key={eventIdx} className="border border-amber-200 rounded-lg overflow-hidden">
                                                    <div className="bg-amber-100 px-3 py-2 flex items-center gap-2">
                                                        <span>{event.icon}</span>
                                                        <span className="font-bold text-amber-800">{event.label}</span>
                                                        <span className="text-xs text-amber-600 ml-auto">
                                                            {Object.values(event.numbers).reduce((sum, n) => sum + n.items.length, 0)}
                                                        </span>
                                                    </div>
                                                    <div className="p-3 bg-white space-y-2">
                                                        {sortedNumbers.map((numGroup, numIdx) => (
                                                            <div key={numIdx} className="flex flex-wrap items-center gap-2">
                                                                <span className="text-sm font-bold text-amber-700 min-w-[40px]">{numGroup.label}</span>
                                                                {numGroup.items
                                                                    .sort((a, b) => (a.date || '').localeCompare(b.date || ''))
                                                                    .map((m, mIdx) => {
                                                                        const playerUrl = m.player_id
                                                                            ? `https://www.baseball-reference.com/players/${m.player_id.charAt(0).toLowerCase()}/${m.player_id}.shtml`
                                                                            : null;
                                                                        const gameUrl = m.game_id
                                                                            ? `https://www.baseball-reference.com/boxes/${m.game_id.substring(0, 3)}/${m.game_id}.shtml`
                                                                            : null;
                                                                        return (
                                                                            <div key={mIdx} className="inline-flex items-center gap-1 bg-amber-50 border border-amber-200 rounded px-2 py-0.5 text-sm">
                                                                                {playerUrl ? (
                                                                                    <a href={playerUrl} target="_blank" rel="noopener noreferrer" className="font-medium text-amber-700 hover:text-amber-900 hover:underline">
                                                                                        {m.player_name}
                                                                                    </a>
                                                                                ) : (
                                                                                    <span className="font-medium text-slate-800">{m.player_name}</span>
                                                                                )}
                                                                                <span className="text-xs text-slate-500">({m.date_display || m.date})</span>
                                                                                {gameUrl && (
                                                                                    <a href={gameUrl} target="_blank" rel="noopener noreferrer" className="text-amber-500 hover:text-amber-700">→</a>
                                                                                )}
                                                                            </div>
                                                                        );
                                                                    })}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                );
                            })()}
                        </div>
                    </details>
                </div>
            )}

            {/* All-Time List Passings Section */}
            {/* Date view - flat chronological list */}
            {viewMode === 'date' && activeCategory !== 'firsts' && (() => {
                const allFiltered = (milestones || []).filter(m => {
                    if (activeCategory === 'batting' && categoryConfig[m.type]?.category !== 'batting') return false;
                    if (activeCategory === 'pitching' && categoryConfig[m.type]?.category !== 'pitching') return false;
                    if (searchTerm) {
                        const q = searchTerm.toLowerCase();
                        return (m.player || '').toLowerCase().includes(q) || (m.type || '').toLowerCase().includes(q) || (m.detail || '').toLowerCase().includes(q);
                    }
                    return true;
                }).sort((a, b) => {
                    // Sort by game date from gameMap, falling back to gameId parsing
                    const gameA = gameMap[a.gameId];
                    const gameB = gameMap[b.gameId];
                    const parseDate = toSortableDate;
                    const da = gameA ? parseDate(gameA.date) : '';
                    const db = gameB ? parseDate(gameB.date) : '';
                    return db.localeCompare(da);
                });

                return (
                    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                        <div className="p-4 border-b bg-slate-50">
                            <span className="font-bold body-text">{allFiltered.length} milestones</span>
                        </div>
                        <div className="divide-y" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                            {allFiltered.map((m, i) => {
                                const config = categoryConfig[m.type] || {};
                                const game = gameMap[m.gameId];
                                return (
                                    <div key={`${m.gameId}-${m.type}-${m.player}-${i}`} className="p-3 hover:bg-slate-50 flex items-start gap-3">
                                        <span className="text-lg">{config.icon || '🏆'}</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="font-semibold text-sm">{m.player}</span>
                                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium bg-${config.color || 'gray'}-100 text-${config.color || 'gray'}-700`}>{m.type}</span>
                                            </div>
                                            {m.detail && <div className="text-xs text-slate-600 mt-0.5 truncate">{m.detail}</div>}
                                        </div>
                                        <div className="text-right flex-shrink-0">
                                            <div className="text-xs text-slate-500">{game?.date || ''}</div>
                                            <div className="text-[10px] text-slate-400">{game?.awayTeam || ''} @ {game?.homeTeam || ''}</div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                );
            })()}

            {/* Milestone groups - category view */}
            {viewMode === 'category' && activeCategory !== 'firsts' && (
            <div className="space-y-4">
                {filteredTypes.map(type => {
                    const items = groupedMilestones[type] || [];
                    const config = categoryConfig[type] || { icon: '⭐', color: 'gray' };

                    // Filter items by search if active
                    let filteredItems = searchTerm
                        ? items.filter(m =>
                            m.player?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            m.team?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            m.detail?.toLowerCase().includes(searchTerm.toLowerCase())
                        )
                        : [...items];

                    // Special sorting for Multi-HR Games: by HR count (descending) then date (descending)
                    if (type === 'Multi-HR Games') {
                        // getHrCount is now global
                        filteredItems.sort((a, b) => {
                            const hrDiff = getHrCount(b.detail) - getHrCount(a.detail);
                            if (hrDiff !== 0) return hrDiff;
                            return new Date(b.date) - new Date(a.date);
                        });
                    }

                    if (filteredItems.length === 0) return null;

                    return (
                        <div key={type} className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                            <details open={filteredItems.length <= 10}>
                                <summary className={`cursor-pointer p-4 bg-gradient-to-r from-${config.color}-500 to-${config.color}-600 text-white hover:opacity-95 transition-opacity`}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <span className="text-2xl">{config.icon}</span>
                                            <h3 className="text-lg font-bold">{type}</h3>
                                        </div>
                                        <span className="bg-white/20 backdrop-blur px-3 py-1 rounded-full text-sm font-bold">
                                            {filteredItems.length}
                                        </span>
                                    </div>
                                </summary>
                                <div className="p-4 bg-slate-50">
                                    {/* Special grouped rendering for Multi-HR Games */}
                                    {type === 'Multi-HR Games' ? (() => {
                                        const getHrCount = (detail) => {
                                            const match = detail?.match(/(\d+)\s*HR/);
                                            return match ? parseInt(match[1], 10) : 0;
                                        };
                                        // Group by HR count
                                        const hrGroups = {};
                                        filteredItems.forEach(m => {
                                            const count = getHrCount(m.detail);
                                            if (!hrGroups[count]) hrGroups[count] = [];
                                            hrGroups[count].push(m);
                                        });
                                        // Sort groups by HR count descending
                                        const sortedCounts = Object.keys(hrGroups).map(Number).sort((a, b) => b - a);

                                        return (
                                            <div className="space-y-4">
                                                {sortedCounts.map(hrCount => (
                                                    <div key={hrCount}>
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <span className="text-lg font-bold text-rose-600">{hrCount} HR</span>
                                                            <span className="text-sm text-slate-500">({hrGroups[hrCount].length})</span>
                                                        </div>
                                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                                            {hrGroups[hrCount]
                                                                .sort((a, b) => new Date(b.date) - new Date(a.date))
                                                                .map((m, idx) => {
                                                                const game = gameMap[m.gameId];
                                                                const url = m.gameId && m.gameId !== 'UNKNOWN'
                                                                    ? `https://www.baseball-reference.com/boxes/${m.gameId.substring(0, 3)}/${m.gameId}.shtml`
                                                                    : null;
                                                                return (
                                                                    <div key={`${m.gameId}-${m.playerId}-${m.type}`} className="bg-white rounded-lg p-3 border border-slate-200 hover:border-rose-300 hover:shadow transition-all">
                                                                        <div className="flex items-start justify-between gap-2">
                                                                            <div className="flex-1 min-w-0">
                                                                                <div className="flex items-center gap-2 mb-1">
                                                                                    {m.playerId && m.playerId !== 'UNKNOWN' ? (
                                                                                        <a
                                                                                            href={`https://www.baseball-reference.com/players/${m.playerId.charAt(0).toLowerCase()}/${m.playerId}.shtml`}
                                                                                            target="_blank"
                                                                                            rel="noopener noreferrer"
                                                                                            className="font-bold text-blue-600 hover:text-blue-800 hover:underline"
                                                                                        >
                                                                                            {m.player}
                                                                                        </a>
                                                                                    ) : (
                                                                                        <span className="font-bold text-slate-900">{m.player || 'Team'}</span>
                                                                                    )}
                                                                                    <span className="text-xs px-2 py-0.5 rounded bg-rose-100 text-rose-700 font-semibold">
                                                                                        {m.team}
                                                                                    </span>
                                                                                </div>
                                                                                {m.detail && (
                                                                                    <p className="text-xs text-slate-600 mb-1 line-clamp-2">{m.detail}</p>
                                                                                )}
                                                                                <div className="flex items-center gap-2 text-xs text-slate-500">
                                                                                    <span>{m.date}</span>
                                                                                    {game && <span>vs {game.awayTeam === m.team ? game.homeTeam : game.awayTeam}</span>}
                                                                                </div>
                                                                            </div>
                                                                            {url && (
                                                                                <a
                                                                                    href={url}
                                                                                    target="_blank"
                                                                                    rel="noopener noreferrer"
                                                                                    className="text-blue-500 hover:text-blue-700 text-sm"
                                                                                    title="View game"
                                                                                >
                                                                                    →
                                                                                </a>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        );
                                    })() : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                        {filteredItems.slice(0, 30).map((m, idx) => {
                                            const game = gameMap[m.gameId];
                                            const url = m.gameId && m.gameId !== 'UNKNOWN'
                                                ? `https://www.baseball-reference.com/boxes/${m.gameId.substring(0, 3)}/${m.gameId}.shtml`
                                                : null;

                                            return (
                                                <div key={`${m.gameId}-${m.playerId}-${m.type}`} className="bg-white rounded-lg p-3 border border-slate-200 hover:border-blue-300 hover:shadow transition-all">
                                                    <div className="flex items-start justify-between gap-2">
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-2 mb-1">
                                                                {m.playerId && m.playerId !== 'UNKNOWN' ? (
                                                                    <a
                                                                        href={`https://www.baseball-reference.com/players/${m.playerId.charAt(0).toLowerCase()}/${m.playerId}.shtml`}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="font-bold text-blue-600 hover:text-blue-800 hover:underline"
                                                                    >
                                                                        {m.player}
                                                                    </a>
                                                                ) : (
                                                                    <span className="font-bold text-slate-900">{m.player || 'Team'}</span>
                                                                )}
                                                                <span className={`text-xs px-2 py-0.5 rounded bg-${config.color}-100 text-${config.color}-700 font-semibold`}>
                                                                    {m.team}
                                                                </span>
                                                            </div>
                                                            {m.detail && (
                                                                <p className="text-xs text-slate-600 mb-1 line-clamp-2">{m.detail}</p>
                                                            )}
                                                            <div className="flex items-center gap-2 text-xs text-slate-500">
                                                                <span>{m.date}</span>
                                                                {game && <span>vs {game.awayTeam === m.team ? game.homeTeam : game.awayTeam}</span>}
                                                            </div>
                                                        </div>
                                                        {url && (
                                                            <a
                                                                href={url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="text-blue-500 hover:text-blue-700 text-sm"
                                                                title="View game"
                                                            >
                                                                →
                                                            </a>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    )}
                                    {filteredItems.length > 30 && type !== 'Multi-HR Games' && (
                                        <p className="text-center text-sm text-slate-500 mt-3">
                                            +{filteredItems.length - 30} more {type.toLowerCase()}
                                        </p>
                                    )}
                                </div>
                            </details>
                        </div>
                    );
                })}
            </div>
            )}
        </div>
    );
};

const CollegePlayersView = ({ data, onViewPlayer }) => {
    const ncaaRef = data.ncaaCrossRef || {};
    const allPlayers = useMemo(() => {
        const seen = new Set();
        return [...(data.players || []), ...(data.pitchers || [])].filter(p => { if (seen.has(p.playerId)) return false; seen.add(p.playerId); return true; });
    }, [data.players, data.pitchers]);
    const { seenPlayers, notSeenPlayers } = useMemo(() => {
        const matched = [];
        const seen = new Set();
        const buildPlayerRow = (ncaa, overrides = {}) => {
            const ncaaStats = ncaa.ncaa_stats || {};
            const proStats = ncaa.pro_stats || {};
            const hasNCAA = (ncaaStats.G || 0) > 0;
            const stats = hasNCAA ? ncaaStats : proStats;
            const ncaaTeams = (ncaa.ncaa_teams || []).join(', ');
            const proTeams = (ncaa.pro_teams || []).join(', ');
            const rawLevels = (ncaa.levels || []);
            const hasNCAALevel = rawLevels.includes('NCAA');
            const levels = overrides.seenInMlb && !rawLevels.includes('MLB') ? [...rawLevels, 'MLB'] : rawLevels;
            const isPitcher = stats.is_pitcher || false;
            return {
                college: ncaaTeams || (hasNCAALevel ? 'Unknown' : '—'),
                proTeam: proTeams || '—',
                levels: levels.join(', '),
                source: hasNCAA ? 'NCAA' : 'MiLB',
                G: stats.G || 0,
                isPitcher,
                // Batting stats
                AB: isPitcher ? null : (stats.AB || 0),
                H: isPitcher ? null : (stats.H || 0),
                HR: isPitcher ? null : (stats.HR || 0),
                AVG: isPitcher ? null : (stats.AVG || '.000'),
                // Pitching stats
                IP: isPitcher ? (stats.IP_display || '0.0') : null,
                K: isPitcher ? (stats.K || 0) : null,
                ER: isPitcher ? (stats.ER || 0) : null,
                // Display column: show relevant stats inline
                statLine: isPitcher
                    ? `${stats.IP_display || '0.0'} IP, ${stats.H || 0} H, ${stats.R || 0} R, ${stats.ER || 0} ER, ${stats.BB || 0} BB, ${stats.K || 0} K`
                    : `${stats.H || 0}-${stats.AB || 0}, ${stats.R || 0} R, ${stats.RBI || 0} RBI, ${stats.HR || 0} HR, ${stats.BB || 0} BB, ${stats.K || 0} K`,
                websiteUrl: ncaa.website_url || '',
                ...overrides,
            };
        };

        // Players seen in both college/MiLB and MLB games
        const usedEntries = new Set();
        allPlayers.forEach(p => {
            const pid = p.playerId;
            const ncaa = pid && ncaaRef[pid];
            if (ncaa && !seen.has(pid) && !usedEntries.has(ncaa)) {
                seen.add(pid);
                usedEntries.add(ncaa);
                if (ncaa.mlb_bref_id) seen.add(ncaa.mlb_bref_id);
                matched.push(buildPlayerRow(ncaa, {
                    name: p.name,
                    playerId: pid,
                    mlbTeam: p.team,
                    seenInMlb: true,
                }));
            }
        });
        // College/MiLB players who reached MLB but weren't at user's MLB games
        const notSeen = [];
        Object.entries(ncaaRef).forEach(([key, ncaa]) => {
            if (seen.has(key) || usedEntries.has(ncaa)) return;
            const levels = ncaa.levels || [];
            if (!levels.includes('MLB') || (!levels.includes('NCAA') && !levels.includes('MiLB'))) return;
            if (ncaa.seen_in_mlb) return;
            const mlbBrefId = ncaa.mlb_bref_id || '';
            if (seen.has(mlbBrefId)) return;
            seen.add(key);
            usedEntries.add(ncaa);
            if (mlbBrefId) seen.add(mlbBrefId);
            notSeen.push(buildPlayerRow(ncaa, {
                name: ncaa.name || key,
                playerId: mlbBrefId,
                seenInMlb: false,
            }));
        });
        return {
            seenPlayers: matched.sort((a, b) => {
                if (a.source !== b.source) return a.source === 'NCAA' ? -1 : 1;
                return b.G - a.G;
            }),
            notSeenPlayers: notSeen.sort((a, b) => (a.name || '').localeCompare(b.name || '')),
        };
    }, [allPlayers, ncaaRef]);

    if (Object.keys(ncaaRef).length === 0) {
        return <EmptyState icon="🎓" title="No College/MiLB Data" message="Run the NCAA processor with --export-players to generate cross-reference data." />;
    }
    if (seenPlayers.length === 0 && notSeenPlayers.length === 0) {
        return <EmptyState icon="🎓" title="No Matches" message="No players in your games were found in the college/minor league data." />;
    }

    return (
        <div className="space-y-6">
            {seenPlayers.length > 0 && (
                <DataTable
                    title={`🎓 Seen Pre-MLB & in MLB (${seenPlayers.length} players)`}
                    data={seenPlayers}
                    defaultSortKey="G"
                    columns={[
                        { key: 'name', label: 'Player', render: (v, r) => (
                            <div className="flex items-center gap-2">
                                {onViewPlayer && r.playerId ? (
                                    <button onClick={() => onViewPlayer(r.playerId, v)} className="text-blue-600 hover:underline text-left">{v}</button>
                                ) : (
                                    <PlayerLink playerId={r.playerId} name={v} />
                                )}
                                <a href={`https://www.baseball-reference.com/players/${(r.playerId || '').charAt(0).toLowerCase()}/${r.playerId}.shtml`} target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-slate-600 text-xs" title="View on Baseball Reference">↗</a>
                            </div>
                        )},
                        { key: 'mlbTeam', label: 'MLB Team' },
                        { key: 'college', label: 'College' },
                        { key: 'proTeam', label: 'MiLB Team' },
                        { key: 'levels', label: 'Levels' },
                        { key: 'source', label: 'Stats From', render: (v) => (
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${v === 'NCAA' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}`}>{v}</span>
                        )},
                        { key: 'G', label: 'G' },
                        { key: 'statLine', label: 'Pre-MLB Stats', render: (v, r) => (
                            <span className="font-mono text-sm">{v}</span>
                        )},
                        { key: 'websiteUrl', label: '', render: (v) => v ? <a href={v} target="_blank" rel="noopener noreferrer" className="text-green-600 hover:text-green-800 small-text font-medium">View on NCAA site →</a> : null },
                    ]}
                />
            )}
            {notSeenPlayers.length > 0 && (
                <DataTable
                    title={`🎓 Saw Pre-MLB, Now in MLB (${notSeenPlayers.length} players)`}
                    data={notSeenPlayers}
                    defaultSortKey="name"
                    defaultSortDirection="asc"
                    columns={[
                        { key: 'name', label: 'Player', render: (v, r) => r.playerId ? <PlayerLink playerId={r.playerId} name={v} /> : v },
                        { key: 'college', label: 'College' },
                        { key: 'proTeam', label: 'MiLB Team' },
                        { key: 'levels', label: 'Levels' },
                        { key: 'source', label: 'Stats From', render: (v) => (
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${v === 'NCAA' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}`}>{v}</span>
                        )},
                        { key: 'G', label: 'G' },
                        { key: 'statLine', label: 'Pre-MLB Stats', render: (v, r) => (
                            <span className="font-mono text-sm">{v}</span>
                        )},
                        { key: 'websiteUrl', label: '', render: (v) => v ? <a href={v} target="_blank" rel="noopener noreferrer" className="text-green-600 hover:text-green-800 small-text font-medium">View on NCAA site →</a> : null },
                    ]}
                />
            )}
        </div>
    );
};

const NoStatsPlayers = ({ data }) => {
    const [selectedPlayer, setSelectedPlayer] = useState(null);

    // Players who appeared in regular season games but had no batting/pitching stats
    const allNoStats = useMemo(() => {
        const gameMap = {};
        (data.games || []).forEach(g => { if (g.gameId) gameMap[g.gameId] = g; });

        // Filter to only players who appeared in at least one regular season game
        return (data.playersWithoutStats || []).map(p => {
            const gameIds = (p.gameIds || '').split(',').map(id => id.trim()).filter(Boolean);
            const gameList = gameIds.map(id => gameMap[id]).filter(Boolean);
            const regGames = gameList.filter(g => (g.gameType || 'regular') === 'regular');
            return { ...p, gameList: regGames, regGameCount: regGames.length };
        }).filter(p => p.regGameCount > 0);
    }, [data]);

    return (
        <div className="space-y-4">
            <DataTable
                title={`👻 Players Without Regular Season Stats (${allNoStats.length})`}
                data={allNoStats}
                defaultSortKey="regGameCount"
                onRowClick={(row) => setSelectedPlayer(selectedPlayer?.playerId === row.playerId ? null : row)}
                columns={[
                    { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                    { key: 'teams', label: 'Team(s)' },
                    { key: 'regGameCount', label: 'Games' },
                    { key: 'positions', label: 'Position(s)' },
                ]}
            />
            {selectedPlayer && selectedPlayer.gameList && selectedPlayer.gameList.length > 0 && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPlayer(null)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-md w-full max-h-[70vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b bg-slate-700 text-white rounded-t-lg flex items-center justify-between">
                            <h3 className="font-bold">{selectedPlayer.name} — {selectedPlayer.gameList.length} game{selectedPlayer.gameList.length > 1 ? 's' : ''}</h3>
                            <button onClick={() => setSelectedPlayer(null)} className="text-white hover:text-slate-200 text-xl leading-none">&times;</button>
                        </div>
                        <div className="p-3 space-y-2">
                            {selectedPlayer.gameList.map((g, i) => (
                                <div key={i} className="bg-slate-50 rounded p-3">
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium text-sm">{g.awayTeam} @ {g.homeTeam}</span>
                                        <span className="text-xs text-slate-500">{g.date}</span>
                                    </div>
                                    <div className="text-xs text-slate-400 mt-1">{g.score} • {g.venue || ''}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// PlayersTab removed - replaced by PlayersTabV2 in merged tab wrappers

const HistoryWitnessedView = ({ allTimePassings, careerFirsts, games }) => {
    const [statFilter, setStatFilter] = useState('all');
    const [rankFilter, setRankFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [viewMode, setViewMode] = useState('timeline'); // 'timeline' or 'by-stat'

    const gameMap = useMemo(() => {
        const map = {};
        (games || []).forEach(g => { if (g.gameId) map[g.gameId] = g; });
        return map;
    }, [games]);

    // Get unique stats for filter
    const availableStats = useMemo(() => {
        const stats = new Set();
        (allTimePassings || []).forEach(p => stats.add(p.stat_name));
        return [...stats].sort();
    }, [allTimePassings]);

    // Filter passings
    const filtered = useMemo(() => {
        return (allTimePassings || []).filter(p => {
            if (statFilter !== 'all' && p.stat_name !== statFilter) return false;
            if (rankFilter === 'top10' && p.new_rank > 10) return false;
            if (rankFilter === 'top25' && p.new_rank > 25) return false;
            if (rankFilter === 'top50' && p.new_rank > 50) return false;
            if (searchTerm) {
                const s = searchTerm.toLowerCase();
                if (!p.player_name?.toLowerCase().includes(s) &&
                    !p.stat_name?.toLowerCase().includes(s) &&
                    !(p.passed_players || []).some(pp => pp.name?.toLowerCase().includes(s))) return false;
            }
            return true;
        });
    }, [allTimePassings, statFilter, rankFilter, searchTerm]);

    // Notable moments (lowest ranks achieved)
    const notableMoments = useMemo(() => {
        return [...(allTimePassings || [])].sort((a, b) => a.new_rank - b.new_rank).slice(0, 5);
    }, [allTimePassings]);

    // Stats summary
    const summary = useMemo(() => {
        const players = new Set();
        const stats = new Set();
        (allTimePassings || []).forEach(p => { players.add(p.player_name); stats.add(p.stat_name); });
        const lowestRank = Math.min(...(allTimePassings || []).map(p => p.new_rank));
        return { total: (allTimePassings || []).length, players: players.size, stats: stats.size, bestRank: lowestRank };
    }, [allTimePassings]);

    // Format helpers
    const formatIP = (val) => {
        let whole = Math.floor(val);
        const frac = val - whole;
        let thirds;
        if (frac < 0.17) thirds = 0;
        else if (frac < 0.5) thirds = 1;
        else if (frac < 0.84) thirds = 2;
        else { thirds = 0; whole++; }
        return `${whole.toLocaleString()}.${thirds}`;
    };
    const formatStatValue = (val, stat) => {
        if (stat === 'IP') return formatIP(val);
        return Number.isInteger(val) ? val.toLocaleString() : val.toFixed(1);
    };

    // Group by stat for by-stat view
    const byStat = useMemo(() => {
        const groups = {};
        filtered.forEach(p => {
            if (!groups[p.stat_name]) groups[p.stat_name] = [];
            groups[p.stat_name].push(p);
        });
        Object.values(groups).forEach(arr => arr.sort((a, b) => a.new_rank - b.new_rank));
        return Object.entries(groups).sort((a, b) => b[1].length - a[1].length);
    }, [filtered]);

    const sortedFiltered = useMemo(() => {
        return [...filtered].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    }, [filtered]);

    if (!allTimePassings || allTimePassings.length === 0) {
        return <EmptyState icon="📜" title="No History Data" message="No all-time list movements have been recorded yet." />;
    }

    const renderPassing = (passing, idx) => {
        const playerUrl = passing.player_id
            ? `https://www.baseball-reference.com/players/${passing.player_id.charAt(0).toLowerCase()}/${passing.player_id}.shtml`
            : null;
        const passedPlayers = passing.passed_players || [];
        const tiedPlayers = passedPlayers.filter(p => p.tied);
        const actuallyPassed = passedPlayers.filter(p => !p.tied);
        const formatPlayerList = (players) => players.map(p => {
            const valueStr = formatStatValue(p.value, passing.stat);
            return `${p.name} (${valueStr})`;
        }).join(', ');
        let passedText = '';
        if (actuallyPassed.length > 0 && tiedPlayers.length > 0) {
            passedText = `passed ${formatPlayerList(actuallyPassed)}, tied ${formatPlayerList(tiedPlayers)}`;
        } else if (tiedPlayers.length > 0) {
            passedText = `tied ${formatPlayerList(tiedPlayers)}`;
        } else if (actuallyPassed.length > 0) {
            passedText = `passed ${formatPlayerList(actuallyPassed)}`;
        } else {
            passedText = 'moved up';
        }

        return (
            <div key={`${passing.player_id}-${passing.stat}-${passing.game_id}-${idx}`} className="flex items-start gap-4 relative">
                <div className="flex flex-col items-center flex-shrink-0">
                    <div className={`w-14 h-14 ${passing.new_rank <= 10 ? 'bg-gradient-to-br from-yellow-400 to-amber-500 ring-2 ring-yellow-300' : passing.new_rank <= 25 ? 'bg-gradient-to-br from-purple-500 to-violet-600' : passing.new_rank <= 50 ? 'bg-gradient-to-br from-purple-400 to-purple-500' : 'bg-gradient-to-br from-slate-400 to-slate-500'} rounded-full flex items-center justify-center text-white font-bold text-lg shadow-md`}>
                        #{passing.new_rank}
                    </div>
                </div>
                <div className="flex-1 bg-white border border-purple-200 rounded-lg p-4 hover:border-purple-400 hover:shadow-md transition-all">
                    <div className="flex items-center gap-2 flex-wrap">
                        {playerUrl ? (
                            <a href={playerUrl} target="_blank" rel="noopener noreferrer" className="font-bold text-purple-700 hover:text-purple-900 hover:underline text-lg">
                                {passing.player_name}
                            </a>
                        ) : (
                            <span className="font-bold text-slate-900 text-lg">{passing.player_name}</span>
                        )}
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-700">{passing.stat_name}</span>
                    </div>
                    <p className="text-purple-600 mt-1">{passedText}</p>
                    <div className="mt-2 flex items-center gap-3 text-xs text-slate-500 flex-wrap">
                        <span className="font-semibold text-purple-700">{formatStatValue(passing.new_value, passing.stat)} career {passing.stat_name.toLowerCase()}</span>
                        <span>{passing.date_display || passing.date}</span>
                        {passing.venue && <span>@ {passing.venue}</span>}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900">📜 History Witnessed</h1>
                        <p className="text-slate-500 mt-1">Players climbing the all-time leaderboards at games you attended</p>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="bg-purple-50 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-purple-700">{summary.total}</div>
                            <div className="text-xs text-purple-600">Passings</div>
                        </div>
                        <div className="bg-purple-50 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-purple-700">{summary.players}</div>
                            <div className="text-xs text-purple-600">Players</div>
                        </div>
                        <div className="bg-purple-50 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-purple-700">{summary.stats}</div>
                            <div className="text-xs text-purple-600">Stat Categories</div>
                        </div>
                        <div className="bg-yellow-50 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-yellow-700">#{summary.bestRank}</div>
                            <div className="text-xs text-yellow-600">Highest Rank</div>
                        </div>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap gap-3 mt-4 items-center">
                    <select value={statFilter} onChange={(e) => setStatFilter(e.target.value)}
                        className="px-3 py-2 border border-slate-300 rounded-lg text-sm">
                        <option value="all">All Stats</option>
                        {availableStats.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <select value={rankFilter} onChange={(e) => setRankFilter(e.target.value)}
                        className="px-3 py-2 border border-slate-300 rounded-lg text-sm">
                        <option value="all">All Ranks</option>
                        <option value="top10">Top 10</option>
                        <option value="top25">Top 25</option>
                        <option value="top50">Top 50</option>
                    </select>
                    <input type="text" placeholder="Search player..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                        className="px-3 py-2 border border-slate-300 rounded-lg text-sm flex-1 min-w-[150px]" />
                    <div className="flex rounded-lg overflow-hidden border border-slate-300">
                        <button onClick={() => setViewMode('timeline')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'timeline' ? 'bg-purple-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-50'}`}>Timeline</button>
                        <button onClick={() => setViewMode('by-stat')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'by-stat' ? 'bg-purple-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-50'}`}>By Stat</button>
                    </div>
                </div>
            </div>

            {/* Notable Moments */}
            {statFilter === 'all' && rankFilter === 'all' && !searchTerm && (
                <div className="bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl shadow p-6 border border-yellow-200">
                    <h2 className="text-lg font-bold text-yellow-800 mb-4">Most Notable Moments</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {notableMoments.map((p, i) => (
                            <div key={i} className="bg-white rounded-lg p-3 border border-yellow-200 shadow-sm">
                                <div className="flex items-center gap-2">
                                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-white text-sm font-bold ${p.new_rank <= 10 ? 'bg-gradient-to-br from-yellow-400 to-amber-500' : 'bg-gradient-to-br from-purple-500 to-violet-600'}`}>#{p.new_rank}</span>
                                    <div>
                                        <div className="font-bold text-slate-900 text-sm">{p.player_name}</div>
                                        <div className="text-xs text-slate-500">{p.stat_name} - {p.date_display || p.date}</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Timeline View */}
            {viewMode === 'timeline' && (
                <div className="space-y-4">
                    {sortedFiltered.map((p, i) => renderPassing(p, i))}
                    {sortedFiltered.length === 0 && <EmptyState icon="🔍" title="No Results" message="No passings match your filters." />}
                </div>
            )}

            {/* By-Stat View */}
            {viewMode === 'by-stat' && (
                <div className="space-y-6">
                    {byStat.map(([stat, passings]) => (
                        <div key={stat} className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                            <div className="p-4 bg-gradient-to-r from-purple-600 to-violet-700 text-white flex items-center justify-between">
                                <h3 className="font-bold text-lg">{stat}</h3>
                                <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-bold">{passings.length} passing{passings.length !== 1 ? 's' : ''}</span>
                            </div>
                            <div className="p-4 space-y-3">
                                {passings.map((p, i) => renderPassing(p, i))}
                            </div>
                        </div>
                    ))}
                    {byStat.length === 0 && <EmptyState icon="🔍" title="No Results" message="No passings match your filters." />}
                </div>
            )}
        </div>
    );
};

const GamesPerYearChart = ({ games }) => {
    const yearlyData = useMemo(() => {
        const byYear = {};
        (games || []).forEach(g => {
            const d = g.date || '';
            const year = d.includes('/') ? d.split('/')[2] : d.substring(0, 4);
            if (year && year.length === 4) byYear[year] = (byYear[year] || 0) + 1;
        });
        return Object.entries(byYear).sort((a, b) => a[0].localeCompare(b[0])).map(([year, count]) => ({ year, count }));
    }, [games]);

    if (yearlyData.length === 0) return null;
    const maxGames = Math.max(...yearlyData.map(y => y.count));

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b">
                <h2 className="subsection-title font-bold">Games Per Year</h2>
            </div>
            <div className="p-4">
                <div className="relative" style={{ height: '200px' }}>
                    <div className="absolute inset-0 flex items-end justify-between gap-1">
                        {yearlyData.map(d => (
                            <div key={d.year} className="flex-1 flex flex-col items-center justify-end h-full">
                                <div className="w-full bg-blue-600 rounded-t hover:bg-blue-700 transition-colors flex items-start justify-center pt-1"
                                     style={{ height: `${(d.count / maxGames) * 100}%`, minHeight: '24px' }}>
                                    <span className="text-xs text-white font-bold">{d.count}</span>
                                </div>
                                <span className="text-[10px] text-slate-500 mt-1">{d.year.slice(2)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

const SeasonTrendsChart = ({ games, playerGames, pitcherGames }) => {
    const canvasRef = useRef(null);
    const [metric, setMetric] = useState('avgSeen');

    const seasonData = useMemo(() => {
        const springIds = new Set((games || []).filter(g => g.gameType === 'spring').map(g => g.gameId));
        const byYear = {};
        const regGames = (games || []).filter(g => !springIds.has(g.gameId));
        regGames.forEach(g => {
            const d = g.date || '';
            const year = d.includes('/') ? d.split('/')[2] : d.substring(0, 4);
            if (!year || year.length !== 4) return;
            if (!byYear[year]) byYear[year] = { games: 0, h: 0, hr: 0, r: 0, rbi: 0, so: 0, bb: 0, sb: 0, ab: 0 };
            byYear[year].games++;
        });
        (playerGames || []).forEach(pg => {
            if (springIds.has(pg.gameId)) return;
            const d = pg.date || '';
            const year = d.includes('/') ? d.split('/')[2] : d.substring(0, 4);
            if (!year || !byYear[year]) return;
            byYear[year].h += (pg.h || 0); byYear[year].hr += (pg.hr || 0);
            byYear[year].r += (pg.r || 0); byYear[year].rbi += (pg.rbi || 0);
            byYear[year].bb += (pg.bb || 0); byYear[year].sb += (pg.sb || 0);
            byYear[year].ab += (pg.ab || 0);
        });
        (pitcherGames || []).forEach(pg => {
            if (springIds.has(pg.gameId)) return;
            const d = pg.date || '';
            const year = d.includes('/') ? d.split('/')[2] : d.substring(0, 4);
            if (!year || !byYear[year]) return;
            byYear[year].so += (pg.so || 0);
        });
        return Object.entries(byYear).sort((a, b) => a[0].localeCompare(b[0]))
            .map(([year, s]) => ({ year, ...s, avgSeen: s.ab > 0 ? (s.h / s.ab) : 0, hrPerGame: s.games > 0 ? s.hr / s.games : 0, kPerGame: s.games > 0 ? s.so / s.games : 0 }));
    }, [games, playerGames, pitcherGames]);

    const metrics = [
        { key: 'avgSeen', label: 'AVG Seen', fmt: v => v.toFixed(3), color: '#2563eb' },
        { key: 'hrPerGame', label: 'HR/Game', fmt: v => v.toFixed(2), color: '#dc2626' },
        { key: 'kPerGame', label: 'K/Game', fmt: v => v.toFixed(1), color: '#9333ea' },
        { key: 'hr', label: 'Total HR', fmt: v => v, color: '#ea580c' },
        { key: 'games', label: 'Games', fmt: v => v, color: '#16a34a' },
    ];

    useEffect(() => {
        if (!canvasRef.current || seasonData.length < 2) return;
        const ctx = canvasRef.current.getContext('2d');
        const cc = chartColors();
        const m = metrics.find(x => x.key === metric);
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: seasonData.map(s => s.year),
                datasets: [{
                    label: m.label,
                    data: seasonData.map(s => s[metric]),
                    borderColor: m.color,
                    backgroundColor: m.color + '20',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: cc.tooltip.bg, titleColor: cc.tooltip.text, bodyColor: cc.tooltip.text,
                        borderColor: cc.tooltip.border, borderWidth: 1,
                        callbacks: { label: (ctx) => `${m.label}: ${m.fmt(ctx.parsed.y)}` }
                    }
                },
                scales: {
                    x: { ticks: { font: { size: 11 }, color: cc.text }, grid: { color: cc.grid } },
                    y: { beginAtZero: metric !== 'avgSeen', ticks: { font: { size: 11 }, color: cc.text, callback: (v) => m.fmt(v) }, grid: { color: cc.grid } }
                }
            }
        });
        return () => chart.destroy();
    }, [seasonData, metric]);

    if (seasonData.length < 2) return null;

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b flex flex-wrap items-center justify-between gap-2">
                <h2 className="subsection-title font-bold">Season Trends</h2>
                <div className="flex flex-wrap gap-1.5">
                    {metrics.map(m => (
                        <button key={m.key} onClick={() => setMetric(m.key)}
                            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${metric === m.key ? 'text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                            style={metric === m.key ? { backgroundColor: m.color } : {}}>
                            {m.label}
                        </button>
                    ))}
                </div>
            </div>
            <div className="p-4"><canvas ref={canvasRef} className="w-full" style={{ height: '260px' }} /></div>
        </div>
    );
};

const CumulativeStatsChart = ({ games, playerGames, pitcherGames }) => {
    const [activeStat, setActiveStat] = useState('H');

    const statDefs = [
        { key: 'H', label: 'Hits', color: '#2563eb' },
        { key: 'R', label: 'Runs', color: '#16a34a' },
        { key: 'HR', label: 'HRs', color: '#dc2626' },
        { key: 'RBI', label: 'RBI', color: '#9333ea' },
        { key: 'K', label: 'K', color: '#ea580c' },
        { key: 'BB', label: 'BB', color: '#0891b2' },
        { key: 'SB', label: 'SB', color: '#65a30d' },
    ];

    const chartData = useMemo(() => {
        const springIds = new Set((games || []).filter(g => g.gameType === 'spring').map(g => g.gameId));
        const parseDate = toSortableDate;

        const pgByGame = {};
        (playerGames || []).forEach(pg => { if (!springIds.has(pg.gameId)) { if (!pgByGame[pg.gameId]) pgByGame[pg.gameId] = []; pgByGame[pg.gameId].push(pg); }});
        const pitByGame = {};
        (pitcherGames || []).forEach(pg => { if (!springIds.has(pg.gameId)) { if (!pitByGame[pg.gameId]) pitByGame[pg.gameId] = []; pitByGame[pg.gameId].push(pg); }});

        const sorted = [...(games || [])].filter(g => !springIds.has(g.gameId)).sort((a, b) => parseDate(a.date).localeCompare(parseDate(b.date)));

        const cumulative = [];
        let totals = { H: 0, R: 0, HR: 0, RBI: 0, K: 0, BB: 0, SB: 0 };
        sorted.forEach((game, i) => {
            const gid = game.gameId;
            (pgByGame[gid] || []).forEach(pg => {
                totals.H += (pg.h || 0); totals.R += (pg.r || 0); totals.HR += (pg.hr || 0);
                totals.RBI += (pg.rbi || 0); totals.BB += (pg.bb || 0); totals.SB += (pg.sb || 0);
            });
            (pitByGame[gid] || []).forEach(pg => { totals.K += (pg.so || 0); });
            cumulative.push({ ...totals, date: game.date });
        });
        return cumulative;
    }, [games, playerGames, pitcherGames]);

    if (chartData.length < 2) return null;

    const activeColor = statDefs.find(s => s.key === activeStat)?.color || '#2563eb';
    const maxVal = Math.max(...chartData.map(d => d[activeStat]), 1);
    const width = 800, height = 250;
    const pad = { top: 15, right: 15, bottom: 25, left: 55 };
    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;

    const points = chartData.map((d, i) => {
        const x = pad.left + (i / (chartData.length - 1)) * chartW;
        const y = pad.top + chartH - (d[activeStat] / maxVal) * chartH;
        return `${x},${y}`;
    }).join(' ');

    const yLabels = [0, 0.25, 0.5, 0.75, 1].map(pct => ({ val: Math.round(maxVal * pct), y: pad.top + chartH - pct * chartH }));

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b">
                <h2 className="subsection-title font-bold">Cumulative Stats Witnessed</h2>
            </div>
            <div className="p-4">
                <div className="flex flex-wrap gap-1.5 mb-3">
                    {statDefs.map(s => (
                        <button key={s.key} onClick={() => setActiveStat(s.key)}
                            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${activeStat === s.key ? 'text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                            style={activeStat === s.key ? { backgroundColor: s.color } : {}}>
                            {s.label}
                        </button>
                    ))}
                </div>
                <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
                    {yLabels.map((l, i) => (
                        <g key={i}>
                            <line x1={pad.left} y1={l.y} x2={width - pad.right} y2={l.y} stroke={isDark() ? '#334155' : '#e5e7eb'} strokeWidth="1" />
                            <text x={pad.left - 8} y={l.y + 4} textAnchor="end" fill={isDark() ? '#94a3b8' : '#6b7280'} fontSize="10">{l.val.toLocaleString()}</text>
                        </g>
                    ))}
                    <polygon points={`${pad.left},${pad.top + chartH} ${points} ${width - pad.right},${pad.top + chartH}`} fill={activeColor} fillOpacity="0.1" />
                    <polyline points={points} fill="none" stroke={activeColor} strokeWidth="2" strokeLinejoin="round" />
                </svg>
                <div className="text-center text-xs text-slate-500 mt-1">
                    Total: <span className="font-bold" style={{ color: activeColor }}>{chartData[chartData.length - 1]?.[activeStat]?.toLocaleString()}</span> {statDefs.find(s => s.key === activeStat)?.label.toLowerCase()} across {chartData.length} games
                </div>
            </div>
        </div>
    );
};

const AttendancePatterns = ({ games }) => {
    const patterns = useMemo(() => {
        const byDow = [0, 0, 0, 0, 0, 0, 0];
        const byMonth = {};
        const byTeam = {};
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

        (games || []).forEach(g => {
            const d = new Date(g.date);
            if (!isNaN(d)) {
                byDow[d.getDay()]++;
                const month = d.toLocaleString('default', { month: 'short' });
                byMonth[month] = (byMonth[month] || 0) + 1;
            }
            [g.homeTeam, g.awayTeam].forEach(t => { if (t) byTeam[t] = (byTeam[t] || 0) + 1; });
        });

        const maxDow = Math.max(...byDow);
        const favDay = dayNames[byDow.indexOf(maxDow)];
        const topTeams = Object.entries(byTeam).sort((a, b) => b[1] - a[1]).slice(0, 8);

        return { byDow, maxDow, dayNames, favDay, byMonth, topTeams };
    }, [games]);

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b">
                <h2 className="subsection-title font-bold">Attendance Patterns</h2>
            </div>
            <div className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h3 className="small-text font-bold text-slate-500 uppercase mb-3">Day of Week</h3>
                        <div className="relative" style={{ height: '140px' }}>
                            <div className="absolute inset-0 flex items-end justify-between gap-1.5">
                                {patterns.dayNames.map((day, i) => {
                                    const count = patterns.byDow[i];
                                    const pct = patterns.maxDow > 0 ? (count / patterns.maxDow) * 100 : 0;
                                    return (
                                        <div key={day} className="flex-1 flex flex-col items-center justify-end h-full">
                                            <div className="w-full bg-indigo-500 rounded-t hover:bg-indigo-600 flex items-start justify-center pt-1"
                                                 style={{ height: `${pct}%`, minHeight: count > 0 ? '22px' : '0' }}>
                                                {count > 0 && <span className="text-[10px] text-white font-bold">{count}</span>}
                                            </div>
                                            <span className="text-[10px] text-slate-500 mt-1">{day}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                    <div>
                        <h3 className="small-text font-bold text-slate-500 uppercase mb-3">Most Seen Teams</h3>
                        <div className="space-y-1.5">
                            {patterns.topTeams.map(([team, count], i) => (
                                <div key={team} className="flex items-center justify-between text-sm">
                                    <div className="flex items-center gap-2">
                                        <span className="text-slate-400 w-4">{i + 1}.</span>
                                        <span className="font-medium">{team}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-20 bg-slate-200 rounded-full h-2">
                                            <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${(count / patterns.topTeams[0][1]) * 100}%` }}></div>
                                        </div>
                                        <span className="text-xs text-slate-500 w-6 text-right">{count}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const GameConditions = ({ games }) => {
    const stats = useMemo(() => {
        const withTemp = (games || []).filter(g => g.temperature && g.temperature > 0);
        const withLength = (games || []).filter(g => g.gameLength);
        const withAttendance = (games || []).filter(g => g.attendance && g.attendance > 0);

        const parseLen = (s) => { if (!s) return 0; const p = s.split(':'); return (parseInt(p[0]) || 0) * 60 + (parseInt(p[1]) || 0); };
        const fmtLen = (m) => `${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}`;

        const tempVals = withTemp.map(g => g.temperature);
        const lenVals = withLength.map(g => ({ mins: parseLen(g.gameLength), game: g }));
        const attVals = withAttendance.map(g => g.attendance);

        const coldest = withTemp.length ? withTemp.reduce((a, b) => a.temperature < b.temperature ? a : b) : null;
        const hottest = withTemp.length ? withTemp.reduce((a, b) => a.temperature > b.temperature ? a : b) : null;
        const avgTemp = tempVals.length ? Math.round(tempVals.reduce((a, b) => a + b, 0) / tempVals.length) : null;

        const shortest = lenVals.length ? lenVals.reduce((a, b) => a.mins < b.mins ? a : b) : null;
        const longest = lenVals.length ? lenVals.reduce((a, b) => a.mins > b.mins ? a : b) : null;
        const avgLen = lenVals.length ? Math.round(lenVals.reduce((a, b) => a + b.mins, 0) / lenVals.length) : null;

        const lowAtt = withAttendance.length ? withAttendance.reduce((a, b) => a.attendance < b.attendance ? a : b) : null;
        const highAtt = withAttendance.length ? withAttendance.reduce((a, b) => a.attendance > b.attendance ? a : b) : null;
        const avgAtt = attVals.length ? Math.round(attVals.reduce((a, b) => a + b, 0) / attVals.length) : null;

        return { coldest, hottest, avgTemp, shortest, longest, avgLen, fmtLen, lowAtt, highAtt, avgAtt, hasTemp: withTemp.length > 0, hasLen: withLength.length > 0, hasAtt: withAttendance.length > 0 };
    }, [games]);

    if (!stats.hasTemp && !stats.hasLen && !stats.hasAtt) return null;

    const ConditionRow = ({ label, low, avg, high, lowLabel, highLabel, lowColor, highColor, unit }) => (
        <div className="flex items-center gap-3 py-2">
            <div className="w-24 text-xs font-semibold text-slate-500 shrink-0">{label}</div>
            <div className="flex-1 flex items-center gap-1">
                <div className="text-center flex-1">
                    <div className={`text-sm font-bold ${lowColor || 'text-blue-600'}`}>{low}{unit}</div>
                    <div className="text-[9px] text-slate-400">{lowLabel || 'Low'}</div>
                </div>
                <div className="text-center flex-1">
                    <div className="text-sm font-bold text-slate-600">{avg}{unit}</div>
                    <div className="text-[9px] text-slate-400">Avg</div>
                </div>
                <div className="text-center flex-1">
                    <div className={`text-sm font-bold ${highColor || 'text-red-600'}`}>{high}{unit}</div>
                    <div className="text-[9px] text-slate-400">{highLabel || 'High'}</div>
                </div>
            </div>
        </div>
    );

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h3 className="subsection-title font-bold text-slate-900 mb-3">Game Conditions</h3>
            <div className="divide-y divide-slate-100">
                {stats.hasTemp && (
                    <ConditionRow label="Temperature" unit={String.fromCharCode(176) + 'F'}
                        low={stats.coldest?.temperature} avg={stats.avgTemp} high={stats.hottest?.temperature}
                        lowLabel={stats.coldest ? `${stats.coldest.date}` : 'Low'}
                        highLabel={stats.hottest ? `${stats.hottest.date}` : 'High'}
                        lowColor="text-blue-600" highColor="text-red-600" />
                )}
                {stats.hasLen && (
                    <ConditionRow label="Duration" unit=""
                        low={stats.shortest ? stats.fmtLen(stats.shortest.mins) : '-'}
                        avg={stats.avgLen ? stats.fmtLen(stats.avgLen) : '-'}
                        high={stats.longest ? stats.fmtLen(stats.longest.mins) : '-'}
                        lowLabel={stats.shortest ? `${stats.shortest.game.date}` : 'Short'}
                        highLabel={stats.longest ? `${stats.longest.game.date}` : 'Long'}
                        lowColor="text-green-600" highColor="text-orange-600" />
                )}
                {stats.hasAtt && (
                    <ConditionRow label="Attendance" unit=""
                        low={stats.lowAtt?.attendance?.toLocaleString()} avg={stats.avgAtt?.toLocaleString()} high={stats.highAtt?.attendance?.toLocaleString()}
                        lowLabel={stats.lowAtt ? `${stats.lowAtt.date}` : 'Low'}
                        highLabel={stats.highAtt ? `${stats.highAtt.date}` : 'High'}
                        lowColor="text-slate-500" highColor="text-slate-800" />
                )}
            </div>
        </div>
    );
};

const Dashboard = ({ data, onTabChange }) => {
    // Get recent highlights for the dashboard
    const toSortDate = toSortableDate;
    const recentDebuts = useMemo(() => [...(data.debuts || [])].sort((a, b) => toSortDate(b.date).localeCompare(toSortDate(a.date))).slice(0, 5), [data.debuts]);
    const recentFinalGames = useMemo(() => [...(data.finalGames || [])].sort((a, b) => toSortDate(b.date).localeCompare(toSortDate(a.date))).slice(0, 5), [data.finalGames]);

    // Notable career milestones (round number milestones like 100th, 200th, 500th HR)
    const notableCareerMilestones = useMemo(() => {
        return [...(data.careerFirsts || [])]
            .filter(f => {
                const match = f.milestone?.match(/#?(\d+)/);
                if (match) {
                    const num = parseInt(match[1]);
                    return num >= 100 && num % 100 === 0;
                }
                return false;
            })
            .sort((a, b) => {
                const numA = parseInt((a.milestone?.match(/#?(\d+)/) || [])[1] || 0);
                const numB = parseInt((b.milestone?.match(/#?(\d+)/) || [])[1] || 0);
                return numB - numA;
            })
            .slice(0, 8);
    }, [data.careerFirsts]);

    // Top all-time passings for dashboard preview
    const topPassings = useMemo(() => {
        return [...(data.allTimePassings || [])].sort((a, b) => a.new_rank - b.new_rank).slice(0, 5);
    }, [data.allTimePassings]);

    // Recent games
    const recentGames = useMemo(() => {
        return [...(data.games || [])].sort((a, b) => toSortDate(b.date).localeCompare(toSortDate(a.date))).slice(0, 5);
    }, [data.games]);

    // Statcast highlights
    const statcastHighlights = useMemo(() => {
        const pg = data.playerGames || [];
        const pit = data.pitcherGames || [];
        const hardest = pg.filter(p => p.maxExitVelo).sort((a, b) => b.maxExitVelo - a.maxExitVelo)[0];
        const longest = pg.filter(p => p.maxDistance).sort((a, b) => b.maxDistance - a.maxDistance)[0];
        const fastest = pit.filter(p => p.maxSpeed).sort((a, b) => b.maxSpeed - a.maxSpeed)[0];
        const spinniest = pit.filter(p => p.avgSpinRate).sort((a, b) => b.avgSpinRate - a.avgSpinRate)[0];
        return [
            hardest && { label: 'Hardest Hit', value: `${hardest.maxExitVelo} mph`, player: hardest.name, playerId: hardest.playerId, sub: hardest.maxDistance ? `${hardest.maxDistance} ft` : null },
            longest && { label: 'Longest Ball', value: `${longest.maxDistance} ft`, player: longest.name, playerId: longest.playerId, sub: longest.maxExitVelo ? `${longest.maxExitVelo} mph` : null },
            fastest && { label: 'Fastest Pitch', value: `${fastest.maxSpeed} mph`, player: fastest.name, playerId: fastest.playerId },
            spinniest && { label: 'Most Spin', value: `${spinniest.avgSpinRate.toLocaleString()} rpm`, player: spinniest.name, playerId: spinniest.playerId },
        ].filter(Boolean);
    }, [data.playerGames, data.pitcherGames]);

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Games" value={data.games?.length || 0} color="blue" onClick={() => onTabChange && onTabChange('gamelog')} />
                <StatCard title="Players" value={data.players?.length || 0} color="green" onClick={() => onTabChange && onTabChange('players')} />
                <StatCard title="Milestones" value={data.milestones?.length || 0} color="purple" onClick={() => onTabChange && onTabChange('milestones')} />
                <StatCard title="Teams" value={data.teams?.length || 0} color="orange" onClick={() => onTabChange && onTabChange('venues')} />
            </div>

            {/* Recent Games + Statcast Records */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {recentGames.length > 0 && (
                    <div className="bg-white rounded-lg border border-slate-200 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="subsection-title font-bold text-slate-900">Recent Games</h3>
                            <button onClick={() => onTabChange && onTabChange('gamelog')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                        </div>
                        <div className="space-y-3">
                            {recentGames.map((g, i) => (
                                <div key={`rg-${g.gameId || i}`} className="flex items-center justify-between py-2 border-b last:border-0">
                                    <div>
                                        <span className="body-text font-semibold text-slate-900">{g.score}</span>
                                        <span className="small-text text-slate-500 ml-2">{g.venue}</span>
                                    </div>
                                    <span className="small-text text-slate-400">{g.date}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                {statcastHighlights.length > 0 && (
                    <div className="bg-white rounded-lg border border-slate-200 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="subsection-title font-bold text-slate-900">Statcast Records</h3>
                            <button onClick={() => { if (window.__navigateTab) window.__navigateTab('players', 'statcast'); }} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            {statcastHighlights.map((h, i) => (
                                <div key={`sc-${i}`} className="bg-slate-50 rounded-lg p-3">
                                    <div className="small-text text-slate-500 mb-1">{h.label}</div>
                                    <div className="text-lg font-bold font-mono text-slate-900">{h.value}</div>
                                    <div className="small-text text-slate-600 mt-1">
                                        <PlayerLink playerId={h.playerId} name={h.player} />
                                        {h.sub && <span className="text-slate-400 ml-1">({h.sub})</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border border-slate-200 p-6"><MilestoneChart milestones={data.milestones} /></div>
                <div className="bg-white rounded-lg border border-slate-200 p-6"><TeamChart teams={data.teams} /></div>
            </div>

            {/* Trends & Patterns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <GamesPerYearChart games={data.games} />
                <GameConditions games={data.games} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <SeasonTrendsChart games={data.games} playerGames={data.playerGames} pitcherGames={data.pitcherGames} />
                <CumulativeStatsChart games={data.games} playerGames={data.playerGames} pitcherGames={data.pitcherGames} />
            </div>

            {/* Recent Highlights */}
            {(recentDebuts.length > 0 || recentFinalGames.length > 0) && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {recentDebuts.length > 0 && (
                        <div className="bg-white rounded-lg border border-slate-200 p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="subsection-title font-bold text-slate-900">🌟 Recent MLB Debuts</h3>
                                <button onClick={() => onTabChange && onTabChange('special')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                            </div>
                            <div className="space-y-3">
                                {recentDebuts.map((d, i) => (
                                    <div key={`debut-${d.playerId || i}`} className="flex items-center justify-between py-2 border-b last:border-0">
                                        <div>
                                            <PlayerLink playerId={d.playerId} name={d.player} />
                                            <span className="small-text text-slate-500 ml-2">{d.team}</span>
                                        </div>
                                        <span className="small-text text-slate-400">{d.date}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    {recentFinalGames.length > 0 && (
                        <div className="bg-white rounded-lg border border-slate-200 p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="subsection-title font-bold text-slate-900">👋 Recent Final Games</h3>
                                <button onClick={() => onTabChange && onTabChange('special')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                            </div>
                            <div className="space-y-3">
                                {recentFinalGames.map((d, i) => (
                                    <div key={`final-${d.playerId || i}`} className="flex items-center justify-between py-2 border-b last:border-0">
                                        <div>
                                            <PlayerLink playerId={d.playerId} name={d.player} />
                                            <span className="small-text text-slate-500 ml-2">{d.team}</span>
                                        </div>
                                        <span className="small-text text-slate-400">{d.date}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Notable Career Milestones & History */}
            {(notableCareerMilestones.length > 0 || topPassings.length > 0) && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {notableCareerMilestones.length > 0 && (
                        <div className="bg-white rounded-lg border border-slate-200 p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="subsection-title font-bold text-slate-900">⭐ Notable Career Milestones</h3>
                                <button onClick={() => onTabChange && onTabChange('milestones')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                            </div>
                            <div className="space-y-3">
                                {notableCareerMilestones.map((m, i) => {
                                    const num = (m.milestone?.match(/#?(\d+)/) || [])[1] || '';
                                    return (
                                        <div key={`cm-${i}`} className="flex items-center gap-3 py-2 border-b last:border-0">
                                            <span className="inline-flex items-center justify-center min-w-[48px] h-8 bg-gradient-to-r from-amber-400 to-yellow-500 text-white text-sm font-bold rounded-full px-2">#{num}</span>
                                            <div className="flex-1">
                                                <PlayerLink playerId={m.player_id} name={m.player_name} />
                                                <span className="small-text text-slate-500 ml-1">{m.milestone?.replace(/#?\d+\w*\s*/, '').trim()}</span>
                                            </div>
                                            <span className="small-text text-slate-400">{m.date_display || m.date}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                    {topPassings.length > 0 && (
                        <div className="bg-white rounded-lg border border-slate-200 p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="subsection-title font-bold text-slate-900">📜 History Witnessed</h3>
                                <button onClick={() => onTabChange && onTabChange('milestones')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all {data.allTimePassings?.length || 0} →</button>
                            </div>
                            <div className="space-y-3">
                                {topPassings.map((p, i) => (
                                    <div key={`hp-${i}`} className="flex items-center gap-3 py-2 border-b last:border-0">
                                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-white text-sm font-bold ${p.new_rank <= 10 ? 'bg-gradient-to-br from-yellow-400 to-amber-500' : 'bg-gradient-to-br from-purple-500 to-violet-600'}`}>#{p.new_rank}</span>
                                        <div className="flex-1">
                                            <PlayerLink playerId={p.player_id} name={p.player_name} />
                                            <span className="small-text text-purple-600 ml-1">{p.stat_name}</span>
                                        </div>
                                        <span className="small-text text-slate-400">{p.date_display || p.date}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Companions summary */}
            {data.companionData?.companions?.length > 0 && (
                <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="subsection-title font-bold text-slate-900">👥 Top Game Companions</h3>
                        <button onClick={() => onTabChange && onTabChange('companions')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {data.companionData.companions.slice(0, 6).map((c, i) => (
                            <div key={`comp-${c.name || i}`} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                                <span className="body-text font-medium text-slate-900">{c.name}</span>
                                <span className="small-text text-slate-500">{c.games} games</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// Expandable badge cell component
const BadgeCell = ({ badges, badgeColors }) => {
    if (!badges || badges.length === 0) return null;
    const MAX_INLINE = 3;
    return (
        <div className="group relative flex flex-wrap gap-1 max-w-sm">
            {badges.slice(0, MAX_INLINE).map((badge, i) => (
                <span
                    key={`${badge.type}-${badge.text}-${i}`}
                    className={`px-1.5 py-0.5 rounded text-xs whitespace-nowrap ${badgeColors[badge.type] || 'bg-slate-100 text-slate-700'}`}
                    title={badge.title}
                >
                    {badge.text}
                </span>
            ))}
            {badges.length > MAX_INLINE && (
                <span className="px-1.5 py-0.5 rounded text-xs bg-slate-200 text-slate-600">
                    +{badges.length - MAX_INLINE}
                </span>
            )}
            {badges.length > MAX_INLINE && (
                <div className="hidden group-hover:block absolute top-full left-0 mt-1 z-20 bg-white rounded-lg shadow-lg border p-2 max-w-md" onClick={(e) => e.stopPropagation()}>
                    <div className="flex flex-wrap gap-1">
                        {badges.map((badge, i) => (
                            <span key={`full-${badge.type}-${badge.text}-${i}`} className={`px-1.5 py-0.5 rounded text-xs whitespace-nowrap ${badgeColors[badge.type] || 'bg-slate-100 text-slate-700'}`} title={badge.title}>
                                {badge.text}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const computeCumulativeStatBadges = (games, playerGames, pitcherGames) => {
    const badges = {};
    const STAT_MILESTONES = [100, 250, 500, 750, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 7500, 10000];

    const pgByGame = {};
    (playerGames || []).forEach(pg => {
        const gid = pg.gameId;
        if (!pgByGame[gid]) pgByGame[gid] = [];
        pgByGame[gid].push(pg);
    });
    const pitByGame = {};
    (pitcherGames || []).forEach(pg => {
        const gid = pg.gameId;
        if (!pitByGame[gid]) pitByGame[gid] = [];
        pitByGame[gid].push(pg);
    });

    const parseDate = toSortableDate;
    const springGameIds = new Set((games || []).filter(g => g.gameType === 'spring').map(g => g.gameId));
    const sorted = [...games].filter(g => !springGameIds.has(g.gameId)).sort((a, b) => parseDate(a.date).localeCompare(parseDate(b.date)));

    let totals = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
    let pitK = 0;
    let prevTotals = { ...totals };
    let prevPitK = 0;

    // Venue-specific tracking
    const VENUE_MILESTONES = [50, 100, 250, 500, 750, 1000];
    const venueTotals = {};  // venue -> { H, R, HR, ... }
    const venuePrev = {};    // venue -> prev totals snapshot

    sorted.forEach(game => {
        const gid = game.gameId;
        if (!gid) return;
        badges[gid] = [];
        const rawVenue = game.venue || '';
        const matched = matchStadiumByName(rawVenue);
        const venue = matched ? matched.name : rawVenue;

        // Initialize venue tracking
        if (venue && !venueTotals[venue]) {
            venueTotals[venue] = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
            venuePrev[venue] = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
        }

        (pgByGame[gid] || []).forEach(pg => {
            totals.H += (pg.h || 0);
            totals.R += (pg.r || 0);
            totals.HR += (pg.hr || 0);
            totals.RBI += (pg.rbi || 0);
            totals.SO += (pg.so || 0);
            totals.BB += (pg.bb || 0);
            totals.SB += (pg.sb || 0);
            totals['2B'] += (pg.doubles || 0);
            totals['3B'] += (pg.triples || 0);
            if (venue) {
                venueTotals[venue].H += (pg.h || 0);
                venueTotals[venue].R += (pg.r || 0);
                venueTotals[venue].HR += (pg.hr || 0);
                venueTotals[venue].RBI += (pg.rbi || 0);
                venueTotals[venue].SO += (pg.so || 0);
                venueTotals[venue].BB += (pg.bb || 0);
                venueTotals[venue].SB += (pg.sb || 0);
                venueTotals[venue]['2B'] += (pg.doubles || 0);
                venueTotals[venue]['3B'] += (pg.triples || 0);
            }
        });
        let gameMaxVelo = 0;
        let gameMaxVeloPitcher = '';
        (pitByGame[gid] || []).forEach(pg => {
            pitK += (pg.so || 0);
            if (pg.maxSpeed && pg.maxSpeed > gameMaxVelo) {
                gameMaxVelo = pg.maxSpeed;
                gameMaxVeloPitcher = pg.name;
            }
        });

        const labels = { H: 'Hits', R: 'Runs', HR: 'HRs', RBI: 'RBI', SO: 'K', BB: 'Walks', SB: 'Steals', '2B': 'Doubles', '3B': 'Triples' };
        Object.entries(totals).forEach(([stat, val]) => {
            const prev = prevTotals[stat];
            STAT_MILESTONES.forEach(m => {
                if (val >= m && prev < m) {
                    badges[gid].push({
                        type: 'cumulative-stat',
                        text: `${m.toLocaleString()} ${labels[stat]} Witnessed`,
                        title: `You've now witnessed ${m.toLocaleString()} total ${labels[stat].toLowerCase()} across all games`
                    });
                }
            });
        });
        STAT_MILESTONES.forEach(m => {
            if (pitK >= m && prevPitK < m) {
                badges[gid].push({
                    type: 'cumulative-stat',
                    text: `${m.toLocaleString()} K Witnessed`,
                    title: `You've now witnessed ${m.toLocaleString()} total strikeouts (pitching) across all games`
                });
            }
        });

        // Pitch velocity milestones
        if (gameMaxVelo >= 100) {
            badges[gid].push({
                type: 'pitch-velo',
                text: `${gameMaxVelo} mph - ${gameMaxVeloPitcher}`,
                title: `${gameMaxVeloPitcher} hit ${gameMaxVelo} mph`
            });
        }

        // Venue-specific milestones
        if (venue) {
            const shortVenue = venue.replace(/ Stadium| Park| Field| Coliseum| Centre| Arena/gi, '').trim();
            Object.entries(venueTotals[venue]).forEach(([stat, val]) => {
                const prev = venuePrev[venue][stat];
                VENUE_MILESTONES.forEach(m => {
                    if (val >= m && prev < m) {
                        badges[gid].push({
                            type: 'venue-stat',
                            text: `${m.toLocaleString()} ${labels[stat]} at ${shortVenue}`,
                            title: `You've witnessed ${m.toLocaleString()} ${labels[stat].toLowerCase()} at ${venue}`
                        });
                    }
                });
            });
            venuePrev[venue] = { ...venueTotals[venue] };
        }

        prevTotals = { ...totals };
        prevPitK = pitK;
    });

    return badges;
};

const GameLogWithDetails = ({ games, playerGames, pitcherGames, careerFirstsByGame, allTimePassingsByGame }) => {
    const [selectedGame, setSelectedGame] = useState(null);
    const [badgeTypeFilter, setBadgeTypeFilter] = useState('all');
    const [badgeTextFilter, setBadgeTextFilter] = useState('');

    // Check for pending game selection (from player timeline click)
    useEffect(() => {
        if (window._pendingGameId) {
            const gameId = window._pendingGameId;
            window._pendingGameId = null;
            const game = (games || []).find(g => g.gameId === gameId);
            if (game) setSelectedGame(game);
        }
    });


    // Compute milestones for badge display
    const milestoneData = useMemo(() => computeGameMilestones(games), [games]);
    const gameMilestones = milestoneData.milestones || {};

    // Compute cumulative stat badges (total hits/runs/HRs witnessed)
    const cumulativeBadges = useMemo(() => computeCumulativeStatBadges(games, playerGames, pitcherGames), [games, playerGames, pitcherGames]);

    // Badge colors by type
    const badgeColors = {
        'game-count': 'bg-purple-100 text-purple-700',
        'team': 'bg-blue-100 text-blue-700',
        'venue': 'bg-green-100 text-green-700',
        'div-first': 'bg-orange-100 text-orange-700',
        'div-complete': 'bg-yellow-100 text-yellow-800 font-bold',
        'div-stadiums': 'bg-indigo-100 text-indigo-700 font-bold',
        'matchup': 'bg-slate-100 text-slate-700',
        'holiday': 'bg-red-100 text-red-700',
        'career-first': 'bg-amber-100 text-amber-800 font-bold',
        'cumulative-stat': 'bg-teal-100 text-teal-800 font-bold',
        'venue-stat': 'bg-purple-100 text-purple-800 font-bold',
        'pitch-velo': 'bg-red-100 text-red-700 font-bold'
    };

    const badgeTypeLabels = {
        'game-count': 'Game Count',
        'team': 'Team',
        'venue': 'Venue',
        'div-first': 'Division First',
        'div-complete': 'Division Complete',
        'div-stadiums': 'Division Stadiums',
        'matchup': 'Matchup',
        'holiday': 'Holiday',
        'career-first': 'Career First',
        'cumulative-stat': 'Cumulative Stat',
        'venue-stat': 'Venue Stat',
        'pitch-velo': '100+ mph'
    };

    // Precompute all badges per game for filtering
    const allBadgesByGame = useMemo(() => {
        const result = {};
        // shortenMilestone is now global
        // getLastName is now global
        games.forEach(game => {
            const gid = game.gameId;
            if (!gid) return;
            const regularBadges = gameMilestones[gid]?.badges || [];
            const gameCareerFirsts = careerFirstsByGame?.[gid] || [];
            const careerFirstBadges = gameCareerFirsts.map(f => ({
                type: 'career-first',
                text: `⭐ ${getLastName(f.player_name)}: ${shortenMilestone(f.milestone)}`,
                title: `${f.player_name || 'Unknown'}'s ${f.milestone || 'milestone'}`
            }));
            result[gid] = [...regularBadges, ...careerFirstBadges, ...(cumulativeBadges[gid] || [])].filter(b => b.text && b.text.trim());
        });
        return result;
    }, [games, gameMilestones, careerFirstsByGame, cumulativeBadges]);

    // Collect all badge types that actually appear
    const availableBadgeTypes = useMemo(() => {
        const types = new Set();
        Object.values(allBadgesByGame).forEach(badges => badges.forEach(b => types.add(b.type)));
        return [...types].sort();
    }, [allBadgesByGame]);

    // Filter games by badge criteria
    const badgeFilteredGames = useMemo(() => {
        if (badgeTypeFilter === 'all' && !badgeTextFilter) return games;
        if (badgeTypeFilter === 'any-badge') {
            return games.filter(g => (allBadgesByGame[g.gameId] || []).length > 0);
        }
        return games.filter(game => {
            const badges = allBadgesByGame[game.gameId] || [];
            if (badges.length === 0) return false;
            let matched = badges;
            if (badgeTypeFilter && badgeTypeFilter !== 'all') {
                matched = matched.filter(b => b.type === badgeTypeFilter);
            }
            if (badgeTextFilter) {
                const q = badgeTextFilter.toLowerCase();
                matched = matched.filter(b => (b.text || '').toLowerCase().includes(q) || (b.title || '').toLowerCase().includes(q));
            }
            return matched.length > 0;
        });
    }, [games, badgeTypeFilter, badgeTextFilter, allBadgesByGame]);

    const hasBadgeFilter = badgeTypeFilter !== 'all' || badgeTextFilter;

    // Compute total stats witnessed — responds to badge filter
    const totalStats = useMemo(() => {
        const springGameIds = new Set((games || []).filter(g => g.gameType === 'spring').map(g => g.gameId));
        const filteredGameIds = hasBadgeFilter ? new Set(badgeFilteredGames.map(g => g.gameId)) : null;
        const stats = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
        let pitK = 0;
        let gameCount = 0;
        const countedGames = new Set();
        (playerGames || []).forEach(pg => {
            if (springGameIds.has(pg.gameId)) return;
            if (filteredGameIds && !filteredGameIds.has(pg.gameId)) return;
            stats.H += (pg.h || 0); stats.R += (pg.r || 0); stats.HR += (pg.hr || 0);
            stats.RBI += (pg.rbi || 0); stats.SO += (pg.so || 0); stats.BB += (pg.bb || 0);
            stats.SB += (pg.sb || 0); stats['2B'] += (pg.doubles || 0); stats['3B'] += (pg.triples || 0);
            countedGames.add(pg.gameId);
        });
        (pitcherGames || []).forEach(pg => {
            if (springGameIds.has(pg.gameId)) return;
            if (filteredGameIds && !filteredGameIds.has(pg.gameId)) return;
            pitK += (pg.so || 0);
            countedGames.add(pg.gameId);
        });
        return { ...stats, pitK, gameCount: countedGames.size };
    }, [games, playerGames, pitcherGames, badgeFilteredGames, hasBadgeFilter]);

    const searchableGames = useMemo(() => badgeFilteredGames.map(g => ({
        ...g, _searchTeams: (TEAM_CODE_TO_NAME[g.awayTeam] || '') + ' ' + (TEAM_CODE_TO_NAME[g.homeTeam] || '')
    })), [badgeFilteredGames]);

    return (
        <>
            {/* Total Stats Witnessed */}
            <div className="bg-gradient-to-r from-teal-600 to-teal-700 rounded-lg shadow-lg p-5 text-white mb-4">
                <h2 className="text-xl font-bold mb-3">📊 Total Stats Witnessed <span className="text-sm font-normal opacity-80">({totalStats.gameCount} regular season & postseason games)</span></h2>
                <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-3">
                    {[
                        { label: 'Hits', val: totalStats.H },
                        { label: 'Runs', val: totalStats.R },
                        { label: 'HR', val: totalStats.HR },
                        { label: 'RBI', val: totalStats.RBI },
                        { label: '2B', val: totalStats['2B'] },
                        { label: '3B', val: totalStats['3B'] },
                        { label: 'K', val: totalStats.pitK },
                        { label: 'BB', val: totalStats.BB },
                        { label: 'SB', val: totalStats.SB },
                    ].map(s => (
                        <div key={s.label} className="bg-white/20 rounded-lg p-2 text-center">
                            <div className="text-2xl font-bold">{s.val.toLocaleString()}</div>
                            <div className="text-xs opacity-90">{s.label}</div>
                        </div>
                    ))}
                </div>
            </div>
            {/* Badge filter bar */}
            <div className="bg-white rounded-lg border border-slate-200 mb-2 p-3">
                <div className="flex flex-wrap items-center gap-3">
                    <span className="small-text font-semibold text-slate-600">🏅 Badge Filter:</span>
                    <select
                        value={badgeTypeFilter}
                        onChange={(e) => setBadgeTypeFilter(e.target.value)}
                        className="px-3 py-1.5 body-text border rounded-lg"
                    >
                        <option value="all">All Games</option>
                        <option value="any-badge">Any Badge</option>
                        {availableBadgeTypes.map(t => (
                            <option key={t} value={t}>{badgeTypeLabels[t] || t}</option>
                        ))}
                    </select>
                    <input
                        type="text"
                        placeholder="Search badge text..."
                        value={badgeTextFilter}
                        onChange={(e) => setBadgeTextFilter(e.target.value)}
                        className="px-3 py-1.5 body-text border rounded-lg min-w-[200px]"
                    />
                    {hasBadgeFilter && (
                        <button
                            onClick={() => { setBadgeTypeFilter('all'); setBadgeTextFilter(''); }}
                            className="px-3 py-1.5 body-text text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded"
                        >
                            Clear
                        </button>
                    )}
                    {hasBadgeFilter && (
                        <span className="small-text text-slate-500">{badgeFilteredGames.length} of {games.length} games</span>
                    )}
                </div>
            </div>
            <DataTable
                title="📋 Game Log"
                data={searchableGames}
                defaultSortKey="date"
                enableDateFilter={true}
                onRowClick={(row) => setSelectedGame(row)}
                filterOptions={[
                    { key: 'gameType', label: 'Game Type', displayFn: (v) => v === 'spring' ? 'Spring Training' : v === 'postseason' ? 'Postseason' : v === 'regular' ? 'Regular Season' : v },
                    { key: 'homeTeam', label: 'Home Team' },
                    { key: 'venue', label: 'Venue' }
                ]}
                columns={[
                    { key: 'date', label: 'Date', render: (v, row) => (
                        <div className="flex items-center gap-1.5">
                            <button className="text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('venues', 'calendar'); }}>{v}</button>
                            {row.gameType === 'spring' && <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-[10px] font-semibold rounded">ST</span>}
                            {row.gameType === 'postseason' && <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 text-[10px] font-semibold rounded">PS</span>}
                        </div>
                    )},
                    { key: 'awayTeam', label: 'Away', render: (v) => <button className="text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('progress', 'matchups'); }}>{v}</button> },
                    { key: 'homeTeam', label: 'Home', render: (v) => <button className="text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('progress', 'matchups'); }}>{v}</button> },
                    { key: 'score', label: 'Score' },
                    { key: 'venue', label: 'Venue', render: (v) => <button className="text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('venues'); }}>{v}</button> },
                    {
                        key: 'badges',
                        label: 'Badges',
                        render: (_, row) => (
                            <BadgeCell
                                badges={allBadgesByGame[row.gameId] || []}
                                badgeColors={badgeColors}
                            />
                        )
                    },
                    {
                        key: 'gameId',
                        label: 'Game',
                        render: (v, row) => (
                            <div className="flex items-center gap-2">
                                <GameLink gameId={v} />
                                <button
                                    onClick={() => setSelectedGame(row)}
                                    className="px-2 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded text-xs font-semibold"
                                >
                                    Details
                                </button>
                            </div>
                        )
                    }
                ]}
            />
            
            {selectedGame && (() => {
                const toSort = toSortableDate;
                const sortedGames = [...(games || [])].sort((a, b) => toSort(b.date).localeCompare(toSort(a.date)));
                const idx = sortedGames.findIndex(g => g.gameId === selectedGame.gameId);
                const prevGame = idx > 0 ? sortedGames[idx - 1] : null;
                const nextGame = idx < sortedGames.length - 1 ? sortedGames[idx + 1] : null;
                return (
                    <GameDetailsModal
                        game={selectedGame}
                        playerGames={playerGames}
                        pitcherGames={pitcherGames}
                        careerFirsts={careerFirstsByGame?.[selectedGame.gameId] || []}
                        allTimePassings={(allTimePassingsByGame || {})[selectedGame.gameId] || []}
                        badges={allBadgesByGame?.[selectedGame.gameId] || []}
                        onClose={() => setSelectedGame(null)}
                        onPrev={prevGame ? () => setSelectedGame(prevGame) : null}
                        onNext={nextGame ? () => setSelectedGame(nextGame) : null}
                        gameIndex={idx >= 0 ? idx + 1 : null}
                        totalGames={sortedGames.length}
                    />
                );
            })()}
        </>
    );
};

// Complete MLB Stadium Database - Current, Historical, and International
const ALL_MLB_STADIUMS = [
    // === CURRENT MLB STADIUMS (30) ===
    { id: 'chase', name: 'Chase Field', team: 'ARI', lat: 33.4455, lng: -112.0667, years: '1998-present', current: true, aliases: ['Bank One Ballpark', 'BOB'] },
    { id: 'truist', name: 'Truist Park', team: 'ATL', lat: 33.8908, lng: -84.4678, years: '2017-present', current: true, aliases: ['SunTrust Park'] },
    { id: 'camden', name: 'Oriole Park at Camden Yards', team: 'BAL', lat: 39.2838, lng: -76.6218, years: '1992-present', current: true, aliases: ['Camden Yards'] },
    { id: 'fenway', name: 'Fenway Park', team: 'BOS', lat: 42.3467, lng: -71.0972, years: '1912-present', current: true, aliases: [] },
    { id: 'wrigley', name: 'Wrigley Field', team: 'CHC', lat: 41.9484, lng: -87.6553, years: '1914-present', current: true, aliases: ['Cubs Park', 'Weeghman Park'] },
    { id: 'guaranteed', name: 'Guaranteed Rate Field', team: 'CHW', lat: 41.8299, lng: -87.6338, years: '1991-present', current: true, aliases: ['Comiskey Park II', 'U.S. Cellular Field', 'New Comiskey Park'] },
    { id: 'gabp', name: 'Great American Ball Park', team: 'CIN', lat: 39.0979, lng: -84.5082, years: '2003-present', current: true, aliases: [] },
    { id: 'progressive', name: 'Progressive Field', team: 'CLE', lat: 41.4962, lng: -81.6852, years: '1994-present', current: true, aliases: ['Jacobs Field', 'The Jake'] },
    { id: 'coors', name: 'Coors Field', team: 'COL', lat: 39.7559, lng: -104.9942, years: '1995-present', current: true, aliases: [] },
    { id: 'comerica', name: 'Comerica Park', team: 'DET', lat: 42.3390, lng: -83.0485, years: '2000-present', current: true, aliases: [] },
    { id: 'minutemaid', name: 'Minute Maid Park', team: 'HOU', lat: 29.7573, lng: -95.3555, years: '2000-present', current: true, aliases: ['Enron Field', 'Astros Field'] },
    { id: 'kauffman', name: 'Kauffman Stadium', team: 'KC', lat: 39.0517, lng: -94.4803, years: '1973-present', current: true, aliases: ['Royals Stadium'] },
    { id: 'angel', name: 'Angel Stadium', team: 'LAA', lat: 33.8003, lng: -117.8827, years: '1966-present', current: true, aliases: ['Anaheim Stadium', 'Edison International Field', 'Angel Stadium of Anaheim'] },
    { id: 'dodger', name: 'Dodger Stadium', team: 'LAD', lat: 34.0739, lng: -118.2400, years: '1962-present', current: true, aliases: ['Chavez Ravine'] },
    { id: 'loandepot', name: 'loanDepot park', team: 'MIA', lat: 25.7781, lng: -80.2196, years: '2012-present', current: true, aliases: ['Marlins Park'] },
    { id: 'amfam', name: 'American Family Field', team: 'MIL', lat: 43.0280, lng: -87.9712, years: '2001-present', current: true, aliases: ['Miller Park'] },
    { id: 'target', name: 'Target Field', team: 'MIN', lat: 44.9817, lng: -93.2776, years: '2010-present', current: true, aliases: [] },
    { id: 'citi', name: 'Citi Field', team: 'NYM', lat: 40.7571, lng: -73.8458, years: '2009-present', current: true, aliases: [] },
    { id: 'yankee3', name: 'Yankee Stadium', team: 'NYY', lat: 40.8296, lng: -73.9262, years: '2009-present', current: true, aliases: ['New Yankee Stadium', 'Yankee Stadium III'] },
    { id: 'coliseum', name: 'Oakland Coliseum', team: 'OAK', lat: 37.7516, lng: -122.2005, years: '1968-2024', current: false, aliases: ['Oakland-Alameda County Coliseum', 'McAfee Coliseum', 'O.co Coliseum', 'RingCentral Coliseum'] },
    { id: 'sutter', name: 'Sutter Health Park', team: 'ATH', lat: 38.5802, lng: -121.5089, years: '2025-present', current: true, aliases: ['Raley Field'] },
    { id: 'citizens', name: 'Citizens Bank Park', team: 'PHI', lat: 39.9061, lng: -75.1665, years: '2004-present', current: true, aliases: [] },
    { id: 'pnc', name: 'PNC Park', team: 'PIT', lat: 40.4469, lng: -80.0057, years: '2001-present', current: true, aliases: [] },
    { id: 'petco', name: 'Petco Park', team: 'SD', lat: 32.7076, lng: -117.1570, years: '2004-present', current: true, aliases: [] },
    { id: 'oracle', name: 'Oracle Park', team: 'SF', lat: 37.7786, lng: -122.3893, years: '2000-present', current: true, aliases: ['Pacific Bell Park', 'SBC Park', 'AT&T Park'] },
    { id: 'tmobile', name: 'T-Mobile Park', team: 'SEA', lat: 47.5914, lng: -122.3325, years: '1999-present', current: true, aliases: ['Safeco Field'] },
    { id: 'busch3', name: 'Busch Stadium', team: 'STL', lat: 38.6226, lng: -90.1928, years: '2006-present', current: true, aliases: ['Busch Stadium III', 'New Busch Stadium'] },
    { id: 'tropicana', name: 'Tropicana Field', team: 'TB', lat: 27.7682, lng: -82.6534, years: '1998-present', current: true, aliases: ['The Trop', 'Thunderdome'] },
    { id: 'globelife2', name: 'Globe Life Field', team: 'TEX', lat: 32.7473, lng: -97.0845, years: '2020-present', current: true, aliases: [] },
    { id: 'rogers', name: 'Rogers Centre', team: 'TOR', lat: 43.6414, lng: -79.3894, years: '1989-present', current: true, aliases: ['SkyDome'] },
    { id: 'nationals', name: 'Nationals Park', team: 'WSH', lat: 38.8730, lng: -77.0074, years: '2008-present', current: true, aliases: [] },

    // === HISTORICAL/DEFUNCT STADIUMS ===
    // Atlanta
    { id: 'turner', name: 'Turner Field', team: 'ATL', lat: 33.7353, lng: -84.3894, years: '1997-2016', current: false, aliases: ['Centennial Olympic Stadium'] },
    { id: 'fulton', name: 'Atlanta-Fulton County Stadium', team: 'ATL', lat: 33.7401, lng: -84.3896, years: '1966-1996', current: false, aliases: ['The Launching Pad'] },

    // New York Yankees - Old Stadium
    { id: 'yankee2', name: 'Yankee Stadium (1923-2008)', team: 'NYY', lat: 40.8267, lng: -73.9281, years: '1923-2008', current: false, aliases: ['Old Yankee Stadium', 'Yankee Stadium II', 'The House That Ruth Built'] },

    // New York Mets
    { id: 'shea', name: 'Shea Stadium', team: 'NYM', lat: 40.7566, lng: -73.8458, years: '1964-2008', current: false, aliases: [] },

    // Minnesota
    { id: 'metrodome', name: 'Hubert H. Humphrey Metrodome', team: 'MIN', lat: 44.9738, lng: -93.2580, years: '1982-2009', current: false, aliases: ['Metrodome', 'The Dome'] },

    // Texas
    { id: 'globelife1', name: 'Globe Life Park in Arlington', team: 'TEX', lat: 32.7512, lng: -97.0832, years: '1994-2019', current: false, aliases: ['The Ballpark in Arlington', 'Rangers Ballpark in Arlington', 'Ameriquest Field'] },

    // St. Louis
    { id: 'busch2', name: 'Busch Memorial Stadium', team: 'STL', lat: 38.6228, lng: -90.1931, years: '1966-2005', current: false, aliases: ['Busch Stadium II'] },

    // Washington
    { id: 'rfk', name: 'RFK Stadium', team: 'WSH', lat: 38.8898, lng: -76.9719, years: '2005-2007', current: false, aliases: ['Robert F. Kennedy Memorial Stadium'] },

    // Miami/Florida
    { id: 'sunlife', name: 'Hard Rock Stadium', team: 'MIA', lat: 25.9580, lng: -80.2389, years: '1993-2011', current: false, aliases: ['Joe Robbie Stadium', 'Pro Player Stadium', 'Dolphin Stadium', 'Land Shark Stadium', 'Sun Life Stadium'] },

    // Philadelphia
    { id: 'veterans', name: 'Veterans Stadium', team: 'PHI', lat: 39.9055, lng: -75.1680, years: '1971-2003', current: false, aliases: ['The Vet'] },

    // Pittsburgh
    { id: 'three_rivers', name: 'Three Rivers Stadium', team: 'PIT', lat: 40.4467, lng: -80.0125, years: '1970-2000', current: false, aliases: [] },

    // Cincinnati
    { id: 'riverfront', name: 'Riverfront Stadium', team: 'CIN', lat: 39.0956, lng: -84.5069, years: '1970-2002', current: false, aliases: ['Cinergy Field'] },

    // Cleveland
    { id: 'municipal', name: 'Cleveland Stadium', team: 'CLE', lat: 41.5019, lng: -81.6994, years: '1932-1993', current: false, aliases: ['Cleveland Municipal Stadium', 'Lakefront Stadium'] },

    // Detroit
    { id: 'tiger', name: 'Tiger Stadium', team: 'DET', lat: 42.3317, lng: -83.0486, years: '1912-1999', current: false, aliases: ['Navin Field', 'Briggs Stadium'] },

    // Milwaukee
    { id: 'county', name: 'Milwaukee County Stadium', team: 'MIL', lat: 43.0301, lng: -87.9716, years: '1970-2000', current: false, aliases: [] },

    // San Francisco
    { id: 'candlestick', name: 'Candlestick Park', team: 'SF', lat: 37.7133, lng: -122.3863, years: '1960-1999', current: false, aliases: ['The Stick', '3Com Park'] },

    // Seattle
    { id: 'kingdome', name: 'Kingdome', team: 'SEA', lat: 47.5951, lng: -122.3316, years: '1977-1999', current: false, aliases: ['King County Domed Stadium'] },

    // Houston
    { id: 'astrodome', name: 'Astrodome', team: 'HOU', lat: 29.6847, lng: -95.4107, years: '1965-1999', current: false, aliases: ['Harris County Domed Stadium', 'Eighth Wonder of the World'] },

    // Montreal (defunct franchise location)
    { id: 'olympic', name: 'Olympic Stadium', team: 'MON', lat: 45.5579, lng: -73.5516, years: '1977-2004', current: false, aliases: ['Stade Olympique', 'The Big O'] },

    // San Diego
    { id: 'qualcomm', name: 'Qualcomm Stadium', team: 'SD', lat: 32.7831, lng: -117.1196, years: '1969-2003', current: false, aliases: ['San Diego Stadium', 'Jack Murphy Stadium'] },

    // === INTERNATIONAL VENUES ===
    { id: 'harp_helu', name: 'Estadio Alfredo Harp Helu', team: 'INT', lat: 19.3827, lng: -99.1503, years: '2019-present', current: true, aliases: ['Alfredo Harp Helu Stadium'], international: true, city: 'Mexico City' },
    { id: 'tokyo_dome', name: 'Tokyo Dome', team: 'INT', lat: 35.7056, lng: 139.7519, years: 'Various', current: true, aliases: ['Big Egg'], international: true, city: 'Tokyo' },
    { id: 'london', name: 'London Stadium', team: 'INT', lat: 51.5387, lng: -0.0166, years: '2019-present', current: true, aliases: ['Olympic Stadium London'], international: true, city: 'London' },
    { id: 'hiram_bithorn', name: 'Hiram Bithorn Stadium', team: 'INT', lat: 18.4271, lng: -66.0612, years: 'Various', current: true, aliases: [], international: true, city: 'San Juan' },
    { id: 'monterrey', name: 'Estadio de Beisbol Monterrey', team: 'INT', lat: 25.7261, lng: -100.3102, years: 'Various', current: true, aliases: ['Estadio Mobil Super'], international: true, city: 'Monterrey' },

    // === SPRING TRAINING FACILITIES ===
    // Arizona Cactus League
    { id: 'camelback', name: 'Camelback Ranch', team: 'ST', lat: 33.5052, lng: -112.3124, years: '2009-present', current: true, aliases: ['Camelback Ranch-Glendale'], springTraining: true, city: 'Glendale' },
    { id: 'saltriver', name: 'Salt River Fields at Talking Stick', team: 'ST', lat: 33.5463, lng: -111.8847, years: '2011-present', current: true, aliases: ['Salt River Fields'], springTraining: true, city: 'Scottsdale' },
    { id: 'goodyear', name: 'Goodyear Ballpark', team: 'ST', lat: 33.4253, lng: -112.3577, years: '2009-present', current: true, aliases: [], springTraining: true, city: 'Goodyear' },
    { id: 'peoria', name: 'Peoria Stadium', team: 'ST', lat: 33.5811, lng: -112.2712, years: '1994-present', current: true, aliases: ['Peoria Sports Complex'], springTraining: true, city: 'Peoria' },
    { id: 'sloan', name: 'Sloan Park', team: 'ST', lat: 33.4381, lng: -111.8366, years: '2014-present', current: true, aliases: [], springTraining: true, city: 'Mesa' },
    { id: 'scottsdale', name: 'Scottsdale Stadium', team: 'ST', lat: 33.4905, lng: -111.9210, years: '1992-present', current: true, aliases: [], springTraining: true, city: 'Scottsdale' },
    { id: 'tempe', name: 'Tempe Diablo Stadium', team: 'ST', lat: 33.4012, lng: -111.9728, years: '1968-present', current: true, aliases: [], springTraining: true, city: 'Tempe' },
    { id: 'surprise', name: 'Surprise Stadium', team: 'ST', lat: 33.6273, lng: -112.3678, years: '2003-present', current: true, aliases: [], springTraining: true, city: 'Surprise' },
    { id: 'hohokam', name: 'Hohokam Stadium', team: 'ST', lat: 33.4363, lng: -111.8259, years: '2015-present', current: true, aliases: [], springTraining: true, city: 'Mesa' },
    { id: 'maryvale', name: 'American Family Fields of Phoenix', team: 'ST', lat: 33.5098, lng: -112.1782, years: '1998-present', current: true, aliases: ['Maryvale Baseball Park'], springTraining: true, city: 'Phoenix' },
    // Florida Grapefruit League
    { id: 'edsmith', name: 'Ed Smith Stadium', team: 'ST', lat: 27.3372, lng: -82.5153, years: '1989-present', current: true, aliases: [], springTraining: true, city: 'Sarasota' },
    { id: 'jetblue', name: 'JetBlue Park', team: 'ST', lat: 26.5391, lng: -81.8413, years: '2012-present', current: true, aliases: ['JetBlue Park at Fenway South'], springTraining: true, city: 'Fort Myers' },
    { id: 'steinbrenner', name: 'George M. Steinbrenner Field', team: 'ST', lat: 27.9788, lng: -82.5033, years: '1996-present', current: true, aliases: ['Legends Field'], springTraining: true, city: 'Tampa' },
    { id: 'rogerdean', name: 'Roger Dean Chevrolet Stadium', team: 'ST', lat: 26.8926, lng: -80.1157, years: '1998-present', current: true, aliases: ['Roger Dean Stadium'], springTraining: true, city: 'Jupiter' },
    { id: 'clover', name: 'Clover Park', team: 'ST', lat: 27.3478, lng: -80.3511, years: '1988-present', current: true, aliases: ['First Data Field', 'Tradition Field', 'St. Lucie Sports Complex'], springTraining: true, city: 'Port St. Lucie' },
    { id: 'baycare', name: 'BayCare Ballpark', team: 'ST', lat: 27.9500, lng: -82.7342, years: '2004-present', current: true, aliases: ['Bright House Field', 'Spectrum Field'], springTraining: true, city: 'Clearwater' },
    { id: 'publix', name: 'Publix Field at Joker Marchant Stadium', team: 'ST', lat: 28.0615, lng: -81.9586, years: '1966-present', current: true, aliases: ['Joker Marchant Stadium'], springTraining: true, city: 'Lakeland' },
    { id: 'lecom', name: 'LECOM Park', team: 'ST', lat: 27.4972, lng: -82.5800, years: '1993-present', current: true, aliases: ['McKechnie Field'], springTraining: true, city: 'Bradenton' },
    { id: 'cooltoday', name: 'CoolToday Park', team: 'ST', lat: 27.0128, lng: -82.1273, years: '2019-present', current: true, aliases: [], springTraining: true, city: 'North Port' },
    { id: 'hammondsfd', name: 'Hammond Stadium', team: 'ST', lat: 26.5528, lng: -81.8626, years: '1991-present', current: true, aliases: ['CenturyLink Sports Complex'], springTraining: true, city: 'Fort Myers' },
];

// Build lookup maps for matching stadium names
const buildStadiumLookup = () => {
    const lookup = {};
    ALL_MLB_STADIUMS.forEach(stadium => {
        // Add primary name
        lookup[stadium.name.toLowerCase()] = stadium;
        // Add aliases
        stadium.aliases.forEach(alias => {
            lookup[alias.toLowerCase()] = stadium;
        });
    });
    return lookup;
};

const STADIUM_LOOKUP = buildStadiumLookup();

// Match a venue name to our stadium database
const matchStadiumByName = (venueName) => {
    if (!venueName) return null;
    const normalized = venueName.toLowerCase().trim();

    // Direct match
    if (STADIUM_LOOKUP[normalized]) return STADIUM_LOOKUP[normalized];

    // Partial match
    for (const [key, stadium] of Object.entries(STADIUM_LOOKUP)) {
        if (normalized.includes(key) || key.includes(normalized)) {
            return stadium;
        }
    }

    // Keyword matching for common terms
    const keywords = {
        'yankee': ['yankee3', 'yankee2'],
        'fenway': ['fenway'],
        'wrigley': ['wrigley'],
        'dodger': ['dodger'],
        'oracle': ['oracle'],
        'att park': ['oracle'],
        'petco': ['petco'],
        'citi field': ['citi'],
        'camden': ['camden'],
        'pnc': ['pnc'],
        'busch': ['busch3', 'busch2'],
        'kauffman': ['kauffman'],
        'coors': ['coors'],
        'chase': ['chase'],
        'truist': ['truist'],
        'suntrust': ['truist'],
        'minute maid': ['minutemaid'],
        'progressive': ['progressive'],
        'jacobs': ['progressive'],
        'comerica': ['comerica'],
        'target field': ['target'],
        'globe life': ['globelife2', 'globelife1'],
        't-mobile': ['tmobile'],
        'safeco': ['tmobile'],
        'angel stadium': ['angel'],
        'rogers': ['rogers'],
        'skydome': ['rogers'],
        'tropicana': ['tropicana'],
        'nationals park': ['nationals'],
        'citizens bank': ['citizens'],
        'american family': ['amfam'],
        'miller park': ['amfam'],
        'loandepot': ['loandepot'],
        'marlins park': ['loandepot'],
        'great american': ['gabp'],
        'guaranteed rate': ['guaranteed'],
        'cellular': ['guaranteed'],
        'coliseum': ['coliseum'],
        'oakland': ['coliseum'],
        'shea': ['shea'],
        'metrodome': ['metrodome'],
        'turner field': ['turner'],
        'rfk': ['rfk'],
        'harp': ['harp_helu'],
        'mexico': ['harp_helu'],
        'tokyo': ['tokyo_dome'],
        'london': ['london'],
    };

    for (const [keyword, stadiumIds] of Object.entries(keywords)) {
        if (normalized.includes(keyword)) {
            const stadium = ALL_MLB_STADIUMS.find(s => stadiumIds.includes(s.id));
            if (stadium) return stadium;
        }
    }

    return null;
};

const StadiumMap = ({ stadiums, games, orioles }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markersRef = useRef([]);
    const [filter, setFilter] = useState('all'); // 'all', 'current', 'historical', 'international'
    const [selectedStadium, setSelectedStadium] = useState(null);

    // Build visited stadiums data from your actual stadium data
    const visitedData = useMemo(() => {
        const visited = {};

        // Process stadiums you've been to
        (stadiums || []).forEach(s => {
            const match = matchStadiumByName(s.stadium);
            if (match) {
                visited[match.id] = {
                    ...s,
                    stadiumInfo: match,
                    hasVisited: true,
                };
            }
        });

        // Add Orioles data
        (orioles || []).forEach(o => {
            const match = matchStadiumByName(o.stadium);
            if (match) {
                if (visited[match.id]) {
                    visited[match.id].sawOrioles = true;
                    visited[match.id].oriolesRecord = o.record;
                    visited[match.id].oriolesGames = o.games;
                } else {
                    visited[match.id] = {
                        stadiumInfo: match,
                        hasVisited: true,
                        sawOrioles: true,
                        oriolesRecord: o.record,
                        oriolesGames: o.games,
                    };
                }
            }
        });

        return visited;
    }, [stadiums, orioles]);

    // Filter stadiums based on selection
    const filteredStadiums = useMemo(() => {
        return ALL_MLB_STADIUMS.filter(s => {
            const hasVisited = visitedData[s.id]?.hasVisited;

            // Always show visited stadiums (including spring training if visited)
            if (hasVisited) {
                if (filter === 'current') return s.current && !s.international && !s.springTraining;
                if (filter === 'historical') return !s.current && !s.springTraining;
                if (filter === 'international') return s.international;
                if (filter === 'spring') return s.springTraining;
                return true;
            }

            // For unvisited stadiums: only show current MLB stadiums (not spring training, international, or defunct)
            if (!hasVisited) {
                if (filter === 'historical' || filter === 'international' || filter === 'spring') return false;
                return s.current && !s.international && !s.springTraining;
            }

            return false;
        });
    }, [filter, visitedData]);

    // Calculate stats (exclude spring training from 30-stadium goal)
    const stats = useMemo(() => {
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const visitedCurrent = currentStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        const oriolesCurrent = currentStadiums.filter(s => visitedData[s.id]?.sawOrioles).length;
        const totalVisited = Object.values(visitedData).filter(v => v.hasVisited).length;
        const totalOrioles = Object.values(visitedData).filter(v => v.sawOrioles).length;
        const springVisited = ALL_MLB_STADIUMS.filter(s => s.springTraining && visitedData[s.id]?.hasVisited).length;

        return {
            currentTotal: currentStadiums.length,
            visitedCurrent,
            oriolesCurrent,
            totalVisited,
            totalOrioles,
            springVisited,
            percentCurrent: Math.round((visitedCurrent / currentStadiums.length) * 100),
            percentOrioles: Math.round((oriolesCurrent / currentStadiums.length) * 100),
        };
    }, [visitedData]);

    // Initialize map
    useEffect(() => {
        if (!mapRef.current || mapInstanceRef.current) return;

        const map = L.map(mapRef.current).setView([39.8283, -98.5795], 4);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        mapInstanceRef.current = map;

        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, []);

    // Update markers
    useEffect(() => {
        if (!mapInstanceRef.current) return;

        // Clear existing markers
        markersRef.current.forEach(m => m.remove());
        markersRef.current = [];

        filteredStadiums.forEach(stadium => {
            const data = visitedData[stadium.id];
            const hasVisited = data?.hasVisited;
            const sawOrioles = data?.sawOrioles;
            const isSpringTraining = stadium.springTraining;

            // Determine marker color
            let fillColor = '#9ca3af'; // gray - not visited
            let borderColor = '#6b7280';
            if (hasVisited && isSpringTraining) {
                fillColor = '#06b6d4'; // cyan - spring training visited
                borderColor = '#0891b2';
            } else if (sawOrioles) {
                fillColor = '#f97316'; // orange - saw Orioles
                borderColor = '#ea580c';
            } else if (hasVisited) {
                fillColor = '#22c55e'; // green - visited
                borderColor = '#16a34a';
            }

            const marker = L.circleMarker([stadium.lat, stadium.lng], {
                radius: hasVisited ? 10 : 7,
                fillColor: fillColor,
                color: borderColor,
                weight: 2,
                opacity: 1,
                fillOpacity: hasVisited ? 0.9 : 0.4
            }).addTo(mapInstanceRef.current);

            // Build popup content
            let statusText = '<span style="color: #9ca3af;">Not yet visited</span>';
            let detailsHtml = '';
            let teamLabel = stadium.team;

            if (hasVisited) {
                if (isSpringTraining) {
                    statusText = '<span style="color: #06b6d4; font-weight: bold;">Spring Training' + (sawOrioles ? ' + Orioles' : '') + '</span>';
                    teamLabel = 'Spring Training';
                } else if (sawOrioles) {
                    statusText = '<span style="color: #f97316; font-weight: bold;">Visited + Saw Orioles</span>';
                    if (data.oriolesRecord) {
                        detailsHtml += `<div><strong>O's Record:</strong> ${data.oriolesRecord}</div>`;
                    }
                } else {
                    statusText = '<span style="color: #22c55e; font-weight: bold;">Visited</span>';
                }

                if (data.games) {
                    detailsHtml += `<div><strong>Games:</strong> ${data.games}</div>`;
                }
                if (data.firstVisit) {
                    detailsHtml += `<div><strong>First:</strong> ${data.firstVisit}</div>`;
                }
                if (data.lastVisit) {
                    detailsHtml += `<div><strong>Last:</strong> ${data.lastVisit}</div>`;
                }
            }

            const popupContent =
                '<div style="min-width: 200px;">' +
                    '<h3 style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">' + stadium.name + '</h3>' +
                    '<div style="font-size: 11px; color: #666; margin-bottom: 8px;">' +
                        teamLabel + (stadium.international ? ' - ' + stadium.city : '') + ' | ' + stadium.years +
                        (stadium.current ? '' : isSpringTraining ? '' : ' (Defunct)') +
                    '</div>' +
                    '<div style="font-size: 12px; margin-bottom: 6px;">' + statusText + '</div>' +
                    (detailsHtml ? '<div style="font-size: 12px; line-height: 1.5; border-top: 1px solid #eee; padding-top: 6px;">' + detailsHtml + '</div>' : '') +
                '</div>';

            marker.bindPopup(popupContent, { className: 'stadium-popup' });
            marker.on('click', () => setSelectedStadium(stadium));
            markersRef.current.push(marker);
        });
    }, [filteredStadiums, visitedData]);

    return (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="p-4 border-b">
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <h2 className="section-title font-bold text-slate-900">🗺️ Stadium Checklist</h2>

                    <div className="flex items-center gap-4">
                        <select
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="px-3 py-2 border rounded-lg body-text"
                        >
                            <option value="all">All Stadiums</option>
                            <option value="current">Current (30 MLB)</option>
                            <option value="historical">Historical/Defunct</option>
                            <option value="international">International</option>
                        </select>
                    </div>
                </div>

                {/* Legend */}
                <div className="mt-3 flex flex-wrap items-center gap-4 text-sm">
                    <span className="text-slate-600">Legend:</span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-slate-400 opacity-40"></span>
                        <span className="text-slate-600">Not Visited</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-green-500"></span>
                        <span className="text-slate-600">Visited</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-orange-500"></span>
                        <span className="text-slate-600">Visited + Saw Orioles</span>
                    </span>
                </div>
            </div>

            {/* Map Container */}
            <div ref={mapRef} style={{ height: '500px', width: '100%' }}></div>

            {/* Progress Stats */}
            <div className="p-4 border-t bg-slate-50">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">{stats.visitedCurrent}/{stats.currentTotal}</div>
                        <div className="small-text text-slate-600">Current Stadiums</div>
                        <div className="text-xs text-slate-400">{stats.percentCurrent}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-500">{stats.oriolesCurrent}/{stats.currentTotal}</div>
                        <div className="small-text text-slate-600">Saw Orioles</div>
                        <div className="text-xs text-slate-400">{stats.percentOrioles}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">{stats.totalVisited}</div>
                        <div className="small-text text-slate-600">Total Stadiums</div>
                        <div className="text-xs text-slate-400">Including historical</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">{stats.totalOrioles}</div>
                        <div className="small-text text-slate-600">O's Venues</div>
                        <div className="text-xs text-slate-400">Total Orioles venues</div>
                    </div>
                </div>
            </div>

            {/* Stadium Checklist */}
            <div className="p-4 border-t max-h-80 overflow-y-auto">
                {/* Visited Stadiums */}
                {(() => {
                    const visitedStadiums = filteredStadiums.filter(s => visitedData[s.id]?.hasVisited);
                    if (visitedStadiums.length === 0) return null;
                    return (
                        <div className="mb-4">
                            <h3 className="font-semibold text-slate-700 mb-3">
                                Visited Stadiums
                                <span className="text-sm font-normal text-slate-500 ml-2">({visitedStadiums.length})</span>
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                {visitedStadiums.map(stadium => {
                                    const data = visitedData[stadium.id];
                                    const sawOrioles = data?.sawOrioles;
                                    return (
                                        <div
                                            key={stadium.id}
                                            className={`flex items-center gap-2 p-2 rounded text-sm ${
                                                sawOrioles ? 'bg-orange-50 border border-orange-200' : 'bg-green-50 border border-green-200'
                                            }`}
                                        >
                                            <span className="text-lg">{sawOrioles ? '🧡' : '✅'}</span>
                                            <div className="flex-1 min-w-0">
                                                <div className="font-medium truncate text-slate-900">{stadium.name}</div>
                                                <div className="text-xs text-slate-500">
                                                    {stadium.team} {!stadium.current && '(Defunct)'}
                                                    {data.games && ` • ${data.games} games`}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })()}

                {/* Still To Visit (Current stadiums only) */}
                {(() => {
                    const toVisit = filteredStadiums.filter(s => s.current && !s.international && !visitedData[s.id]?.hasVisited);
                    if (toVisit.length === 0) return null;
                    return (
                        <div>
                            <h3 className="font-semibold text-slate-700 mb-3">
                                Still To Visit
                                <span className="text-sm font-normal text-slate-500 ml-2">({toVisit.length} remaining)</span>
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                {toVisit.map(stadium => (
                                    <div
                                        key={stadium.id}
                                        className="flex items-center gap-2 p-2 rounded text-sm bg-slate-50 border border-slate-200"
                                    >
                                        <span className="text-lg opacity-30">⬜</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium truncate text-slate-400">{stadium.name}</div>
                                            <div className="text-xs text-slate-400">{stadium.team}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })()}
            </div>
        </div>
    );
};

// === MLB DIVISIONS CONSTANT ===
const MLB_DIVISIONS = {
    'AL East': ['BAL', 'BOS', 'NYA', 'TBA', 'TOR'],
    'AL Central': ['CHA', 'CLE', 'DET', 'KCA', 'MIN'],
    'AL West': ['ANA', 'HOU', 'ATH', 'SEA', 'TEX'],
    'NL East': ['ATL', 'MIA', 'NYN', 'PHI', 'WAS'],
    'NL Central': ['CHN', 'CIN', 'MIL', 'PIT', 'SLN'],
    'NL West': ['ARI', 'COL', 'LAN', 'SDN', 'SFN'],
};

// Map stadium team codes to retrosheet division codes
const STADIUM_TO_DIVISION_CODE = {
    'LAD': 'LAN', 'LA': 'LAN', 'NYM': 'NYN', 'SD': 'SDN', 'SF': 'SFN',
    'NYY': 'NYA', 'TB': 'TBA', 'CWS': 'CHA', 'CHW': 'CHA', 'KC': 'KCA', 'LAA': 'ANA',
    'STL': 'SLN', 'CHC': 'CHN', 'WSH': 'WAS', 'WSN': 'WAS', 'FLA': 'MIA',
    // Pass through codes that already match
    'BAL': 'BAL', 'BOS': 'BOS', 'TOR': 'TOR', 'CLE': 'CLE', 'DET': 'DET',
    'MIN': 'MIN', 'HOU': 'HOU', 'OAK': 'ATH', 'ATH': 'ATH', 'SEA': 'SEA', 'TEX': 'TEX',
    'ATL': 'ATL', 'MIA': 'MIA', 'PHI': 'PHI', 'CIN': 'CIN', 'MIL': 'MIL',
    'PIT': 'PIT', 'ARI': 'ARI', 'COL': 'COL',
};

const TEAM_CODE_TO_NAME = {
    // Retrosheet codes
    'BAL': 'Baltimore Orioles', 'BOS': 'Boston Red Sox', 'NYA': 'New York Yankees',
    'TBA': 'Tampa Bay Rays', 'TOR': 'Toronto Blue Jays', 'CHA': 'Chicago White Sox',
    'CLE': 'Cleveland Guardians', 'DET': 'Detroit Tigers', 'KCA': 'Kansas City Royals',
    'MIN': 'Minnesota Twins', 'ANA': 'Los Angeles Angels', 'HOU': 'Houston Astros',
    'OAK': 'Oakland Athletics', 'ATH': 'Athletics', 'SEA': 'Seattle Mariners', 'TEX': 'Texas Rangers',
    'ATL': 'Atlanta Braves', 'MIA': 'Miami Marlins', 'NYN': 'New York Mets',
    'PHI': 'Philadelphia Phillies', 'WAS': 'Washington Nationals', 'CHN': 'Chicago Cubs',
    'CIN': 'Cincinnati Reds', 'MIL': 'Milwaukee Brewers', 'PIT': 'Pittsburgh Pirates',
    'SLN': 'St. Louis Cardinals', 'ARI': 'Arizona Diamondbacks', 'COL': 'Colorado Rockies',
    'LAN': 'Los Angeles Dodgers', 'SDN': 'San Diego Padres', 'SFN': 'San Francisco Giants',
    // Common abbreviations (for display when these appear in data)
    'NYY': 'New York Yankees', 'NYM': 'New York Mets', 'SF': 'San Francisco Giants',
    'LAD': 'Los Angeles Dodgers', 'SD': 'San Diego Padres', 'STL': 'St. Louis Cardinals',
    'TB': 'Tampa Bay Rays', 'KC': 'Kansas City Royals', 'CWS': 'Chicago White Sox',
    'CHC': 'Chicago Cubs', 'WSH': 'Washington Nationals', 'LAA': 'Los Angeles Angels',
    'ATH': 'Athletics', 'FLA': 'Florida Marlins',
};

// Team code aliases - map common abbreviations to Retrosheet codes for tracking
const TEAM_CODE_ALIASES = {
    // Relocated/renamed teams
    'OAK': 'ATH',  // Oakland Athletics -> Athletics (Sacramento 2025+)
    'FLA': 'MIA',  // Florida Marlins -> Miami Marlins
    'FLO': 'MIA',  // Florida Marlins alternate code
    'MON': 'WAS',  // Montreal Expos -> Washington Nationals
    // Common abbreviations -> Retrosheet codes
    'NYY': 'NYA',  // New York Yankees
    'NYM': 'NYN',  // New York Mets
    'SF': 'SFN',   // San Francisco Giants
    'LAD': 'LAN',  // Los Angeles Dodgers
    'SD': 'SDN',   // San Diego Padres
    'STL': 'SLN',  // St. Louis Cardinals
    'TB': 'TBA',   // Tampa Bay Rays
    'KC': 'KCA',   // Kansas City Royals
    'CWS': 'CHA',  // Chicago White Sox
    'CHC': 'CHN',  // Chicago Cubs
    'WSH': 'WAS',  // Washington Nationals
    'LAA': 'ANA',  // Los Angeles Angels
    'CAL': 'ANA',  // California Angels
};

const normalizeTeamCode = (code) => TEAM_CODE_ALIASES[code] || code;

// Milestone thresholds
const MILESTONE_COUNTS = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 75, 100, 150, 200];
const GAME_MILESTONES = [1, 10, 25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 750, 1000];

// Holiday detection
const getHoliday = (dateStr) => {
    if (!dateStr) return null;
    let month, day;
    if (dateStr.includes('/')) {
        const parts = dateStr.split('/');
        month = parts[0].padStart(2, '0');
        day = parts[1].padStart(2, '0');
    } else if (dateStr.length >= 8) {
        month = dateStr.substring(4, 6);
        day = dateStr.substring(6, 8);
    } else {
        return null;
    }
    const mmdd = month + day;

    const holidays = {
        '0704': 'July 4th',
        '1031': 'Halloween',
        '0317': "St. Patrick's Day",
        '0214': "Valentine's Day",
        '0101': "New Year's Day",
    };

    return holidays[mmdd] || null;
};

const ordinal = (n) => {
    const s = ['th', 'st', 'nd', 'rd'];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
};

// Compute badges/milestones for each game
const computeGameMilestones = (games) => {
    if (!games || games.length === 0) return { milestones: {}, tracking: {} };

    // Sort games chronologically
    const sortedGames = [...games].sort((a, b) => {
        const dateA = a.date || '';
        const dateB = b.date || '';
        const parseDate = toSortableDate;
        return parseDate(dateA).localeCompare(parseDate(dateB));
    });

    const gameMilestones = {};
    let gameCount = 0;
    const teamCounts = {};
    const venueCounts = {};
    const matchupsSeen = {};
    const divisionTeamsSeen = {};
    const divisionTeamsCompleted = {};
    const divisionStadiumsVisited = {};
    const divisionStadiumsCompleted = {};
    const venueOrder = [];

    // Initialize division tracking
    Object.keys(MLB_DIVISIONS).forEach(div => {
        divisionTeamsSeen[div] = new Set();
        divisionStadiumsVisited[div] = new Set();
    });

    sortedGames.forEach(game => {
        const gameId = game.gameId;
        if (!gameId) return;

        gameMilestones[gameId] = { badges: [] };
        gameCount++;

        // awayTeam and homeTeam are team codes - normalize for relocated teams (ATH -> OAK, etc.)
        const awayCode = normalizeTeamCode(game.awayTeam || '');
        const homeCode = normalizeTeamCode(game.homeTeam || '');
        const venue = game.venue || '';
        const dateStr = game.date || '';

        // Get team names for display
        const awayName = TEAM_CODE_TO_NAME[awayCode] || awayCode;
        const homeName = TEAM_CODE_TO_NAME[homeCode] || homeCode;

        // Get divisions
        const getDivision = (code) => {
            for (const [div, teams] of Object.entries(MLB_DIVISIONS)) {
                if (teams.includes(code)) return div;
            }
            return null;
        };

        const awayDiv = getDivision(awayCode);
        const homeDiv = getDivision(homeCode);

        // Game count milestone
        if (GAME_MILESTONES.includes(gameCount)) {
            gameMilestones[gameId].badges.push({
                type: 'game-count',
                text: `Game #${gameCount}`,
                title: `${ordinal(gameCount)} game attended`
            });
        }

        // Holiday badge
        const holiday = getHoliday(dateStr);
        if (holiday) {
            gameMilestones[gameId].badges.push({
                type: 'holiday',
                text: holiday,
                title: `${holiday} game`
            });
        }

        // Track first team from each division
        if (awayDiv && divisionTeamsSeen[awayDiv].size === 0) {
            gameMilestones[gameId].badges.push({
                type: 'div-first',
                text: `1st ${awayDiv}`,
                title: `First ${awayDiv} team seen: ${awayName}`
            });
        }
        if (homeDiv && homeDiv !== awayDiv && divisionTeamsSeen[homeDiv].size === 0) {
            gameMilestones[gameId].badges.push({
                type: 'div-first',
                text: `1st ${homeDiv}`,
                title: `First ${homeDiv} team seen: ${homeName}`
            });
        }

        // Track team counts and milestones
        if (awayCode) {
            teamCounts[awayCode] = (teamCounts[awayCode] || 0) + 1;
            if (MILESTONE_COUNTS.includes(teamCounts[awayCode])) {
                gameMilestones[gameId].badges.push({
                    type: 'team',
                    text: teamCounts[awayCode] === 1 ? `1st ${awayName}` : `${awayName} #${teamCounts[awayCode]}`,
                    title: `${ordinal(teamCounts[awayCode])} time seeing ${awayName}`
                });
            }
        }
        if (homeCode) {
            teamCounts[homeCode] = (teamCounts[homeCode] || 0) + 1;
            if (MILESTONE_COUNTS.includes(teamCounts[homeCode])) {
                gameMilestones[gameId].badges.push({
                    type: 'team',
                    text: teamCounts[homeCode] === 1 ? `1st ${homeName}` : `${homeName} #${teamCounts[homeCode]}`,
                    title: `${ordinal(teamCounts[homeCode])} time seeing ${homeName}`
                });
            }
        }

        // Track division completion (teams)
        if (awayDiv) divisionTeamsSeen[awayDiv].add(awayCode);
        if (homeDiv) divisionTeamsSeen[homeDiv].add(homeCode);

        // Check for division team completion
        [awayDiv, homeDiv].forEach(div => {
            if (!div || divisionTeamsCompleted[div]) return;
            const totalTeams = MLB_DIVISIONS[div].length;
            if (divisionTeamsSeen[div].size >= totalTeams) {
                divisionTeamsCompleted[div] = true;
                gameMilestones[gameId].badges.push({
                    type: 'div-complete',
                    text: `${div} Teams!`,
                    title: `Seen all ${totalTeams} ${div} teams!`
                });
            }
        });

        // Venue tracking - normalize stadium names (AT&T Park -> Oracle Park, etc.)
        if (venue) {
            const matchedStadium = matchStadiumByName(venue);
            const normalizedVenue = matchedStadium ? matchedStadium.name : venue;

            const isFirstVenueVisit = !venueCounts[normalizedVenue];
            venueCounts[normalizedVenue] = (venueCounts[normalizedVenue] || 0) + 1;

            if (isFirstVenueVisit) {
                venueOrder.push(normalizedVenue);
                const venueNum = venueOrder.length;
                gameMilestones[gameId].badges.push({
                    type: 'venue',
                    text: `${normalizedVenue} (#${venueNum})`,
                    title: `${ordinal(venueNum)} different venue visited`
                });

                // Track stadium division completion (only count if it's actually the home team's home stadium)
                // Track by team code, not venue name, so multiple stadiums for same team count as one
                if (matchedStadium && matchedStadium.team) {
                    const divisionCode = STADIUM_TO_DIVISION_CODE[matchedStadium.team] || matchedStadium.team;
                    const stadiumTeamDiv = Object.entries(MLB_DIVISIONS).find(([div, teams]) => teams.includes(divisionCode))?.[0];
                    if (stadiumTeamDiv) {
                        // Use divisionCode (team) instead of venue name so old/new stadiums for same team count as one
                        divisionStadiumsVisited[stadiumTeamDiv].add(divisionCode);
                        // Check if all stadiums in division visited
                        if (!divisionStadiumsCompleted[stadiumTeamDiv]) {
                            const totalStadiums = MLB_DIVISIONS[stadiumTeamDiv].length;
                            if (divisionStadiumsVisited[stadiumTeamDiv].size >= totalStadiums) {
                                divisionStadiumsCompleted[stadiumTeamDiv] = true;
                                gameMilestones[gameId].badges.push({
                                    type: 'div-stadiums',
                                    text: `${stadiumTeamDiv} Stadiums!`,
                                    title: `Visited all ${totalStadiums} ${stadiumTeamDiv} stadiums!`
                                });
                            }
                        }
                    }
                }
            } else if (MILESTONE_COUNTS.includes(venueCounts[normalizedVenue])) {
                gameMilestones[gameId].badges.push({
                    type: 'venue',
                    text: `${normalizedVenue} #${venueCounts[normalizedVenue]}`,
                    title: `${ordinal(venueCounts[normalizedVenue])} game at ${normalizedVenue}`
                });
            }
        }

        // First matchup tracking
        const matchupKey = [awayCode, homeCode].sort().join(' vs ');
        if (!matchupsSeen[matchupKey]) {
            matchupsSeen[matchupKey] = true;
            gameMilestones[gameId].badges.push({
                type: 'matchup',
                text: '1st Matchup',
                title: `First time seeing ${awayName} vs ${homeName}`
            });
        }
    });

    return {
        milestones: gameMilestones,
        tracking: {
            teamCounts,
            venueCounts,
            venueOrder,
            divisionTeamsSeen: Object.fromEntries(
                Object.entries(divisionTeamsSeen).map(([k, v]) => [k, Array.from(v)])
            ),
            divisionStadiumsVisited: Object.fromEntries(
                Object.entries(divisionStadiumsVisited).map(([k, v]) => [k, Array.from(v)])
            ),
            divisionTeamsCompleted,
            divisionStadiumsCompleted,
            matchupsSeen,
            totalGames: gameCount
        }
    };
};

// Division Checklist Component
const DivisionChecklist = ({ divisionChecklist, games }) => {
    const [selectedGroup, setSelectedGroup] = useState('All MLB');
    const [viewMode, setViewMode] = useState('teams');

    const milestoneData = useMemo(() => computeGameMilestones(games), [games]);
    const tracking = milestoneData.tracking || {};

    const groups = ['All MLB', 'AL', 'NL', 'AL East', 'AL Central', 'AL West', 'NL East', 'NL Central', 'NL West'];

    const currentData = divisionChecklist?.[selectedGroup] || { teams: [], teamsSeen: 0, totalTeams: 0 };

    const teamProgress = currentData.totalTeams > 0
        ? Math.round((currentData.teamsSeen / currentData.totalTeams) * 100)
        : 0;
    const stadiumProgress = currentData.totalStadiums > 0
        ? Math.round((currentData.stadiumsVisited / currentData.totalStadiums) * 100)
        : 0;

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b">
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <h2 className="section-title font-bold">Division Checklist</h2>
                    <div className="flex items-center gap-4">
                        <select
                            value={selectedGroup}
                            onChange={(e) => setSelectedGroup(e.target.value)}
                            className="px-3 py-2 border rounded-lg"
                        >
                            {groups.map(g => (
                                <option key={g} value={g}>{g}</option>
                            ))}
                        </select>
                        <div className="flex border rounded-lg overflow-hidden">
                            <button
                                onClick={() => setViewMode('teams')}
                                className={`px-3 py-2 ${viewMode === 'teams' ? 'bg-blue-500 text-white' : 'bg-slate-100'}`}
                            >
                                Teams
                            </button>
                            <button
                                onClick={() => setViewMode('stadiums')}
                                className={`px-3 py-2 ${viewMode === 'stadiums' ? 'bg-blue-500 text-white' : 'bg-slate-100'}`}
                            >
                                Stadiums
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Progress Summary */}
            <div className="p-4 bg-slate-50 border-b">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">
                            {currentData.teamsSeen}/{currentData.totalTeams}
                        </div>
                        <div className="text-sm text-slate-600">Teams Seen</div>
                        <div className="text-xs text-slate-400">{teamProgress}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">
                            {currentData.stadiumsVisited}/{currentData.totalStadiums}
                        </div>
                        <div className="text-sm text-slate-600">Stadiums Visited</div>
                        <div className="text-xs text-slate-400">{stadiumProgress}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">
                            {Object.keys(tracking.divisionTeamsCompleted || {}).length}/6
                        </div>
                        <div className="text-sm text-slate-600">Div. Teams</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-indigo-600">
                            {Object.keys(tracking.divisionStadiumsCompleted || {}).length}/6
                        </div>
                        <div className="text-sm text-slate-600">Div. Stadiums</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-600">
                            {tracking.totalGames || games?.length || 0}
                        </div>
                        <div className="text-sm text-slate-600">Total Games</div>
                    </div>
                </div>
            </div>

            {/* Team/Stadium Grid */}
            <div className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {(currentData.teams || []).map(team => {
                        const isSeen = viewMode === 'teams' ? team.seen : team.stadiumVisited;
                        const count = viewMode === 'teams' ? team.visitCount : team.stadiumVisitCount;
                        const displayName = viewMode === 'teams' ? team.teamName : team.homeStadium;

                        return (
                            <div
                                key={team.teamCode}
                                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:shadow-sm transition-all ${
                                    isSeen
                                        ? 'bg-green-50 border-green-200 hover:border-green-300'
                                        : 'bg-slate-50 border-slate-200 hover:border-slate-300'
                                }`}
                                onClick={() => {
                                    if (isSeen) {
                                        if (viewMode === 'teams') window.__navigateTab('progress', 'matchups');
                                        else window.__navigateTab('venues');
                                    }
                                }}
                            >
                                <span className="text-2xl">{isSeen ? '✅' : '⬜'}</span>
                                <div className="flex-1 min-w-0">
                                    <div className={`font-medium truncate ${!isSeen ? 'text-slate-400' : 'text-blue-700'}`}>
                                        {displayName || 'Unknown'}
                                    </div>
                                    <div className="text-xs text-slate-500">
                                        {viewMode === 'teams' ? team.division : team.teamName}
                                        {isSeen && count > 0 && ` • ${count} ${count === 1 ? 'game' : 'games'}`}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Division Progress Cards */}
            {selectedGroup === 'All MLB' && (
                <div className="p-4 border-t">
                    <h3 className="font-semibold text-slate-700 mb-4">Division Progress</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {['AL East', 'AL Central', 'AL West', 'NL East', 'NL Central', 'NL West'].map(div => {
                            const divData = divisionChecklist?.[div] || {};
                            const pct = divData.totalTeams > 0
                                ? Math.round((divData.teamsSeen / divData.totalTeams) * 100)
                                : 0;
                            const isComplete = divData.teamsSeen >= divData.totalTeams;

                            return (
                                <div
                                    key={div}
                                    onClick={() => setSelectedGroup(div)}
                                    className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                                        isComplete ? 'bg-green-50 border-green-300' : 'bg-white border-slate-200'
                                    }`}
                                >
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-semibold">{div}</span>
                                        <span className="text-sm">{divData.teamsSeen}/{divData.totalTeams}</span>
                                    </div>
                                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all ${
                                                isComplete ? 'bg-green-500' : 'bg-blue-500'
                                            }`}
                                            style={{ width: `${pct}%` }}
                                        />
                                    </div>
                                    {isComplete && (
                                        <div className="text-xs text-green-600 mt-1 font-medium">Complete!</div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

// Badges Display Component
const BadgesDisplay = ({ games }) => {
    const [filter, setFilter] = useState('all');
    const milestoneData = useMemo(() => computeGameMilestones(games), [games]);

    // Collect all badges
    const allBadges = useMemo(() => {
        const badges = [];
        const sortedGames = [...(games || [])].sort((a, b) => toSortableDate(b.date).localeCompare(toSortableDate(a.date)));

        sortedGames.forEach(game => {
            const gameBadges = milestoneData.milestones?.[game.gameId]?.badges || [];
            gameBadges.forEach(badge => {
                badges.push({
                    ...badge,
                    date: game.date,
                    gameId: game.gameId,
                    away: game.awayTeam,
                    home: game.homeTeam,
                    venue: game.venue
                });
            });
        });

        return badges;
    }, [games, milestoneData]);

    const filteredBadges = useMemo(() => {
        if (filter === 'all') return allBadges;
        return allBadges.filter(b => b.type === filter);
    }, [allBadges, filter]);

    const badgeCounts = useMemo(() => {
        const counts = { all: allBadges.length };
        allBadges.forEach(b => {
            counts[b.type] = (counts[b.type] || 0) + 1;
        });
        return counts;
    }, [allBadges]);

    const getBadgeIcon = (type) => {
        const icons = {
            'game-count': '🎮',
            'team': '👕',
            'venue': '🏟️',
            'div-first': '🌟',
            'div-complete': '🏆',
            'matchup': '⚔️',
            'holiday': '🎉',
        };
        return icons[type] || '🏅';
    };

    const getBadgeColor = (type) => {
        const colors = {
            'game-count': 'bg-purple-100 border-purple-300',
            'team': 'bg-blue-100 border-blue-300',
            'venue': 'bg-green-100 border-green-300',
            'div-first': 'bg-yellow-100 border-yellow-300',
            'div-complete': 'bg-orange-100 border-orange-300',
            'matchup': 'bg-pink-100 border-pink-300',
            'holiday': 'bg-red-100 border-red-300',
            'div-stadiums': 'bg-indigo-100 border-indigo-300',
        };
        return colors[type] || 'bg-slate-100 border-slate-300';
    };

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b">
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <h2 className="section-title font-bold">Badges & Milestones</h2>
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="px-3 py-2 border rounded-lg"
                    >
                        <option value="all">All Badges ({badgeCounts.all})</option>
                        <option value="game-count">Game Count ({badgeCounts['game-count'] || 0})</option>
                        <option value="team">Team Milestones ({badgeCounts['team'] || 0})</option>
                        <option value="venue">Venue ({badgeCounts['venue'] || 0})</option>
                        <option value="div-first">Division Firsts ({badgeCounts['div-first'] || 0})</option>
                        <option value="div-complete">Div. Teams Complete ({badgeCounts['div-complete'] || 0})</option>
                        <option value="div-stadiums">Div. Stadiums Complete ({badgeCounts['div-stadiums'] || 0})</option>
                        <option value="matchup">First Matchups ({badgeCounts['matchup'] || 0})</option>
                        <option value="holiday">Holiday Games ({badgeCounts['holiday'] || 0})</option>
                    </select>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="p-4 bg-slate-50 border-b">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">{badgeCounts.all}</div>
                        <div className="text-sm text-slate-600">Total Badges</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">{badgeCounts['div-complete'] || 0}</div>
                        <div className="text-sm text-slate-600">Divisions Complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">{milestoneData.tracking?.venueOrder?.length || 0}</div>
                        <div className="text-sm text-slate-600">Unique Venues</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-600">{Object.keys(milestoneData.tracking?.matchupsSeen || {}).length}</div>
                        <div className="text-sm text-slate-600">Unique Matchups</div>
                    </div>
                </div>
            </div>

            {/* Badges Grid */}
            <div className="p-4 max-h-[600px] overflow-y-auto">
                {filteredBadges.length === 0 ? (
                    <EmptyState
                        icon="🏅"
                        title="No badges yet"
                        message="Keep attending games to earn badges!"
                    />
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {filteredBadges.map((badge, idx) => (
                            <div
                                key={`${badge.gameId}-${badge.type}-${idx}`}
                                className={`p-3 rounded-lg border ${getBadgeColor(badge.type)} cursor-pointer hover:shadow-md transition-all`}
                                title={badge.title}
                                onClick={() => { window._pendingGameId = badge.gameId; if (window.__navigateTab) window.__navigateTab('gamelog'); }}
                            >
                                <div className="flex items-start gap-3">
                                    <span className="text-2xl">{getBadgeIcon(badge.type)}</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold text-slate-800 truncate">{badge.text}</div>
                                        <div className="text-xs text-slate-600 truncate">{badge.away} vs {badge.home}</div>
                                        <div className="text-xs text-slate-400 mt-1">{badge.date}</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

// Error Boundary to catch rendering errors gracefully
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, info) {
        console.error('React Error Boundary caught:', error, info);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-slate-50">
                    <div className="bg-white rounded-xl shadow-lg p-8 max-w-lg text-center">
                        <h2 className="text-xl font-bold text-red-600 mb-4">Something went wrong</h2>
                        <p className="text-slate-600 mb-4">{this.state.error?.message || 'An unexpected error occurred while rendering.'}</p>
                        <button onClick={() => { this.setState({ hasError: false, error: null }); }} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 mr-2">Try Again</button>
                        <button onClick={() => window.location.reload()} className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300">Reload Page</button>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}

const UmpireTracker = ({ umpireLog, games }) => {
    const [search, setSearch] = useState('');
    const [expandedUmpire, setExpandedUmpire] = useState(null);
    const [sortKey, setSortKey] = useState('games');
    const [sortDir, setSortDir] = useState('desc');

    const gameMap = useMemo(() => {
        const map = {};
        (games || []).forEach(g => { if (g.gameId) map[g.gameId] = g; });
        return map;
    }, [games]);

    useEffect(() => {
        if (window._pendingUmpireSearch) {
            setSearch(window._pendingUmpireSearch);
            window._pendingUmpireSearch = null;
        }
    }, []);

    const toSortDate = toSortableDate;
    const handleSort = (key) => { if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc'); else { setSortKey(key); setSortDir(key === 'name' ? 'asc' : 'desc'); } };

    const filtered = useMemo(() => {
        let list = umpireLog;
        if (search) {
            const q = search.toLowerCase();
            list = list.filter(u => u.name.toLowerCase().includes(q));
        }
        return [...list].sort((a, b) => {
            let aVal, bVal;
            if (sortKey === 'name') { aVal = a.name; bVal = b.name; }
            else if (sortKey === 'games') { aVal = a.games; bVal = b.games; }
            else if (sortKey === 'absChallenges') { aVal = a.absChallenges || 0; bVal = b.absChallenges || 0; }
            else if (sortKey === 'firstSeen') { aVal = toSortDate(a.firstSeen); bVal = toSortDate(b.firstSeen); }
            else if (sortKey === 'lastSeen') { aVal = toSortDate(a.lastSeen); bVal = toSortDate(b.lastSeen); }
            else if (['HP','1B','2B','3B','LF','RF'].includes(sortKey)) { aVal = (a.positions || {})[sortKey] || 0; bVal = (b.positions || {})[sortKey] || 0; }
            else { aVal = a[sortKey]; bVal = b[sortKey]; }
            let result = typeof aVal === 'number' ? aVal - bVal : String(aVal || '').localeCompare(String(bVal || ''));
            return sortDir === 'asc' ? result : -result;
        });
    }, [umpireLog, search, sortKey, sortDir]);

    const totalUmpires = umpireLog.length;
    const multipleGames = umpireLog.filter(u => u.games > 1).length;
    const totalChallenges = umpireLog.reduce((sum, u) => sum + (u.absChallenges || 0), 0);
    const totalOverturned = umpireLog.reduce((sum, u) => sum + (u.absOverturned || 0), 0);
    const SortHeader = ({ k, label, align }) => (
        <th className={`px-3 py-2 ${align || 'text-left'} cursor-pointer hover:bg-slate-100`} onClick={() => handleSort(k)}>
            {label} {sortKey === k && (sortDir === 'asc' ? '↑' : '↓')}
        </th>
    );

    return (
        <div className="space-y-4">
            {totalChallenges > 0 && (
                <div className="bg-white rounded-lg border border-slate-200 p-4" style={{ boxShadow: 'var(--shadow)' }}>
                    <h3 className="subsection-title font-semibold mb-3">ABS Challenge Summary</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-slate-800">{totalChallenges}</div>
                            <div className="small-text text-slate-500">Total Challenges</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green-600">{totalOverturned}</div>
                            <div className="small-text text-slate-500">Overturned</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-red-600">{totalChallenges - totalOverturned}</div>
                            <div className="small-text text-slate-500">Upheld</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">{totalChallenges > 0 ? Math.round(totalOverturned / totalChallenges * 100) : 0}%</div>
                            <div className="small-text text-slate-500">Overturn Rate</div>
                        </div>
                    </div>
                </div>
            )}
            <div className="bg-white rounded-lg border border-slate-200" style={{ boxShadow: 'var(--shadow)' }}>
                <div className="p-4 border-b border-slate-100">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                            <h2 className="section-title font-semibold text-slate-800">Umpire Tracker</h2>
                            <p className="small-text text-slate-500 mt-0.5">{totalUmpires} unique umpires, {multipleGames} seen multiple times</p>
                        </div>
                        <input type="text" placeholder="Search umpires..." value={search} onChange={(e) => setSearch(e.target.value)}
                            className="px-3 py-1.5 body-text border border-slate-200 rounded-lg focus:border-blue-500 focus:outline-none" />
                    </div>
                </div>
                <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                    <table className="w-full">
                        <thead className="bg-slate-50 sticky top-0">
                            <tr>
                                <SortHeader k="name" label="Umpire" />
                                <SortHeader k="games" label="Games" align="text-center" />
                                <SortHeader k="HP" label="HP" align="text-center" />
                                <SortHeader k="1B" label="1B" align="text-center" />
                                <SortHeader k="2B" label="2B" align="text-center" />
                                <SortHeader k="3B" label="3B" align="text-center" />
                                <SortHeader k="LF" label="LF" align="text-center" />
                                <SortHeader k="RF" label="RF" align="text-center" />
                                {totalChallenges > 0 && <SortHeader k="absChallenges" label="ABS Challenges" align="text-center" />}
                                <SortHeader k="firstSeen" label="First Seen" />
                                <SortHeader k="lastSeen" label="Last Seen" />
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {filtered.map((u, idx) => {
                                const isExpanded = expandedUmpire === u.name;
                                const posOrder = {'HP': 0, '1B': 1, '2B': 2, '3B': 3, 'LF': 4, 'RF': 5};
                                const umpGamesWithPos = (u.gameIds || []).map(entry => {
                                    const gid = typeof entry === 'string' ? entry : entry.gameId;
                                    const pos = typeof entry === 'string' ? '' : (entry.position || '');
                                    const game = gameMap[gid];
                                    return game ? { ...game, umpPosition: pos } : null;
                                }).filter(Boolean).sort((a, b) => (posOrder[a.umpPosition] ?? 9) - (posOrder[b.umpPosition] ?? 9));
                                return (
                                <React.Fragment key={u.name}>
                                <tr className={`hover:bg-blue-50/50 cursor-pointer ${idx % 2 === 1 ? 'bg-slate-50/50' : ''} ${isExpanded ? 'bg-blue-50' : ''}`}
                                    onClick={() => setExpandedUmpire(isExpanded ? null : u.name)}>
                                    <td className="px-3 py-2 body-text font-semibold text-slate-800">{u.name}</td>
                                    <td className="px-3 py-2 body-text font-bold text-blue-600 text-center">{u.games}</td>
                                    {['HP','1B','2B','3B','LF','RF'].map(pos => (
                                        <td key={pos} className="px-3 py-2 text-center body-text text-slate-600">{(u.positions || {})[pos] || '-'}</td>
                                    ))}
                                    {totalChallenges > 0 && (
                                        <td className="px-3 py-2 text-center">
                                            {u.absChallenges > 0 ? (
                                                <div className="flex items-center justify-center gap-2 text-xs">
                                                    <span className="text-green-600 font-medium" title="Overturned">{u.absOverturned} OVT</span>
                                                    <span className="text-red-600 font-medium" title="Upheld">{u.absUpheld} UPH</span>
                                                    <span className="text-slate-400">/ {u.absChallenges}</span>
                                                </div>
                                            ) : (
                                                <span className="text-slate-300">—</span>
                                            )}
                                        </td>
                                    )}
                                    <td className="px-3 py-2 body-text text-slate-500">{u.firstSeen}</td>
                                    <td className="px-3 py-2 body-text text-slate-500">{u.lastSeen}</td>
                                </tr>
                                {isExpanded && umpGamesWithPos.length > 0 && (
                                    <tr>
                                        <td colSpan={totalChallenges > 0 ? 10 : 9} className="px-3 py-2 bg-blue-50/50">
                                            <div className="flex flex-wrap gap-1">
                                                {umpGamesWithPos.map((g, gi) => {
                                                    const posColors = {'HP': 'bg-purple-50 border-purple-200 text-purple-700', '1B': 'bg-blue-50 border-blue-200 text-blue-700', '2B': 'bg-sky-50 border-sky-200 text-sky-700', '3B': 'bg-teal-50 border-teal-200 text-teal-700', 'LF': 'bg-green-50 border-green-200 text-green-700', 'RF': 'bg-emerald-50 border-emerald-200 text-emerald-700'};
                                                    const cls = posColors[g.umpPosition] || 'bg-white border-blue-200 text-blue-700';
                                                    return (
                                                        <button key={gi} onClick={(e) => { e.stopPropagation(); window._pendingGameId = g.gameId; if (window.__navigateTab) window.__navigateTab('gamelog'); }}
                                                            className={`text-[10px] px-2 py-0.5 rounded border hover:opacity-80 ${cls}`}>
                                                            {g.umpPosition ? <span className="font-bold mr-1">{g.umpPosition}</span> : ''}{g.date} {g.awayTeam}@{g.homeTeam}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                </React.Fragment>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const JerseyCollection = ({ jerseyLog }) => {
    const [selectedNumber, setSelectedNumber] = useState(null);
    const [includeSpring, setIncludeSpring] = useState(false);
    const [search, setSearch] = useState('');

    // Build grid of numbers 00-99, filtering spring training if needed
    const numbers = useMemo(() => {
        const grid = [];
        const filterFn = (players) => includeSpring ? players : players.filter(p => {
            // gameType is 'regular'/'postseason' for MLB games, 'spring'/'exhibition' otherwise
            return p.gameType !== 'spring' && p.gameType !== 'exhibition';
        });
        grid.push({ num: '00', players: filterFn(jerseyLog['00'] || []) });
        for (let i = 0; i <= 99; i++) {
            const key = String(i);
            grid.push({ num: key, players: filterFn(jerseyLog[key] || []) });
        }
        return grid;
    }, [jerseyLog, includeSpring]);

    const collected = numbers.filter(n => n.players.length > 0).length;
    const total = numbers.length;

    // Search: find jersey numbers that have a matching player
    const matchingNumbers = useMemo(() => {
        if (!search) return new Set();
        const q = search.toLowerCase();
        const matches = new Set();
        numbers.forEach(({ num, players }) => {
            if (players.some(p => (p.name || '').toLowerCase().includes(q) || (p.team || '').toLowerCase().includes(q)))
                matches.add(num);
        });
        return matches;
    }, [search, numbers]);

    return (
        <div className="space-y-4">
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <div className="mb-4">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h2 className="section-title font-bold">Jersey Number Collection</h2>
                            <p className="body-text text-slate-500 mt-1">
                                {collected} of {total} numbers collected ({Math.round(collected / total * 100)}%)
                            </p>
                        </div>
                        <div className="flex items-center gap-3">
                            <input type="text" placeholder="Search players..." value={search} onChange={(e) => setSearch(e.target.value)}
                                className="px-3 py-1.5 body-text border border-slate-200 rounded-lg focus:border-blue-500 focus:outline-none w-40" />
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" checked={includeSpring} onChange={(e) => setIncludeSpring(e.target.checked)} className="rounded" />
                                <span className="body-text text-slate-600">Include ST</span>
                            </label>
                        </div>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-3 mt-2">
                        <div className="bg-blue-600 h-3 rounded-full transition-all" style={{ width: `${(collected / total * 100)}%` }}></div>
                    </div>
                </div>

                <div className="grid gap-1.5" style={{ gridTemplateColumns: 'repeat(10, 1fr)' }}>
                    {numbers.map(({ num, players }) => {
                        const hasPlayers = players.length > 0;
                        const isSearchMatch = search && matchingNumbers.has(num);
                        return (
                            <button
                                key={num}
                                onClick={() => hasPlayers && setSelectedNumber(selectedNumber === num ? null : num)}
                                className={`aspect-square flex items-center justify-center rounded-lg text-sm font-bold transition-all ${
                                    isSearchMatch
                                        ? 'bg-amber-400 text-amber-900 ring-2 ring-amber-300 cursor-pointer'
                                        : hasPlayers
                                        ? selectedNumber === num
                                            ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                                            : 'bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer'
                                        : search ? 'bg-slate-50 text-slate-300' : 'bg-slate-100 text-slate-400'
                                }`}
                                title={hasPlayers ? `#${num}: ${players.length} player${players.length > 1 ? 's' : ''}` : `#${num}: not seen yet`}
                            >
                                {num}
                            </button>
                        );
                    })}
                </div>

                {selectedNumber && (() => {
                    const entry = numbers.find(n => n.num === selectedNumber);
                    const players = entry ? entry.players : [];
                    if (players.length === 0) return null;
                    // Sort by date (convert MM/DD/YYYY to sortable)
                    const sorted = [...players].sort((a, b) => {
                        const da = (a.date || '').split('/');
                        const db = (b.date || '').split('/');
                        const sa = da.length === 3 ? `${da[2]}${da[0].padStart(2,'0')}${da[1].padStart(2,'0')}` : '';
                        const sb = db.length === 3 ? `${db[2]}${db[0].padStart(2,'0')}${db[1].padStart(2,'0')}` : '';
                        return sa.localeCompare(sb);
                    });
                    return (
                    <div className="mt-4 bg-blue-50 rounded-lg p-4">
                        <h3 className="subsection-title font-bold mb-3">#{selectedNumber} — {sorted.length} player{sorted.length > 1 ? 's' : ''}</h3>
                        <div className="space-y-2">
                            {sorted.map((p, i) => (
                                <div key={`${p.playerId}-${i}`} className="flex items-center justify-between bg-white rounded p-2">
                                    <div className="flex items-center gap-2">
                                        <PlayerLink playerId={p.playerId} name={p.name} />
                                        <span className="text-xs text-slate-500">{p.team}</span>
                                    </div>
                                    <span className="text-xs text-slate-400">{p.date}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    );
                })()}
            </div>
        </div>
    );
};

// State abbreviation -> full name mapping for GeoJSON matching
const STATE_ABBR_TO_NAME = {
    'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CA':'California','CO':'Colorado',
    'CT':'Connecticut','DE':'Delaware','FL':'Florida','GA':'Georgia','HI':'Hawaii','ID':'Idaho',
    'IL':'Illinois','IN':'Indiana','IA':'Iowa','KS':'Kansas','KY':'Kentucky','LA':'Louisiana',
    'ME':'Maine','MD':'Maryland','MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi',
    'MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada','NH':'New Hampshire','NJ':'New Jersey',
    'NM':'New Mexico','NY':'New York','NC':'North Carolina','ND':'North Dakota','OH':'Ohio','OK':'Oklahoma',
    'OR':'Oregon','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota',
    'TN':'Tennessee','TX':'Texas','UT':'Utah','VT':'Vermont','VA':'Virginia','WA':'Washington',
    'WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming','DC':'District of Columbia'
};
const STATE_NAME_TO_ABBR = Object.fromEntries(Object.entries(STATE_ABBR_TO_NAME).map(([k,v]) => [v, k]));

// MLB API country name -> GeoJSON country name mapping
const COUNTRY_NAME_MAP = {
    'USA': 'United States of America', 'Dominican Republic': 'Dominican Republic',
    'Venezuela': 'Venezuela', 'Cuba': 'Cuba', 'Mexico': 'Mexico', 'Canada': 'Canada',
    'Japan': 'Japan', 'South Korea': 'South Korea', 'Republic of Korea': 'South Korea',
    'Colombia': 'Colombia', 'Panama': 'Panama', 'Nicaragua': 'Nicaragua',
    'Taiwan': 'Taiwan', 'Australia': 'Australia', 'Brazil': 'Brazil',
    'Germany': 'Germany', 'Honduras': 'Honduras', 'Netherlands': 'Netherlands',
    'Italy': 'Italy', 'Jamaica': 'Jamaica', 'Peru': 'Peru', 'Saudi Arabia': 'Saudi Arabia',
    'Puerto Rico': 'Puerto Rico', 'Curacao': 'Curacao', 'Aruba': 'Aruba',
    'Bahamas': 'The Bahamas', 'South Africa': 'South Africa',
    // Abbreviation fallbacks
    'VEN': 'Venezuela', 'DOM': 'Dominican Republic', 'CUB': 'Cuba',
    'MEX': 'Mexico', 'CAN': 'Canada', 'JPN': 'Japan', 'COL': 'Colombia',
    'PAN': 'Panama', 'NIC': 'Nicaragua', 'AUS': 'Australia', 'BRA': 'Brazil',
};

const GEOJSON_URLS = {
    states: 'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json',
    countries: 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'
};

const ChoroplethMap = ({ geoData, dataByPlace, nameMapper, center, zoom, onSelect, selectedPlace }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const layerRef = useRef(null);

    const getColor = (count) => {
        if (!count) return '#e5e7eb';
        if (count >= 100) return '#1e40af';
        if (count >= 50) return '#2563eb';
        if (count >= 20) return '#3b82f6';
        if (count >= 10) return '#60a5fa';
        if (count >= 5) return '#93c5fd';
        return '#bfdbfe';
    };

    useEffect(() => {
        if (!mapRef.current || !geoData || typeof L === 'undefined') return;

        if (!mapInstanceRef.current) {
            mapInstanceRef.current = L.map(mapRef.current, { scrollWheelZoom: true }).setView(center, zoom);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap'
            }).addTo(mapInstanceRef.current);
        }

        if (layerRef.current) {
            mapInstanceRef.current.removeLayer(layerRef.current);
        }

        layerRef.current = L.geoJSON(geoData, {
            style: (feature) => {
                const name = feature.properties.name;
                const key = nameMapper ? nameMapper(name) : name;
                const count = (dataByPlace[key] || []).length;
                const isSelected = key === selectedPlace || name === selectedPlace;
                return {
                    fillColor: getColor(count),
                    weight: isSelected ? 3 : 1,
                    opacity: 1,
                    color: isSelected ? '#1e3a8a' : '#6b7280',
                    fillOpacity: count > 0 ? 0.8 : 0.3
                };
            },
            onEachFeature: (feature, layer) => {
                const name = feature.properties.name;
                const key = nameMapper ? nameMapper(name) : name;
                const players = dataByPlace[key] || [];
                layer.bindTooltip(`<b>${key || name}</b>: ${players.length} player${players.length !== 1 ? 's' : ''}`, { sticky: true });
                layer.on('click', () => {
                    if (players.length > 0) onSelect(key || name);
                });
            }
        }).addTo(mapInstanceRef.current);

        // Auto-fit map to show regions with data
        try {
            const bounds = layerRef.current.getBounds();
            if (bounds.isValid()) mapInstanceRef.current.fitBounds(bounds, { padding: [20, 20], maxZoom: 5 });
        } catch(e) {}
    }, [geoData, dataByPlace, selectedPlace]);

    useEffect(() => {
        if (mapInstanceRef.current) {
            setTimeout(() => mapInstanceRef.current.invalidateSize(), 100);
        }
    });

    return <div ref={mapRef} style={{ height: '500px', borderRadius: '8px' }} className="border"></div>;
};

const OriginsMap = ({ countriesGeo, statesGeo, countryData, stateData, selectedPlace, onSelect }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const countryLayerRef = useRef(null);
    const stateLayerRef = useRef(null);

    const getColor = (count) => {
        if (!count) return '#e5e7eb';
        if (count >= 100) return '#1e40af';
        if (count >= 50) return '#2563eb';
        if (count >= 20) return '#3b82f6';
        if (count >= 10) return '#60a5fa';
        if (count >= 5) return '#93c5fd';
        return '#bfdbfe';
    };

    useEffect(() => {
        if (!mapRef.current || typeof L === 'undefined') return;

        if (!mapInstanceRef.current) {
            mapInstanceRef.current = L.map(mapRef.current, { scrollWheelZoom: true, worldCopyJump: true }).setView([25, -40], 3);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap'
            }).addTo(mapInstanceRef.current);
        }

        const map = mapInstanceRef.current;

        // Remove old layers
        if (countryLayerRef.current) map.removeLayer(countryLayerRef.current);
        if (stateLayerRef.current) map.removeLayer(stateLayerRef.current);

        // Add countries layer (bottom)
        if (countriesGeo) {
            countryLayerRef.current = L.geoJSON(countriesGeo, {
                filter: (feature) => feature.properties.name !== 'United States of America',
                style: (feature) => {
                    const name = feature.properties.name;
                    const count = (countryData[name] || []).length;
                    const isSelected = name === selectedPlace;
                    return { fillColor: getColor(count), weight: isSelected ? 3 : 1, opacity: 1,
                        color: isSelected ? '#1e3a8a' : '#9ca3af', fillOpacity: count > 0 ? 0.8 : 0.2 };
                },
                onEachFeature: (feature, layer) => {
                    const name = feature.properties.name;
                    const players = countryData[name] || [];
                    layer.bindTooltip(`<b>${name}</b>: ${players.length} player${players.length !== 1 ? 's' : ''}`, { sticky: true });
                    layer.on('click', () => { if (players.length > 0) onSelect(name, false); });
                }
            }).addTo(map);
        }

        // Add US states layer (top, over USA country shape)
        // Exclude territories that are tracked as countries in our data
        const STATE_EXCLUSIONS = new Set(['Puerto Rico', 'Guam', 'American Samoa', 'U.S. Virgin Islands', 'Northern Mariana Islands']);
        if (statesGeo) {
            stateLayerRef.current = L.geoJSON(statesGeo, {
                filter: (feature) => !STATE_EXCLUSIONS.has(feature.properties.name),
                style: (feature) => {
                    const name = feature.properties.name;
                    const count = (stateData[name] || []).length;
                    const isSelected = name === selectedPlace;
                    return { fillColor: getColor(count), weight: isSelected ? 3 : 1, opacity: 1,
                        color: isSelected ? '#1e3a8a' : '#6b7280', fillOpacity: count > 0 ? 0.8 : 0.3 };
                },
                onEachFeature: (feature, layer) => {
                    const name = feature.properties.name;
                    const players = stateData[name] || [];
                    layer.bindTooltip(`<b>${name}</b>: ${players.length} player${players.length !== 1 ? 's' : ''}`, { sticky: true });
                    layer.on('click', () => { if (players.length > 0) onSelect(name, true); });
                }
            }).addTo(map);
        }
    }, [countriesGeo, statesGeo, countryData, stateData, selectedPlace]);

    useEffect(() => {
        if (mapInstanceRef.current) setTimeout(() => mapInstanceRef.current.invalidateSize(), 100);
    });

    return <div ref={mapRef} style={{ height: '500px', borderRadius: '8px' }} className="border"></div>;
};

const PlayerOrigins = ({ playerBios, allPlayers }) => {
    const [viewMode, setViewMode] = useState('maps');
    const [selectedPlace, setSelectedPlace] = useState(null);
    const [statesGeo, setStatesGeo] = useState(null);
    const [countriesGeo, setCountriesGeo] = useState(null);
    const [search, setSearch] = useState('');

    // Fetch GeoJSON
    useEffect(() => {
        fetch(GEOJSON_URLS.states).then(r => r.json()).then(setStatesGeo).catch(() => {});
        fetch(GEOJSON_URLS.countries).then(r => r.json()).then(setCountriesGeo).catch(() => {});
    }, []);

    const data = useMemo(() => {
        const playerList = allPlayers.map(p => {
            const bio = playerBios[p.playerId] || {};
            return { ...p, ...bio };
        }).filter(p => p.birthCountry);

        const byCountry = {};
        playerList.forEach(p => {
            const c = p.birthCountry || 'Unknown';
            if (!byCountry[c]) byCountry[c] = [];
            byCountry[c].push(p);
        });

        const byState = {};
        playerList.filter(p => p.birthCountry === 'USA' && p.birthState).forEach(p => {
            const s = p.birthState;
            if (!byState[s]) byState[s] = [];
            byState[s].push(p);
        });

        // Also key by full state name for GeoJSON matching
        const byStateName = {};
        Object.entries(byState).forEach(([abbr, players]) => {
            const fullName = STATE_ABBR_TO_NAME[abbr];
            if (fullName) byStateName[fullName] = players;
            byStateName[abbr] = players;
        });

        return { byCountry, byState, byStateName, total: playerList.length };
    }, [playerBios, allPlayers]);

    // Map name from GeoJSON country -> MLB API country
    const countryGeoToMlb = (geoName) => {
        // Reverse lookup
        for (const [mlb, geo] of Object.entries(COUNTRY_NAME_MAP)) {
            if (geo === geoName) return mlb;
        }
        return geoName;
    };

    const selectedPlayers = useMemo(() => {
        if (!selectedPlace) return [];
        // Try direct match in byCountry, byState, byStateName
        return data.byCountry[selectedPlace] || data.byState[selectedPlace] || data.byStateName[selectedPlace] || [];
    }, [selectedPlace, data]);

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <div>
                    <h2 className="section-title font-bold">Player Origins</h2>
                    <p className="body-text text-slate-500 mt-1">{data.total} players from {Object.keys(data.byCountry).length} countries, {Object.keys(data.byState).length} US states</p>
                </div>
                <div className="flex items-center gap-3">
                    <input type="text" placeholder="Search players..." value={search} onChange={(e) => setSearch(e.target.value)}
                        className="px-3 py-1.5 body-text border border-slate-200 rounded-lg focus:border-blue-500 focus:outline-none w-40" />
                    <div className="flex rounded-lg overflow-hidden border">
                        <button onClick={() => { setViewMode('maps'); setSelectedPlace(null); }} className={`px-4 py-2 text-sm font-medium ${viewMode === 'maps' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-100'}`}>Maps</button>
                        <button onClick={() => { setViewMode('list'); setSelectedPlace(null); }} className={`px-4 py-2 text-sm font-medium ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-100'}`}>List</button>
                    </div>
                </div>
            </div>

            {search && (() => {
                const q = search.toLowerCase();
                const matches = allPlayers.map(p => ({ ...p, ...(playerBios[p.playerId] || {}) }))
                    .filter(p => (p.name || '').toLowerCase().includes(q) || (p.birthCity || '').toLowerCase().includes(q))
                    .slice(0, 20);
                return matches.length > 0 ? (
                    <div className="bg-blue-50 rounded-lg p-3 mb-4">
                        <div className="flex flex-wrap gap-2">
                            {matches.map(p => {
                                const place = p.birthCountry === 'USA' && p.birthState
                                    ? p.birthState : p.birthCountry;
                                return (
                                <button key={p.playerId} className="px-2 py-1 bg-white rounded text-sm hover:bg-blue-100 text-left"
                                    onClick={() => place && setSelectedPlace(place)}>
                                    <PlayerLink playerId={p.playerId} name={p.name} />
                                    <span className="text-slate-400 text-xs ml-1">
                                        {[p.birthCity, p.birthState, p.birthCountry].filter(Boolean).join(', ')}
                                    </span>
                                </button>
                                );
                            })}
                        </div>
                    </div>
                ) : null;
            })()}

            {viewMode === 'maps' && (() => {
                // Merge country data (excluding USA which is shown by state) with state data
                const countryData = Object.fromEntries(
                    Object.entries(data.byCountry)
                        .filter(([k]) => k !== 'USA')
                        .map(([mlb, players]) => [COUNTRY_NAME_MAP[mlb] || mlb, players])
                );
                const stateData = data.byStateName;
                // Combined handler: states use abbreviation lookup, countries use reverse name mapping
                const handleSelect = (name, isState) => {
                    if (isState) {
                        setSelectedPlace(STATE_NAME_TO_ABBR[name] || name);
                    } else {
                        const mlb = countryGeoToMlb(name);
                        setSelectedPlace(prev => prev === mlb ? null : mlb);
                    }
                };
                const resolvedSelected = selectedPlace
                    ? (STATE_ABBR_TO_NAME[selectedPlace] || COUNTRY_NAME_MAP[selectedPlace] || selectedPlace)
                    : null;

                return (
                    <OriginsMap
                        countriesGeo={countriesGeo}
                        statesGeo={statesGeo}
                        countryData={countryData}
                        stateData={stateData}
                        selectedPlace={resolvedSelected}
                        onSelect={handleSelect}
                    />
                );
            })()}

            {selectedPlace && selectedPlayers.length > 0 && viewMode !== 'list' && (
                <div className="mt-4 bg-blue-50 rounded-lg p-4">
                    <h3 className="subsection-title font-bold mb-2">{selectedPlace} — {selectedPlayers.length} players</h3>
                    <div className="flex flex-wrap gap-2">
                        {selectedPlayers.sort((a, b) => (a.name || '').localeCompare(b.name || '')).map(p => (
                            <span key={p.playerId} className="px-2 py-1 bg-white rounded text-sm">
                                <PlayerLink playerId={p.playerId} name={p.name} />
                                {p.birthCity && <span className="text-slate-400 text-xs ml-1">({p.birthCity})</span>}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {viewMode === 'list' && (
                <div className="space-y-2">
                    {Object.entries(data.byCountry).sort((a, b) => b[1].length - a[1].length).map(([place, players]) => {
                        const isUSA = place === 'USA';
                        // Group USA players by state
                        const byState = isUSA ? {} : null;
                        if (isUSA) {
                            players.forEach(p => {
                                const st = p.birthState || 'Unknown';
                                if (!byState[st]) byState[st] = [];
                                byState[st].push(p);
                            });
                        }
                        return (
                        <details key={place} className="bg-slate-50 rounded-lg">
                            <summary className="px-4 py-3 cursor-pointer hover:bg-slate-100 flex items-center justify-between">
                                <span className="font-semibold body-text">{place}</span>
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-bold">{players.length}</span>
                            </summary>
                            {isUSA && byState ? (
                                <div className="px-4 pb-3 space-y-1">
                                    {Object.entries(byState).sort((a, b) => b[1].length - a[1].length).map(([state, stPlayers]) => (
                                        <details key={state} className="bg-white rounded-lg">
                                            <summary className="px-3 py-2 cursor-pointer hover:bg-slate-50 flex items-center justify-between text-sm">
                                                <span className="font-medium">{state}</span>
                                                <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-bold">{stPlayers.length}</span>
                                            </summary>
                                            <div className="px-3 pb-2 flex flex-wrap gap-2">
                                                {stPlayers.sort((a, b) => (a.name || '').localeCompare(b.name || '')).map(p => (
                                                    <span key={p.playerId} className="px-2 py-1 bg-slate-50 rounded text-sm">
                                                        <PlayerLink playerId={p.playerId} name={p.name} />
                                                        {p.birthCity && <span className="text-slate-400 text-xs ml-1">({p.birthCity})</span>}
                                                    </span>
                                                ))}
                                            </div>
                                        </details>
                                    ))}
                                </div>
                            ) : (
                                <div className="px-4 pb-3 flex flex-wrap gap-2">
                                    {players.sort((a, b) => (a.name || '').localeCompare(b.name || '')).map(p => (
                                        <span key={p.playerId} className="px-2 py-1 bg-white rounded text-sm">
                                            <PlayerLink playerId={p.playerId} name={p.name} />
                                            {p.birthCity && <span className="text-slate-400 text-xs ml-1">({p.birthCity})</span>}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </details>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

const PlayerBirthdays = ({ playerBios, allPlayers }) => {
    const [selectedDay, setSelectedDay] = useState(null);
    const [search, setSearch] = useState('');
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    const daysInMonth = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

    const data = useMemo(() => {
        const byDay = {};  // "MM-DD" -> [players]
        const today = new Date();
        const todayKey = String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');

        allPlayers.forEach(p => {
            const bio = playerBios[p.playerId] || {};
            if (!bio.birthDate) return;
            const parts = bio.birthDate.split('-');
            if (parts.length < 3) return;
            const key = parts[1] + '-' + parts[2];
            if (!byDay[key]) byDay[key] = [];
            byDay[key].push({ ...p, birthDate: bio.birthDate });
        });

        const totalDays = 366;
        const collected = Object.keys(byDay).length;
        return { byDay, todayKey, collected, totalDays };
    }, [playerBios, allPlayers]);

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="mb-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <h2 className="section-title font-bold">Birthday Calendar</h2>
                        <p className="body-text text-slate-500 mt-1">
                            {data.collected} of {data.totalDays} days collected ({Math.round(data.collected / data.totalDays * 100)}%)
                        </p>
                    </div>
                    <input type="text" placeholder="Search players..." value={search} onChange={(e) => setSearch(e.target.value)}
                        className="px-3 py-1.5 body-text border border-slate-200 rounded-lg focus:border-blue-500 focus:outline-none w-40" />
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3 mt-2">
                    <div className="bg-purple-600 h-3 rounded-full transition-all" style={{ width: `${(data.collected / data.totalDays * 100)}%` }}></div>
                </div>
            </div>

            {(() => {
                const q = search ? search.toLowerCase() : '';
                const matches = q ? allPlayers.map(p => ({ ...p, ...(playerBios[p.playerId] || {}) }))
                    .filter(p => (p.name || '').toLowerCase().includes(q) && p.birthDate).slice(0, 20) : [];
                // Build set of highlighted day keys from search matches
                const highlightDays = new Set();
                matches.forEach(p => {
                    if (p.birthDate) {
                        const d = new Date(p.birthDate + 'T00:00:00');
                        const key = String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
                        highlightDays.add(key);
                    }
                });
                return <>
                {matches.length > 0 && (
                    <div className="bg-purple-50 rounded-lg p-3 mb-4">
                        <div className="flex flex-wrap gap-2">
                            {matches.map(p => (
                                <span key={p.playerId} className="px-2 py-1 bg-white rounded text-sm">
                                    <PlayerLink playerId={p.playerId} name={p.name} />
                                    <span className="text-slate-400 text-xs ml-1">
                                        {p.birthDate ? new Date(p.birthDate + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''}
                                    </span>
                                </span>
                            ))}
                        </div>
                    </div>
                )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {monthNames.map((month, mi) => {
                    const monthNum = String(mi + 1).padStart(2, '0');
                    const days = daysInMonth[mi];
                    const firstDow = new Date(2024, mi, 1).getDay();
                    const collected = Array.from({ length: days }, (_, di) => {
                        const key = `${monthNum}-${String(di + 1).padStart(2, '0')}`;
                        return (data.byDay[key] || []).length > 0 ? 1 : 0;
                    }).reduce((a, b) => a + b, 0);

                    return (
                        <div key={month} className="bg-slate-50 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-1">
                                <div className="text-sm font-bold text-slate-700">{month}</div>
                                <div className="text-xs text-slate-500">{collected}/{days}</div>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-1.5 mb-2">
                                <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: `${(collected / days * 100)}%` }}></div>
                            </div>
                            <div className="grid grid-cols-7 gap-0.5 text-center">
                                {['S','M','T','W','T','F','S'].map((d, i) => (
                                    <div key={`hdr-${i}`} className="text-[10px] font-medium text-slate-400 py-0.5">{d}</div>
                                ))}
                                {Array.from({ length: firstDow }, (_, i) => (
                                    <div key={`pad-${i}`}></div>
                                ))}
                                {Array.from({ length: days }, (_, di) => {
                                    const dayNum = String(di + 1).padStart(2, '0');
                                    const key = `${monthNum}-${dayNum}`;
                                    const players = data.byDay[key] || [];
                                    const isToday = key === data.todayKey;
                                    const isSelected = selectedDay === key;
                                    const isHighlighted = highlightDays.has(key);
                                    const hasPlayers = players.length > 0;
                                    const count = players.length;
                                    return (
                                        <button
                                            key={key}
                                            onClick={() => hasPlayers && setSelectedDay(isSelected ? null : key)}
                                            className={`aspect-square flex items-center justify-center rounded text-xs font-medium transition-all ${
                                                isToday ? 'ring-2 ring-yellow-400 ' : ''
                                            }${
                                                isHighlighted ? 'bg-amber-400 text-amber-900 ring-2 ring-amber-300 cursor-pointer' :
                                                isSelected ? 'bg-purple-600 text-white' :
                                                count >= 10 ? 'bg-purple-500 text-white cursor-pointer' :
                                                count >= 5 ? 'bg-purple-300 text-purple-900 cursor-pointer' :
                                                hasPlayers ? 'bg-purple-100 text-purple-800 hover:bg-purple-200 cursor-pointer' :
                                                'text-slate-400'
                                            }`}
                                            title={hasPlayers ? `${month} ${di+1}: ${count} player${count > 1 ? 's' : ''}` : `${month} ${di+1}`}
                                        >
                                            {di + 1}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>

            {selectedDay && data.byDay[selectedDay] && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedDay(null)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-md w-full max-h-[70vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b bg-purple-600 text-white rounded-t-lg flex items-center justify-between">
                            <h3 className="font-bold">
                                {monthNames[parseInt(selectedDay.split('-')[0]) - 1]} {parseInt(selectedDay.split('-')[1])} — {data.byDay[selectedDay].length} player{data.byDay[selectedDay].length > 1 ? 's' : ''}
                            </h3>
                            <button onClick={() => setSelectedDay(null)} className="text-white hover:text-slate-200 text-xl leading-none">&times;</button>
                        </div>
                        <div className="p-4 space-y-2">
                            {data.byDay[selectedDay]
                                .filter((p, i, arr) => arr.findIndex(x => x.playerId === p.playerId) === i)
                                .sort((a, b) => (a.birthDate || '').localeCompare(b.birthDate || ''))
                                .map((p, i) => (
                                <div key={`${p.playerId}-${i}`} className="flex items-center justify-between bg-slate-50 rounded p-2">
                                    <PlayerLink playerId={p.playerId} name={p.name} />
                                    <span className="text-xs text-slate-400">{p.birthDate}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
            </>;
            })()}
        </div>
    );
};

const DebutPerformance = ({ r }) => {
    if (r.ip && r.ip !== '' && r.ip !== '0.0') return <span className="font-mono small-text">{r.ip} IP, {r.h_p} H, {r.er} ER, {r.bb_p} BB, {r.so_p} SO{r.decision ? ` (${r.decision})` : ''}</span>;
    if (r.ab > 0) {
        const parts = r.h > 0 ? [`${r.h}-${r.ab}`] : [`0-${r.ab}`];
        if (r.hr > 0) parts.push(`${r.hr} HR`);
        if (r.rbi > 0) parts.push(`${r.rbi} RBI`);
        if (r.r > 0) parts.push(`${r.r} R`);
        if (r.bb > 0) parts.push(`${r.bb} BB`);
        if (r.so > 0) parts.push(`${r.so} SO`);
        return <span className="font-mono small-text">{parts.join(', ')}</span>;
    }
    return <span className="text-slate-500 italic small-text">Defensive replacement</span>;
};

const PersonalRecords = ({ data }) => {
    const [expandedRecord, setExpandedRecord] = useState(null);
    const [indivTab, setIndivTab] = useState('hitting');

    const gameMap = useMemo(() => {
        const map = {};
        (data.games || []).forEach(game => { if (game.gameId) map[game.gameId] = game; });
        return map;
    }, [data.games]);

    const HIDDEN_RECORDS = new Set(['Hits Leaders', 'Runs Leaders', 'Home Run Leaders', 'RBI Leaders',
        'Doubles Leaders', 'Triples Leaders', 'Stolen Base Leaders', 'Walks Leaders (Hitting)',
        'Batting Average Leaders (min. 10 AB)', 'On-Base Percentage Leaders (min. 10 AB)',
        'OPS Leaders (min. 10 AB)', 'Wins Leaders', 'Strikeout Leaders (Pitching)',
        'Save Leaders', 'Innings Pitched Leaders', 'ERA Leaders (min. 10 IP)',
        'Career WPA Leaders (Top 3)', 'Day Games vs Night Games', 'Weekend vs Weekday Games',
        'Percent of Possible Matchups Seen']);

    // Section classification
    const SECTION_MAP = {
        'Total Hits Across All Games': 'cumulative',
        'Total Home Runs Across All Games': 'cumulative',
        'Total Runs Across All Games': 'cumulative',
        'Total Strikeouts Across All Games': 'cumulative',
        'Total Stolen Bases Across All Games': 'cumulative',
        'Back-to-Back HR Events': 'rare',
        'Back-to-Back-to-Back HR Events': 'rare',
        'Back-to-Back-to-Back-to-Back HR Events': 'rare',
        'Inside-the-Park Home Runs': 'rare',
        'Cycles': 'rare',
        'No-Hitters': 'rare',
        'Biggest Victory': 'extremes',
        'Biggest Comeback': 'extremes',
        'Most Combined Runs': 'extremes',
        'Most Runs by One Team': 'extremes',
        'Most Runs in a Single Inning': 'extremes',
        'Longest Game by Innings': 'environment',
        'Longest Game by Time': 'environment',
        'Shortest Game by Time': 'environment',
        'Most Combined HRs': 'extremes',
        'Most HRs by One Team': 'extremes',
        'Both Teams 10+ Runs': 'extremes',
        'Coldest Game': 'environment',
        'Hottest Game': 'environment',
        'Average Temperature': 'environment',
        'Highest Attendance': 'environment',
        'Lowest Attendance': 'environment',
        'Average Attendance': 'environment',
        'Earliest Start Time': 'environment',
        'Latest Start Time': 'environment',
        'Highest Wind Speed': 'environment',
        'Average Wind Speed': 'environment',
        'Games with Precipitation': 'environment',
        'Most Hits by One Team': 'individual-hitting',
        'Most Combined Hits': 'individual-hitting',
        'Fewest Hits by One Team': 'individual-hitting',
        'Fewest Combined Hits': 'individual-hitting',
        'Most RBIs in a Game': 'individual-hitting',
        'Most SBs by One Player': 'individual-hitting',
        'Most SBs by One Team': 'individual-hitting',
        'Most Combined SBs in a Game': 'individual-hitting',
        'Most Walks by One Team': 'individual-hitting',
        'Most Combined Walks': 'individual-hitting',
        'Fewest Combined Walks': 'individual-hitting',
        '20+ Hit Games by One Team': 'individual-hitting',
        '4+ Hit Games': 'hidden',
        '5+ RBI Games': 'hidden',
        'Multi-HR Games': 'hidden',
        'Most Clutch Single Game (WPA)': 'individual-hitting',
        'Most Pitching Strikeouts by One Team': 'individual-pitching',
        'Most Combined Pitching Strikeouts': 'individual-pitching',
        'Fewest Combined Strikeouts': 'individual-pitching',
        'Most Pitches by One Pitcher': 'individual-pitching',
        'Most Pitchers Used': 'individual-pitching',
        'Fewest Pitchers Used': 'individual-pitching',
        '10+ K Games': 'hidden',
        'Complete Games': 'hidden',
        'Shutouts': 'hidden',
        'Quality Starts': 'hidden',
        '1-Run Games': 'frequency',
        '1-0 Games': 'frequency',
        'Extra Inning Games': 'frequency',
        '10+ Run Innings': 'frequency',
        'Unique Players with a Hit': 'frequency',
        'Unique Players with a Home Run': 'frequency',
        'Unique Pitchers with a Win': 'frequency',
        'Unique Pitchers with a Loss': 'frequency',
        'Unique Pitchers with a Save': 'frequency',
        'Most Teams Seen for a Player': 'frequency',
        'Players with RISP Opportunities': 'hidden',
        'Players with Bases Loaded Opportunities': 'hidden',
    };

    const sections = useMemo(() => {
        const result = { cumulative: [], rare: [], extremes: [], environment: [],
            'individual-hitting': [], 'individual-pitching': [], frequency: [] };
        (data.summary || []).forEach(row => {
            if (HIDDEN_RECORDS.has(row.record)) return;
            const section = SECTION_MAP[row.record];
            if (section && result[section]) result[section].push(row);
            else if (!HIDDEN_RECORDS.has(row.record)) result.frequency.push(row);
        });
        return result;
    }, [data.summary]);

    // ABS challenge records
    const absRecords = useMemo(() => {
        const countAbs = (abs) => {
            // Savant-sourced reviews are authoritative when available
            const reviews = abs.reviews || [];
            if (reviews.length > 0) return { total: reviews.length, overturned: reviews.filter(r => r.overturned).length };
            // Fallback for old cached data: summary totals
            const total = ['away','home'].reduce((s, side) => s + (abs[side]?.usedSuccessful || 0) + (abs[side]?.usedFailed || 0), 0);
            const overturned = ['away','home'].reduce((s, side) => s + (abs[side]?.usedSuccessful || 0), 0);
            return { total, overturned };
        };
        const gamesWithAbs = (data.games || []).filter(g => {
            const abs = g.absChallenges;
            if (!abs) return false;
            return countAbs(abs).total > 0;
        }).map(g => {
            const { total, overturned } = countAbs(g.absChallenges);
            return { ...g, absTotal: total, absOverturned: overturned };
        }).sort((a, b) => b.absTotal - a.absTotal);

        const umpires = (data.umpireLog || []).filter(u => (u.absChallenges || 0) > 0);
        const umpsWithRate = umpires.map(u => ({
            ...u, overturnRate: Math.round((u.absOverturned || 0) / u.absChallenges * 100)
        }));
        const highestRate = [...umpsWithRate].sort((a, b) => b.overturnRate - a.overturnRate);
        const lowestRate = [...umpsWithRate].sort((a, b) => a.overturnRate - b.overturnRate);

        return {
            totalGames: gamesWithAbs.length,
            totalChallenges: gamesWithAbs.reduce((s, g) => s + g.absTotal, 0),
            topByTotal: gamesWithAbs.slice(0, 5),
            topByOverturned: [...gamesWithAbs].sort((a, b) => b.absOverturned - a.absOverturned).slice(0, 5),
            highestRate: highestRate.slice(0, 5),
            lowestRate: lowestRate.slice(0, 5),
            umpiresByTotal: [...umpires].sort((a, b) => (b.absChallenges || 0) - (a.absChallenges || 0)).slice(0, 5),
        };
    }, [data.games, data.umpireLog]);

    // Helper: navigate to game
    const goToGame = (gameId) => {
        window._pendingGameId = gameId;
        if (window.__navigateTab) window.__navigateTab('gamelog');
    };

    // Helper: parse detail/score/gameIds from a record
    const parseRecord = (record) => {
        const gameIds = (record.gameIds || '').split(',').map(id => id.trim()).filter(Boolean);
        const games = gameIds.map(id => gameMap[id]).filter(Boolean);
        const detailParts = (record.detail || '').split(';').map(d => d.trim()).filter(Boolean);
        const scoreParts = (record.score || '').split(';').map(s => s.trim()).filter(Boolean);
        return { gameIds, games, detailParts, scoreParts };
    };

    // Helper: render game buttons
    const GameButtons = ({ games, max = 8 }) => games.length > 0 ? (
        <div className="flex flex-wrap gap-1 mt-1.5">
            {games.slice(0, max).map((g, gi) => (
                <button key={gi} onClick={(e) => { e.stopPropagation(); goToGame(g.gameId); }}
                    className="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
                    {g.date} {g.awayTeam}@{g.homeTeam}
                </button>
            ))}
            {games.length > max && <span className="text-[10px] text-slate-400 self-center">+{games.length - max} more</span>}
        </div>
    ) : null;

    // Helper: expandable record card (used in extremes and individual sections)
    const RecordCard = ({ record, compact }) => {
        const key = record.record;
        const isExpanded = expandedRecord === key;
        const { games, detailParts, scoreParts } = parseRecord(record);
        const hasDetail = detailParts.length > 0 || games.length > 0;
        // For single-game records, show full detail (both teams); for multi-game, show first entry
        const previewText = detailParts.length > 0
            ? (scoreParts.length <= 1 ? detailParts.join(' / ') : detailParts[0])
            : games.length > 0 && games.length <= 3 ? games.map(g => `${g.awayTeam}@${g.homeTeam} ${g.date}`).join(', ')
            : games.length > 3 ? `${games.length} games` : '';

        return (
            <div className={`bg-white rounded-lg border hover:shadow-sm transition-all ${isExpanded ? 'border-blue-300 shadow-sm' : 'border-slate-200'}`}>
                <div className={`${compact ? 'p-2.5' : 'p-3'} ${hasDetail ? 'cursor-pointer' : ''}`}
                    onClick={() => hasDetail && setExpandedRecord(isExpanded ? null : key)}>
                    <div className="flex items-center justify-between gap-3">
                        <div className="flex-1 min-w-0">
                            <div className={`${compact ? 'text-xs' : 'text-sm'} font-semibold text-slate-900`}>{record.record}</div>
                            {!isExpanded && previewText && (
                                <div className="text-[11px] text-slate-500 mt-0.5 truncate">{previewText}</div>
                            )}
                        </div>
                        <div className="text-lg font-bold text-blue-600 flex-shrink-0">{record.value}</div>
                    </div>
                </div>
                {isExpanded && hasDetail && (
                    <div className="px-3 pb-3 space-y-1.5 border-t pt-2">
                        {(() => {
                            // Group details + scores into per-game blocks
                            const grouped = [];
                            detailParts.forEach((detail, di) => {
                                const score = scoreParts[di] || '';
                                const game = games[di] || null;
                                const gameId = game?.gameId || score || di;
                                const last = grouped[grouped.length - 1];
                                if (last && last.gameId === gameId) last.details.push(detail);
                                else grouped.push({ details: [detail], score, game, gameId });
                            });
                            return grouped.map((group, gi) => (
                                <div key={gi} className="bg-slate-50 rounded p-2 text-xs">
                                    {(group.score || group.game) && (
                                        <div className="flex items-center justify-between mb-1">
                                            {group.game && (
                                                <button onClick={() => goToGame(group.game.gameId)}
                                                    className="font-semibold text-blue-600 hover:underline">
                                                    {group.game.awayTeam} @ {group.game.homeTeam} — {group.game.date}
                                                </button>
                                            )}
                                            {group.score && <span className="text-slate-400 whitespace-nowrap">{group.score}</span>}
                                        </div>
                                    )}
                                    <div className="space-y-0.5">
                                        {group.details.map((d, di) => (
                                            <div key={di} className="text-slate-700">{d}</div>
                                        ))}
                                    </div>
                                </div>
                            ));
                        })()}
                        {games.length > 0 && detailParts.length === 0 && <GameButtons games={games} />}
                    </div>
                )}
            </div>
        );
    };

    // Cumulative short labels
    const cumulativeLabels = {
        'Total Hits Across All Games': { label: 'Hits', icon: 'H' },
        'Total Home Runs Across All Games': { label: 'Home Runs', icon: 'HR' },
        'Total Runs Across All Games': { label: 'Runs', icon: 'R' },
        'Total Strikeouts Across All Games': { label: 'Strikeouts', icon: 'K' },
        'Total Stolen Bases Across All Games': { label: 'Stolen Bases', icon: 'SB' },
    };

    // Environment record lookup
    const envLookup = useMemo(() => {
        const map = {};
        sections.environment.forEach(r => { map[r.record] = r; });
        return map;
    }, [sections.environment]);

    const envVal = (name) => {
        const r = envLookup[name];
        return r ? r.value : '--';
    };
    const envGame = (name) => {
        const r = envLookup[name];
        if (!r) return null;
        const { games } = parseRecord(r);
        return games[0] || null;
    };

    return (
        <div className="space-y-5">
            {/* Section 1: Cumulative Totals */}
            {sections.cumulative.length > 0 && (
                <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-xl p-4 shadow-md">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Across All Games</div>
                    <div className="grid grid-cols-5 gap-3">
                        {sections.cumulative.map(r => {
                            const info = cumulativeLabels[r.record] || { label: r.record, icon: '?' };
                            return (
                                <div key={r.record} className="text-center">
                                    <div className="text-2xl font-bold text-white">{parseInt(r.value).toLocaleString()}</div>
                                    <div className="text-[11px] text-slate-400 mt-0.5">{info.label}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Section 2: Rare Moments */}
            {sections.rare.filter(r => parseInt(r.value) > 0).length > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="text-sm font-semibold text-slate-900">Rare Moments</div>
                        <div className="flex-1 h-px bg-slate-200"></div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {sections.rare.filter(r => parseInt(r.value) > 0).map(record => {
                            const { games, detailParts, scoreParts } = parseRecord(record);
                            const isExpanded = expandedRecord === record.record;
                            return (
                                <div key={record.record}
                                    className={`bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl overflow-hidden transition-all ${isExpanded ? 'md:col-span-2 lg:col-span-3' : ''}`}>
                                    <div className="p-4 cursor-pointer" onClick={() => setExpandedRecord(isExpanded ? null : record.record)}>
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <div className="text-sm font-bold text-amber-900">{record.record}</div>
                                                {!isExpanded && detailParts.length > 0 && (
                                                    <div className="text-xs text-amber-700 mt-1 truncate max-w-[300px]">{detailParts[0]}</div>
                                                )}
                                            </div>
                                            <div className="text-3xl font-black text-amber-600">{record.value}</div>
                                        </div>
                                    </div>
                                    {isExpanded && (detailParts.length > 0 || games.length > 0) && (
                                        <div className="px-4 pb-4 space-y-2 border-t border-amber-200 pt-3">
                                            {detailParts.map((d, di) => (
                                                <div key={di} className="flex items-start justify-between gap-2 bg-white bg-opacity-60 rounded-lg p-2.5 text-xs">
                                                    <span className="text-amber-900">{d}</span>
                                                    {scoreParts[di] && <span className="text-amber-600 whitespace-nowrap font-medium">{scoreParts[di]}</span>}
                                                </div>
                                            ))}
                                            <GameButtons games={games} />
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Section 3: Game Extremes */}
            {sections.extremes.length > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="text-sm font-semibold text-slate-900">Game Extremes</div>
                        <div className="flex-1 h-px bg-slate-200"></div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {sections.extremes.map(record => <RecordCard key={record.record} record={record} />)}
                    </div>
                </div>
            )}

            {/* Section 4: Environment Dashboard */}
            {sections.environment.length > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="text-sm font-semibold text-slate-900">Game Environment</div>
                        <div className="flex-1 h-px bg-slate-200"></div>
                    </div>
                    <div className="bg-white rounded-xl border border-slate-200 p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            {/* Temperature */}
                            <div>
                                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Temperature</div>
                                <div className="flex items-end gap-3">
                                    {[{ label: 'Cold', name: 'Coldest Game', color: 'text-blue-600' },
                                      { label: 'Avg', name: 'Average Temperature', color: 'text-slate-600' },
                                      { label: 'Hot', name: 'Hottest Game', color: 'text-red-600' }].map(t => {
                                        const game = envGame(t.name);
                                        return (
                                            <div key={t.label} className="text-center flex-1">
                                                <div className={`text-lg font-bold ${t.color}`}>{envVal(t.name)}</div>
                                                <div className="text-[10px] text-slate-400">{t.label}</div>
                                                {game && <button onClick={() => goToGame(game.gameId)}
                                                    className="text-[9px] text-blue-500 hover:underline mt-0.5 block mx-auto">{game.date}</button>}
                                            </div>
                                        );
                                    })}
                                </div>
                                <div className="mt-2 h-1.5 rounded-full bg-gradient-to-r from-blue-400 via-slate-300 to-red-400 opacity-60"></div>
                            </div>

                            {/* Attendance */}
                            <div>
                                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Attendance</div>
                                <div className="flex items-end gap-3">
                                    {[{ label: 'Low', name: 'Lowest Attendance' },
                                      { label: 'Avg', name: 'Average Attendance' },
                                      { label: 'High', name: 'Highest Attendance' }].map(a => {
                                        const game = envGame(a.name);
                                        return (
                                            <div key={a.label} className="text-center flex-1">
                                                <div className="text-lg font-bold text-slate-800">{envVal(a.name)}</div>
                                                <div className="text-[10px] text-slate-400">{a.label}</div>
                                                {game && <button onClick={() => goToGame(game.gameId)}
                                                    className="text-[9px] text-blue-500 hover:underline mt-0.5 block mx-auto">{game.date}</button>}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Game Duration */}
                            <div>
                                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Game Duration</div>
                                <div className="flex items-end gap-3">
                                    {[{ label: 'Shortest', name: 'Shortest Game by Time', color: 'text-green-600' },
                                      { label: 'Longest', name: 'Longest Game by Time', color: 'text-orange-600' },
                                      { label: 'Most Inn.', name: 'Longest Game by Innings', color: 'text-purple-600' }].map(d => {
                                        const game = envGame(d.name);
                                        return (
                                            <div key={d.label} className="text-center flex-1">
                                                <div className={`text-lg font-bold ${d.color}`}>{envVal(d.name)}</div>
                                                <div className="text-[10px] text-slate-400">{d.label}</div>
                                                {game && <button onClick={() => goToGame(game.gameId)}
                                                    className="text-[9px] text-blue-500 hover:underline mt-0.5 block mx-auto">{game.date}</button>}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Timing & Weather */}
                            <div>
                                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Timing & Weather</div>
                                <div className="grid grid-cols-2 gap-2">
                                    {[{ label: 'Earliest Start', name: 'Earliest Start Time' },
                                      { label: 'Latest Start', name: 'Latest Start Time' },
                                      { label: 'Max Wind', name: 'Highest Wind Speed' },
                                      { label: 'Rain Games', name: 'Games with Precipitation' }].map(item => (
                                        <div key={item.label} className="bg-slate-50 rounded-lg p-2 text-center">
                                            <div className="text-sm font-bold text-slate-800">{envVal(item.name)}</div>
                                            <div className="text-[9px] text-slate-400">{item.label}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Section 5: Individual Records (tabbed: Hitting | Pitching) */}
            {(sections['individual-hitting'].length > 0 || sections['individual-pitching'].length > 0) && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="text-sm font-semibold text-slate-900">Team & Individual Records</div>
                        <div className="flex-1 h-px bg-slate-200"></div>
                        <div className="flex gap-1">
                            {['hitting', 'pitching'].map(tab => (
                                <button key={tab} onClick={() => setIndivTab(tab)}
                                    className={`px-3 py-1 rounded-full text-xs font-medium ${indivTab === tab ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                                    {tab === 'hitting' ? 'Hitting' : 'Pitching'} ({sections[`individual-${tab}`].length})
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {sections[`individual-${indivTab}`].map(record => (
                            <RecordCard key={record.record} record={record} compact />
                        ))}
                    </div>
                </div>
            )}

            {/* Section 6: Frequency Counts */}
            {sections.frequency.length > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="text-sm font-semibold text-slate-900">Counts & Tallies</div>
                        <div className="flex-1 h-px bg-slate-200"></div>
                    </div>
                    {expandedRecord && sections.frequency.some(r => r.record === expandedRecord) && (
                        <div className="fixed inset-0 z-[5]" onClick={() => setExpandedRecord(null)} />
                    )}
                    <div className="flex flex-wrap gap-2 relative z-10">
                        {sections.frequency.map(record => {
                            const { games } = parseRecord(record);
                            const hasContent = games.length > 0 || (record.detail && record.detail.trim());
                            const isExpanded = expandedRecord === record.record;
                            return (
                                <div key={record.record} className="relative">
                                    <button onClick={() => hasContent && setExpandedRecord(isExpanded ? null : record.record)}
                                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs border transition-all ${isExpanded ? 'bg-blue-50 border-blue-300 text-blue-800' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'} ${hasContent ? 'cursor-pointer' : 'cursor-default'}`}>
                                        <span className="font-medium">{record.record}</span>
                                        <span className={`font-bold ${isExpanded ? 'text-blue-600' : 'text-slate-900'}`}>{record.value}</span>
                                    </button>
                                    {isExpanded && hasContent && (
                                        <div className="absolute top-full left-0 mt-1 z-10 bg-white rounded-lg shadow-lg border border-slate-200 p-2 min-w-[200px] max-w-[400px]">
                                            {record.detail && (
                                                <div className="text-[11px] text-slate-600 mb-1.5 px-1">{record.detail}</div>
                                            )}
                                            {games.length > 0 && <GameButtons games={games} max={6} />}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Section 7: ABS Challenge Records */}
            {absRecords.totalGames > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-2 mt-4">
                        <div className="text-sm font-semibold text-slate-900">ABS Challenge Records</div>
                        <div className="flex-1 h-px bg-slate-200"></div>
                        <span className="text-xs text-slate-400">{absRecords.totalChallenges} challenges in {absRecords.totalGames} games</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {absRecords.topByTotal.length > 0 && (
                            <div className="bg-white border border-slate-200 rounded-lg p-4">
                                <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Most Challenges in a Game</div>
                                <div className="space-y-1.5">
                                    {absRecords.topByTotal.map((g, i) => (
                                        <div key={g.gameId} className="flex items-center gap-2 text-sm">
                                            <span className="text-slate-400 w-4 text-right">{i + 1}.</span>
                                            <span className="font-bold text-slate-800 w-6">{g.absTotal}</span>
                                            <button onClick={() => goToGame(g.gameId)} className="text-blue-600 hover:underline">{g.awayTeam} @ {g.homeTeam}</button>
                                            <span className="text-slate-400 ml-auto text-xs">{g.absOverturned} ovt · {g.date}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {absRecords.topByOverturned.length > 0 && (
                            <div className="bg-white border border-slate-200 rounded-lg p-4">
                                <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Most Overturned in a Game</div>
                                <div className="space-y-1.5">
                                    {absRecords.topByOverturned.map((g, i) => (
                                        <div key={g.gameId} className="flex items-center gap-2 text-sm">
                                            <span className="text-slate-400 w-4 text-right">{i + 1}.</span>
                                            <span className="font-bold text-green-600 w-6">{g.absOverturned}</span>
                                            <button onClick={() => goToGame(g.gameId)} className="text-blue-600 hover:underline">{g.awayTeam} @ {g.homeTeam}</button>
                                            <span className="text-slate-400 ml-auto text-xs">{g.absTotal} total · {g.date}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {absRecords.umpiresByTotal.length > 0 && (
                            <div className="bg-white border border-slate-200 rounded-lg p-4">
                                <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Most Challenges Faced (HP Umpire)</div>
                                <div className="space-y-1.5">
                                    {absRecords.umpiresByTotal.map((u, i) => (
                                        <div key={u.name} className="flex items-center gap-2 text-sm">
                                            <span className="text-slate-400 w-4 text-right">{i + 1}.</span>
                                            <span className="font-medium text-slate-800">{u.name}</span>
                                            <span className="text-slate-400 ml-auto">{u.absChallenges} challenges, {u.absOverturned || 0} overturned</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {absRecords.highestRate.length > 0 && (
                            <div className="bg-white border border-slate-200 rounded-lg p-4">
                                <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Highest Overturn Rate</div>
                                <div className="space-y-1.5">
                                    {absRecords.highestRate.map((u, i) => (
                                        <div key={u.name} className="flex items-center gap-2 text-sm">
                                            <span className="text-slate-400 w-4 text-right">{i + 1}.</span>
                                            <span className="font-medium text-slate-800">{u.name}</span>
                                            <span className="text-green-600 font-bold ml-auto">{u.overturnRate}%</span>
                                            <span className="text-slate-400 text-xs">({u.absOverturned || 0}/{u.absChallenges})</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {absRecords.lowestRate.length > 0 && (
                            <div className="bg-white border border-slate-200 rounded-lg p-4">
                                <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Lowest Overturn Rate</div>
                                <div className="space-y-1.5">
                                    {absRecords.lowestRate.map((u, i) => (
                                        <div key={u.name} className="flex items-center gap-2 text-sm">
                                            <span className="text-slate-400 w-4 text-right">{i + 1}.</span>
                                            <span className="font-medium text-slate-800">{u.name}</span>
                                            <span className="text-red-600 font-bold ml-auto">{u.overturnRate}%</span>
                                            <span className="text-slate-400 text-xs">({u.absOverturned || 0}/{u.absChallenges})</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                    {/* Player Challenge Leaderboard */}
                    {(data.absPlayerStats || []).length > 0 && (() => {
                        const [absSortKey, setAbsSortKey] = React.useState('challenges');
                        const [absSortDir, setAbsSortDir] = React.useState('desc');
                        const handleAbsSort = (key) => {
                            if (absSortKey === key) setAbsSortDir(absSortDir === 'asc' ? 'desc' : 'asc');
                            else { setAbsSortKey(key); setAbsSortDir('desc'); }
                        };
                        const sorted = [...(data.absPlayerStats || [])].sort((a, b) => {
                            let aVal = a[absSortKey], bVal = b[absSortKey];
                            if (absSortKey === 'name') { const r = String(aVal || '').localeCompare(String(bVal || '')); return absSortDir === 'asc' ? r : -r; }
                            if (absSortKey === 'avgEdgeDistance') { aVal = aVal ?? 999; bVal = bVal ?? 999; }
                            const r = (aVal || 0) - (bVal || 0);
                            return absSortDir === 'asc' ? r : -r;
                        });
                        const AbsHeader = ({ k, label }) => (
                            <th className={`px-2 py-2 text-center font-medium text-slate-500 cursor-pointer hover:bg-slate-100 ${k === 'name' ? 'text-left px-3' : ''}`}
                                onClick={() => handleAbsSort(k)}>
                                {label} {absSortKey === k && (absSortDir === 'asc' ? '↑' : '↓')}
                            </th>
                        );
                        return (
                        <div className="mt-3 bg-white border border-slate-200 rounded-lg p-4">
                            <div className="text-xs font-semibold text-slate-400 uppercase mb-3">Player Challenge Leaderboard</div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-slate-50 border-b">
                                        <tr>
                                            <AbsHeader k="name" label="Player" />
                                            <AbsHeader k="challenges" label="Challenges" />
                                            <AbsHeader k="overturned" label="Overturned" />
                                            <AbsHeader k="upheld" label="Upheld" />
                                            <AbsHeader k="successRate" label="Success %" />
                                            <AbsHeader k="asBatter" label="Batter" />
                                            <AbsHeader k="asCatcher" label="Catcher" />
                                            <AbsHeader k="asPitcher" label="Pitcher" />
                                            <AbsHeader k="avgEdgeDistance" label="Avg Edge" />
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                        {sorted.map((p) => (
                                            <tr key={p.name} className="hover:bg-blue-50">
                                                <td className="px-3 py-2 font-medium text-slate-800">{p.name}</td>
                                                <td className="px-2 py-2 text-center font-bold">{p.challenges}</td>
                                                <td className="px-2 py-2 text-center text-green-600 font-medium">{p.overturned}</td>
                                                <td className="px-2 py-2 text-center text-red-600 font-medium">{p.upheld}</td>
                                                <td className="px-2 py-2 text-center">
                                                    <span className={`font-bold ${p.successRate >= 75 ? 'text-green-600' : p.successRate >= 50 ? 'text-slate-700' : 'text-red-600'}`}>
                                                        {p.successRate}%
                                                    </span>
                                                </td>
                                                <td className="px-2 py-2 text-center text-slate-600">{p.asBatter || '-'}</td>
                                                <td className="px-2 py-2 text-center text-slate-600">{p.asCatcher || '-'}</td>
                                                <td className="px-2 py-2 text-center text-slate-600">{p.asPitcher || '-'}</td>
                                                <td className="px-2 py-2 text-center text-slate-500">{p.avgEdgeDistance != null ? p.avgEdgeDistance.toFixed(3) : '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        );
                    })()}
                </div>
            )}
        </div>
    );
};

const SpecialTab = ({ data, initialSubtab, onSubtabChange }) => {
    const [view, setView] = useState(initialSubtab || 'records');
    return (
        <div>
            <SubNav tabs={[
                { id: 'records', label: 'Records' },
                { id: 'debuts', label: 'Debuts' },
                { id: 'finals', label: 'Final Games' },
                { id: 'splash', label: 'Signature HRs' },
            ]} active={view} onChange={setView} onSubtabChange={onSubtabChange} />
            {view === 'records' && <PersonalRecords data={data} />}
            {view === 'debuts' && (
                <DataTable title="🌟 MLB Debuts" data={data.debuts || []} defaultSortKey="date" enableDateFilter={true} persistKey="debuts" columns={[
                    { key: 'date', label: 'Date' }, { key: 'player', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                    { key: 'team', label: 'Team' }, { key: 'opponent', label: 'vs' }, { key: 'position', label: 'Pos' },
                    { key: 'stats', label: 'Debut Performance', render: (v, r) => <DebutPerformance r={r} /> },
                    { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                ]} />
            )}
            {view === 'finals' && (
                <DataTable title="👋 Final MLB Games" data={data.finalGames || []} defaultSortKey="date" enableDateFilter={true} persistKey="finals" columns={[
                    { key: 'date', label: 'Date' }, { key: 'player', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                    { key: 'team', label: 'Team' }, { key: 'position', label: 'Pos' },
                    { key: 'stats', label: 'Final Performance', render: (v, r) => <DebutPerformance r={r} /> },
                    { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                ]} />
            )}
            {view === 'splash' && (
                <DataTable title="💦 Signature HRs" data={data.signatureHRs || []} defaultSortKey="date" enableDateFilter={true} persistKey="sigHRs" columns={[
                    { key: 'date', label: 'Date' }, { key: 'player', label: 'Player' }, { key: 'team', label: 'Team' },
                    { key: 'opponent', label: 'Opponent' }, { key: 'pitcher', label: 'Pitcher' }, { key: 'signatureNumber', label: 'Type' },
                    { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                ]} />
            )}
        </div>
    );
};

const ScorigamiChart = ({ games }) => {
    const [selectedCell, setSelectedCell] = useState(null);

    const data = useMemo(() => {
        const scoreCounts = {};
        const scoreGames = {};
        let maxWinner = 0;
        let maxLoser = 0;

        (games || []).forEach(game => {
            const score = game.score || '';
            const nums = score.match(/\d+/g);
            if (!nums || nums.length < 2) return;
            const a = parseInt(nums[0]);
            const b = parseInt(nums[1]);
            if (isNaN(a) || isNaN(b) || a === b) return;
            const winner = Math.max(a, b);
            const loser = Math.min(a, b);
            const key = `${loser}-${winner}`;
            scoreCounts[key] = (scoreCounts[key] || 0) + 1;
            if (!scoreGames[key]) scoreGames[key] = [];
            // Determine which team won
            const awayScore = a, homeScore = b;
            const winnerTeam = homeScore > awayScore ? game.homeTeam : game.awayTeam;
            const loserTeam = homeScore > awayScore ? game.awayTeam : game.homeTeam;
            scoreGames[key].push({ ...game, winnerTeam, loserTeam, winnerScore: winner, loserScore: loser });
            maxWinner = Math.max(maxWinner, winner);
            maxLoser = Math.max(maxLoser, loser);
        });

        // Trim to actual data range
        const displayMaxWinner = maxWinner;
        const displayMaxLoser = maxLoser;
        const unique = Object.keys(scoreCounts).length;
        return { scoreCounts, scoreGames, displayMaxWinner, displayMaxLoser, unique };
    }, [games]);

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="mb-4">
                <h2 className="section-title font-bold">Personal Scorigami</h2>
                <p className="body-text text-slate-500 mt-1">{data.unique} unique final scores witnessed</p>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full border-collapse" style={{ tableLayout: 'fixed' }}>
                    <thead>
                        <tr>
                            <th className="p-0 text-xs text-slate-500 text-center" style={{width:'30px'}}></th>
                            {Array.from({ length: data.displayMaxWinner + 1 }, (_, i) => (
                                <th key={i} className="p-0 text-xs text-slate-500 text-center">{i}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {Array.from({ length: data.displayMaxLoser + 1 }, (_, loser) => (
                            <tr key={loser}>
                                <td className="p-0 text-xs text-slate-500 text-center font-medium" style={{width:'30px'}}>{loser}</td>
                                {Array.from({ length: data.displayMaxWinner + 1 }, (_, winner) => {
                                    if (winner <= loser) {
                                        return <td key={winner} className="p-px"><div className="w-full aspect-square bg-slate-200 rounded-sm"></div></td>;
                                    }
                                    const key = `${loser}-${winner}`;
                                    const count = data.scoreCounts[key] || 0;
                                    const isSelected = selectedCell === key;
                                    return (
                                        <td key={winner} className="p-px">
                                            <button
                                                onClick={() => count > 0 && setSelectedCell(isSelected ? null : key)}
                                                className={`w-full aspect-square rounded-sm text-[10px] font-bold flex items-center justify-center transition-all ${
                                                    isSelected ? 'ring-2 ring-blue-500 bg-blue-600 text-white' :
                                                    count >= 5 ? 'bg-green-600 text-white' :
                                                    count >= 3 ? 'bg-green-400 text-white' :
                                                    count >= 2 ? 'bg-green-300 text-green-900' :
                                                    count === 1 ? 'bg-green-100 text-green-800' :
                                                    'bg-white border border-slate-200'
                                                } ${count > 0 ? 'cursor-pointer hover:ring-1 hover:ring-blue-300' : ''}`}
                                                title={count > 0 ? `${loser}-${winner}: ${count} game${count > 1 ? 's' : ''}` : `${loser}-${winner}: never seen`}
                                            >
                                                {count || ''}
                                            </button>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
                <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
                    <span>Losing score ↓</span>
                    <span>Winning score →</span>
                    <div className="flex items-center gap-1 ml-4">
                        <div className="w-3 h-3 bg-white border border-slate-200 rounded-sm"></div> <span>0</span>
                        <div className="w-3 h-3 bg-green-100 rounded-sm ml-1"></div> <span>1</span>
                        <div className="w-3 h-3 bg-green-300 rounded-sm ml-1"></div> <span>2</span>
                        <div className="w-3 h-3 bg-green-400 rounded-sm ml-1"></div> <span>3-4</span>
                        <div className="w-3 h-3 bg-green-600 rounded-sm ml-1"></div> <span>5+</span>
                    </div>
                </div>
            </div>

            {selectedCell && data.scoreGames[selectedCell] && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedCell(null)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-lg w-full max-h-[70vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b bg-green-600 text-white rounded-t-lg flex items-center justify-between">
                            <h3 className="font-bold">Final Score: {selectedCell.replace('-', ' - ')} ({data.scoreGames[selectedCell].length} game{data.scoreGames[selectedCell].length > 1 ? 's' : ''})</h3>
                            <button onClick={() => setSelectedCell(null)} className="text-white hover:text-slate-200 text-xl leading-none">&times;</button>
                        </div>
                        <div className="p-3 space-y-2">
                            {data.scoreGames[selectedCell].map((g, i) => (
                                <div key={i} className="bg-slate-50 rounded p-3 cursor-pointer hover:bg-blue-50 transition-colors"
                                    onClick={() => { window._pendingGameId = g.gameId; setSelectedCell(null); if (window.__navigateTab) window.__navigateTab('gamelog'); }}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-green-700">{g.winnerTeam} {g.winnerScore}</span>
                                            <span className="text-slate-400">def.</span>
                                            <span className="text-slate-600">{g.loserTeam} {g.loserScore}</span>
                                        </div>
                                        <span className="text-xs text-slate-500">{g.date}</span>
                                    </div>
                                    <div className="text-xs text-slate-400 mt-1">{g.awayTeam} @ {g.homeTeam} • {g.venue || ''}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const TriviaTab = ({ umpireLog, jerseyLog, playerBios, players, pitchers, games, initialSubtab, onSubtabChange }) => {
    const [view, setView] = useState(initialSubtab || 'jerseys');
    const allPlayers = useMemo(() => {
        const seen = new Set();
        return [...(players || []), ...(pitchers || [])].filter(p => { if (seen.has(p.playerId)) return false; seen.add(p.playerId); return true; });
    }, [players, pitchers]);
    return (
        <div>
            <SubNav tabs={[
                { id: 'jerseys', label: 'Jersey Numbers' },
                { id: 'origins', label: 'Origins' },
                { id: 'birthdays', label: 'Birthdays' },
                { id: 'scorigami', label: 'Scorigami' },
                { id: 'umpires', label: 'Umpires' },
            ]} active={view} onChange={setView} onSubtabChange={onSubtabChange} />
            {view === 'jerseys' && <JerseyCollection jerseyLog={jerseyLog} />}
            {view === 'origins' && <PlayerOrigins playerBios={playerBios} allPlayers={allPlayers} />}
            {view === 'birthdays' && <PlayerBirthdays playerBios={playerBios} allPlayers={allPlayers} />}
            {view === 'scorigami' && <ScorigamiChart games={games} />}
            {view === 'umpires' && <UmpireTracker umpireLog={umpireLog} games={games} />}
        </div>
    );
};

// Reusable subtab navigation
const SubNav = ({ tabs, active, onChange, onSubtabChange }) => (
    <div className="flex flex-wrap gap-1 mb-4 bg-slate-100 rounded-lg p-1">
        {tabs.map(t => (
            <button key={t.id} onClick={() => { onChange(t.id); if (onSubtabChange) onSubtabChange(t.id); }} className={`px-3.5 py-1.5 rounded-md text-[13px] font-medium transition-all ${
                active === t.id
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
            }`}>
                {t.label}
            </button>
        ))}
    </div>
);

// === MERGED TAB WRAPPERS ===

// Players tab: absorbs Leaderboards
const PlayersTabV2 = ({ data, initialSubtab, onSubtabChange }) => {
    const hasCollegeData = Object.keys(data.ncaaCrossRef || {}).length > 0;
    const [view, setView] = useState(initialSubtab || 'hitters');

    useEffect(() => {
        if (window._pendingPlayerSelect) {
            const pid = window._pendingPlayerSelect.id;
            const isPitcher = (data.pitchers || []).some(p => p.playerId === pid) && !(data.players || []).some(p => p.playerId === pid);
            setView(isPitcher ? 'pitchers' : 'hitters');
        }
    });

    const handleViewPlayer = (playerId, name) => {
        setView('hitters');
        window._pendingPlayerSelect = { id: playerId, name };
    };

    const subtabs = [
        { id: 'hitters', label: 'Hitters' },
        { id: 'pitchers', label: 'Pitchers' },
        ...((data.playersWithoutStats || []).length > 0 ? [{ id: 'nostats', label: 'No Stats' }] : []),
        ...(hasCollegeData ? [{ id: 'college', label: 'College & MiLB' }] : []),
        { id: 'leaders', label: 'Leaderboards' },
        { id: 'statcast', label: 'Statcast' },
    ];

    return (
        <div>
            <SubNav tabs={subtabs} active={view} onChange={setView} onSubtabChange={onSubtabChange} />
            {view === 'hitters' && <DynamicPlayerTable allPlayers={data.players || []} playerGames={data.playerGames || []} ncaaCrossRef={data.ncaaCrossRef} careerFirstsByPlayer={data.careerFirstsByPlayer || {}} allTimePassings={data.allTimePassings || []} milestones={data.milestones || []} debuts={data.debuts || []} finalGames={data.finalGames || []} />}
            {view === 'pitchers' && <DynamicPitcherTable allPitchers={data.pitchers || []} pitcherGames={data.pitcherGames || []} ncaaCrossRef={data.ncaaCrossRef} careerFirstsByPlayer={data.careerFirstsByPlayer || {}} allTimePassings={data.allTimePassings || []} milestones={data.milestones || []} debuts={data.debuts || []} finalGames={data.finalGames || []} />}
            {view === 'nostats' && <NoStatsPlayers data={data} />}
            {view === 'college' && <CollegePlayersView data={data} onViewPlayer={handleViewPlayer} />}
            {view === 'leaders' && (data.players?.length ? <Leaderboards data={data} /> : <EmptyState icon="🏅" title="No Player Data" message="No player statistics available." />)}
            {view === 'statcast' && <StatcastView playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} games={data.games || []} />}
        </div>
    );
};

// Milestones tab: absorbs History
const MilestonesTabV2 = ({ data, onTabChange, initialSubtab, onSubtabChange }) => {
    const [view, setView] = useState(initialSubtab || 'milestones');
    return (
        <div>
            <SubNav tabs={[
                { id: 'milestones', label: 'Game Milestones' },
                { id: 'history', label: 'All-Time Passings' },
            ]} active={view} onChange={setView} onSubtabChange={onSubtabChange} />
            {view === 'milestones' && (data.milestones?.length ? <MilestonesView milestones={data.milestones} games={data.games || []} careerFirsts={data.careerFirsts || []} allTimePassings={data.allTimePassings || []} onTabChange={onTabChange} /> : <EmptyState icon="🏆" title="No Milestones" message="No milestones have been recorded yet." />)}
            {view === 'history' && <HistoryWitnessedView allTimePassings={data.allTimePassings || []} careerFirsts={data.careerFirsts || []} games={data.games || []} />}
        </div>
    );
};

// Statcast leaderboards view
const StatcastView = ({ playerGames, pitcherGames, games }) => {
    const gameInfo = useMemo(() => {
        const venueMap = {};
        const dateMap = {};
        (games || []).forEach(g => {
            if (g.gameId) {
                venueMap[g.gameId] = g.venue || '';
                dateMap[g.gameId] = g.date || '';
            }
        });
        return { venueMap, dateMap };
    }, [games]);

    const hardestHits = useMemo(() => {
        return (playerGames || [])
            .filter(pg => pg.maxExitVelo)
            .map(pg => ({
                name: pg.name, playerId: pg.playerId, team: pg.team,
                maxExitVelo: pg.maxExitVelo, maxDistance: pg.maxDistance || 0,
                date: pg.date || gameInfo.dateMap[pg.gameId] || '', venue: gameInfo.venueMap[pg.gameId] || '',
            }))
            .sort((a, b) => b.maxExitVelo - a.maxExitVelo);
    }, [playerGames, gameInfo]);

    const longestBalls = useMemo(() => {
        return (playerGames || [])
            .filter(pg => pg.maxDistance && pg.maxDistance > 0)
            .map(pg => ({
                name: pg.name, playerId: pg.playerId, team: pg.team,
                maxDistance: pg.maxDistance, maxExitVelo: pg.maxExitVelo || 0,
                date: pg.date || gameInfo.dateMap[pg.gameId] || '', venue: gameInfo.venueMap[pg.gameId] || '',
            }))
            .sort((a, b) => b.maxDistance - a.maxDistance);
    }, [playerGames, gameInfo]);

    const fastestPitches = useMemo(() => {
        return (pitcherGames || [])
            .filter(pg => pg.maxSpeed)
            .map(pg => ({
                name: pg.name, playerId: pg.playerId, team: pg.team,
                maxSpeed: pg.maxSpeed, totalPitches: pg.totalPitches || 0,
                date: pg.date || gameInfo.dateMap[pg.gameId] || '', venue: gameInfo.venueMap[pg.gameId] || '',
            }))
            .sort((a, b) => b.maxSpeed - a.maxSpeed);
    }, [pitcherGames, gameInfo]);

    const highestSpin = useMemo(() => {
        return (pitcherGames || [])
            .filter(pg => pg.avgSpinRate && pg.avgSpinRate > 0)
            .map(pg => ({
                name: pg.name, playerId: pg.playerId, team: pg.team,
                avgSpinRate: pg.avgSpinRate, maxSpeed: pg.maxSpeed || 0, totalPitches: pg.totalPitches || 0,
                date: pg.date || gameInfo.dateMap[pg.gameId] || '', venue: gameInfo.venueMap[pg.gameId] || '',
            }))
            .sort((a, b) => b.avgSpinRate - a.avgSpinRate);
    }, [pitcherGames, gameInfo]);

    const slowestPitches = useMemo(() => {
        return (pitcherGames || [])
            .filter(pg => pg.minSpeed && pg.minSpeed > 0)
            .map(pg => ({
                name: pg.name, playerId: pg.playerId, team: pg.team,
                minSpeed: pg.minSpeed, maxSpeed: pg.maxSpeed || 0, totalPitches: pg.totalPitches || 0,
                date: pg.date || gameInfo.dateMap[pg.gameId] || '', venue: gameInfo.venueMap[pg.gameId] || '',
            }))
            .sort((a, b) => a.minSpeed - b.minSpeed);
    }, [pitcherGames, gameInfo]);

    const lowestSpin = useMemo(() => {
        return (pitcherGames || [])
            .filter(pg => pg.minSpinRate && pg.minSpinRate > 0)
            .map(pg => ({
                name: pg.name, playerId: pg.playerId, team: pg.team,
                minSpinRate: pg.minSpinRate, maxSpeed: pg.maxSpeed || 0, totalPitches: pg.totalPitches || 0,
                date: pg.date || gameInfo.dateMap[pg.gameId] || '', venue: gameInfo.venueMap[pg.gameId] || '',
            }))
            .sort((a, b) => a.minSpinRate - b.minSpinRate);
    }, [pitcherGames, gameInfo]);

    const evCount = (playerGames || []).filter(pg => pg.maxExitVelo).length;
    const pitchCount = (pitcherGames || []).filter(pg => pg.maxSpeed).length;
    const playerCol = { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> };

    return (
        <div className="space-y-6">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm text-slate-600">
                Exit velo data available for <strong>{evCount.toLocaleString()}</strong> of {(playerGames || []).length.toLocaleString()} batter games.
                {' '}Pitch data available for <strong>{pitchCount.toLocaleString()}</strong> of {(pitcherGames || []).length.toLocaleString()} pitcher games.
            </div>
            <DataTable title="Hardest Hit Balls" data={hardestHits} defaultSortKey="maxExitVelo" persistKey="statcast-ev" columns={[
                playerCol, { key: 'team', label: 'Team' },
                { key: 'maxExitVelo', label: 'Exit Velo', render: v => <span className="font-mono">{v} mph</span> },
                { key: 'maxDistance', label: 'Distance', render: v => v ? <span className="font-mono">{v} ft</span> : '—' },
                { key: 'date', label: 'Date' }, { key: 'venue', label: 'Venue' },
            ]} />
            <DataTable title="Longest Batted Balls" data={longestBalls} defaultSortKey="maxDistance" persistKey="statcast-dist" columns={[
                playerCol, { key: 'team', label: 'Team' },
                { key: 'maxDistance', label: 'Distance', render: v => <span className="font-mono">{v} ft</span> },
                { key: 'maxExitVelo', label: 'Exit Velo', render: v => v ? <span className="font-mono">{v} mph</span> : '—' },
                { key: 'date', label: 'Date' }, { key: 'venue', label: 'Venue' },
            ]} />
            <DataTable title="Fastest Pitches" data={fastestPitches} defaultSortKey="maxSpeed" persistKey="statcast-speed" columns={[
                playerCol, { key: 'team', label: 'Team' },
                { key: 'maxSpeed', label: 'Speed', render: v => <span className="font-mono">{v} mph</span> },
                { key: 'totalPitches', label: 'Pitches' },
                { key: 'date', label: 'Date' }, { key: 'venue', label: 'Venue' },
            ]} />
            <DataTable title="Highest Avg Spin Rates" data={highestSpin} defaultSortKey="avgSpinRate" persistKey="statcast-spin" columns={[
                playerCol, { key: 'team', label: 'Team' },
                { key: 'avgSpinRate', label: 'Spin Rate', render: v => <span className="font-mono">{v.toLocaleString()} rpm</span> },
                { key: 'maxSpeed', label: 'Speed', render: v => v ? <span className="font-mono">{v} mph</span> : '—' },
                { key: 'totalPitches', label: 'Pitches' },
                { key: 'date', label: 'Date' }, { key: 'venue', label: 'Venue' },
            ]} />
            <DataTable title="Slowest Pitches" data={slowestPitches} defaultSortKey="minSpeed" defaultSortDir="asc" persistKey="statcast-speed-slow" columns={[
                playerCol, { key: 'team', label: 'Team' },
                { key: 'minSpeed', label: 'Speed', render: v => <span className="font-mono">{v} mph</span> },
                { key: 'maxSpeed', label: 'Max', render: v => v ? <span className="font-mono">{v} mph</span> : '—' },
                { key: 'totalPitches', label: 'Pitches' },
                { key: 'date', label: 'Date' }, { key: 'venue', label: 'Venue' },
            ]} />
            <DataTable title="Lowest Single-Pitch Spin Rates" data={lowestSpin} defaultSortKey="minSpinRate" defaultSortDir="asc" persistKey="statcast-spin-low" columns={[
                playerCol, { key: 'team', label: 'Team' },
                { key: 'minSpinRate', label: 'Spin Rate', render: v => <span className="font-mono">{v.toLocaleString()} rpm</span> },
                { key: 'maxSpeed', label: 'Speed', render: v => v ? <span className="font-mono">{v} mph</span> : '—' },
                { key: 'totalPitches', label: 'Pitches' },
                { key: 'date', label: 'Date' }, { key: 'venue', label: 'Venue' },
            ]} />
        </div>
    );
};

// Venues tab: absorbs Calendar + Statcast
const VenuesTab = ({ data, initialSubtab, onSubtabChange }) => {
    const [view, setView] = useState(initialSubtab || 'map');

    const enhancedStadiums = useMemo(() => {
        const gamesByVenue = {};
        (data.games || []).forEach(g => {
            const v = g.venue;
            if (!v) return;
            if (!gamesByVenue[v]) gamesByVenue[v] = [];
            gamesByVenue[v].push(g);
        });
        return (data.stadiums || []).map(s => {
            const venueGames = gamesByVenue[s.stadium] || [];
            let totalRuns = 0, totalMargin = 0, parsed = 0;
            venueGames.forEach(g => {
                const m = (g.score || '').match(/(\d+)\s*-\s*(\d+)/);
                if (m) {
                    const r1 = parseInt(m[1]), r2 = parseInt(m[2]);
                    totalRuns += r1 + r2;
                    totalMargin += Math.abs(r1 - r2);
                    parsed++;
                }
            });
            return {
                ...s,
                hrsPerGame: s.games > 0 ? Math.round(s.homeRunsSeen / s.games * 10) / 10 : 0,
                runsPerGame: parsed > 0 ? Math.round(totalRuns / parsed * 10) / 10 : 0,
                avgMargin: parsed > 0 ? Math.round(totalMargin / parsed * 10) / 10 : 0,
            };
        });
    }, [data.stadiums, data.games]);

    return (
        <div>
            <SubNav tabs={[
                { id: 'map', label: 'Map & Tables' },
                { id: 'calendar', label: 'Calendar' },
            ]} active={view} onChange={setView} onSubtabChange={onSubtabChange} />
            {view === 'map' && ((data.stadiums?.length || data.teams?.length) ? (
                <div className="space-y-6">
                    <StadiumMap stadiums={data.stadiums || []} games={data.games || []} orioles={data.orioles || []} />
                    <DataTable title="Teams" data={data.teams || []} defaultSortKey="games" persistKey="teams" columns={[
                        { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'record', label: 'Record' },
                        { key: 'runs', label: 'R' }, { key: 'runsAllowed', label: 'RA' }, { key: 'diff', label: 'Diff' },
                        { key: 'homeRecord', label: 'Home' }, { key: 'awayRecord', label: 'Away' },
                        { key: 'oneRunGames', label: '1-Run' }, { key: 'blowouts', label: 'Blowouts' }
                    ]} />
                    <DataTable title="Stadiums" data={enhancedStadiums} defaultSortKey="games" persistKey="stadiums" columns={[
                        { key: 'stadium', label: 'Stadium' }, { key: 'games', label: 'G' }, { key: 'firstVisit', label: 'First' },
                        { key: 'lastVisit', label: 'Last' }, { key: 'span', label: 'Span' }, { key: 'avgAttendance', label: 'Avg Att.' },
                        { key: 'homeRunsSeen', label: 'HRs' }, { key: 'hrsPerGame', label: 'HR/G' },
                        { key: 'runsPerGame', label: 'R/G' }, { key: 'avgMargin', label: 'Avg Margin' },
                        { key: 'hitsSeen', label: 'Hits' }, { key: 'strikeoutsSeen', label: 'SOs' },
                        { key: 'teamsSeen', label: 'Teams' }, { key: 'homeTeamRecord', label: 'Home Record' }
                    ]} />
                </div>
            ) : <EmptyState icon="🏟️" title="No Venue Data" message="No stadium or team records available." />)}
            {view === 'calendar' && (data.games?.length ? <Calendar games={data.games} /> : <EmptyState icon="📅" title="No Games" message="No games to display on the calendar." />)}
        </div>
    );
};

// Progress tab: absorbs Matchups
const ProgressTab = ({ data, initialSubtab, onSubtabChange }) => {
    const [view, setView] = useState(initialSubtab || 'checklist');
    return (
        <div>
            <SubNav tabs={[
                { id: 'checklist', label: 'Division Checklist' },
                { id: 'badges', label: 'Badges' },
                { id: 'matchups', label: 'Matchups' },
            ]} active={view} onChange={setView} onSubtabChange={onSubtabChange} />
            {view === 'checklist' && <DivisionChecklist divisionChecklist={data.divisionChecklist} games={data.games || []} />}
            {view === 'badges' && <BadgesDisplay games={data.games || []} />}
            {view === 'matchups' && (data.matchupMatrix ? <MatchupMatrix matchupData={data.matchupMatrix} games={data.games || []} /> : <EmptyState icon="🎯" title="No Matchup Data" message="No matchup data available." />)}
        </div>
    );
};

const VALID_TABS = new Set(['dashboard','gamelog','players','milestones','venues','progress','special','trivia','companions','orioles']);
// Legacy tab redirects (old tab IDs -> new locations)
const TAB_REDIRECTS = { 'calendar': 'venues', 'history': 'milestones', 'leaderboards': 'players', 'matchups': 'progress' };

const App = () => {
    const parseHash = (hash) => {
        const parts = (hash || '').split('/');
        let tabId = parts[0];
        if (TAB_REDIRECTS[tabId]) tabId = TAB_REDIRECTS[tabId];
        return { tab: VALID_TABS.has(tabId) ? tabId : null, subtab: parts[1] || null };
    };

    const [tab, setTabRaw] = useState(() => {
        const { tab: t } = parseHash(window.location.hash.slice(1));
        if (t) return t;
        const saved = localStorage.getItem('baseballActiveTab');
        if (saved && VALID_TABS.has(saved)) return saved;
        if (saved && TAB_REDIRECTS[saved]) return TAB_REDIRECTS[saved];
        return 'dashboard';
    });
    const [subtab, setSubtab] = useState(() => {
        const { subtab: s } = parseHash(window.location.hash.slice(1));
        return s;
    });
    const subtabMemory = useRef({}); // Remember last subtab per tab

    const setTab = (newTab) => {
        // Save current subtab for current tab
        if (subtab) subtabMemory.current[tab] = subtab;
        setTabRaw(newTab);
        // Restore remembered subtab for the new tab (or null)
        setSubtab(subtabMemory.current[newTab] || null);
    };
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('baseballDarkMode');
        if (saved !== null) return saved === 'true';
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });
    const [data, setData] = useState(BASEBALL_DATA);
    const [loadError, setLoadError] = useState(DATA_LOAD_ERROR);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchOpen, setSearchOpen] = useState(false);
    const [showScrollTop, setShowScrollTop] = useState(false);
    const [navCanScrollLeft, setNavCanScrollLeft] = useState(false);
    const [navCanScrollRight, setNavCanScrollRight] = useState(true);
    const searchRef = useRef(null);
    const navScrollRef = useRef(null);

    useEffect(() => {
        if (!data && !loadError) {
            window.__onDataReady = (d) => setData(d);
            window.__onDataError = (e) => setLoadError(e);
            if (BASEBALL_DATA) setData(BASEBALL_DATA);
            if (DATA_LOAD_ERROR) setLoadError(DATA_LOAD_ERROR);
        }
        return () => { window.__onDataReady = null; window.__onDataError = null; };
    }, []);

    useEffect(() => {
        localStorage.setItem('baseballActiveTab', tab);
        const hashTarget = subtab ? `${tab}/${subtab}` : tab;
        if (window.location.hash.slice(1) !== hashTarget) {
            history.replaceState(null, '', '#' + hashTarget);
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [tab, subtab]);

    useEffect(() => {
        const onHashChange = () => {
            const { tab: t, subtab: s } = parseHash(window.location.hash.slice(1));
            if (t) { setTabRaw(t); setSubtab(s); }
        };
        window.addEventListener('hashchange', onHashChange);
        return () => window.removeEventListener('hashchange', onHashChange);
    }, []);

    useEffect(() => {
        document.documentElement.classList.toggle('dark', darkMode);
        localStorage.setItem('baseballDarkMode', darkMode);
    }, [darkMode]);

    // Global tab navigation for cross-linking from child components
    useEffect(() => {
        window.__navigateTab = (tabId, subId) => {
            let resolved = tabId;
            if (TAB_REDIRECTS[tabId]) resolved = TAB_REDIRECTS[tabId];
            if (VALID_TABS.has(resolved)) { setTabRaw(resolved); setSubtab(subId || null); }
        };
        return () => { window.__navigateTab = null; };
    }, []);

    // Scroll-to-top visibility
    useEffect(() => {
        const onScroll = () => setShowScrollTop(window.scrollY > 400);
        window.addEventListener('scroll', onScroll, { passive: true });
        return () => window.removeEventListener('scroll', onScroll);
    }, []);

    // Nav scroll indicator initialization
    useEffect(() => {
        const el = navScrollRef.current;
        if (!el) return;
        const check = () => {
            setNavCanScrollLeft(el.scrollLeft > 4);
            setNavCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
        };
        check();
        window.addEventListener('resize', check);
        return () => window.removeEventListener('resize', check);
    }, [data]);

    // Keyboard shortcuts
    useEffect(() => {
        const tabIds = [...VALID_TABS];
        const onKey = (e) => {
            if (e.key === 'Escape') {
                if (searchOpen) { setSearchOpen(false); return; }
                // Close any open modal by dispatching a custom event
                window.dispatchEvent(new CustomEvent('closeModals'));
            }
            // Don't navigate tabs if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                const idx = tabIds.indexOf(tab);
                if (idx === -1) return;
                const next = e.key === 'ArrowRight' ? (idx + 1) % tabIds.length : (idx - 1 + tabIds.length) % tabIds.length;
                setTab(tabIds[next]);
            }
            // "/" focuses search
            if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                const input = searchRef.current?.querySelector('input');
                if (input) { input.focus(); setSearchOpen(true); }
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [tab, searchOpen]);

    const searchResults = useMemo(() => {
        if (!data || !searchQuery || searchQuery.length < 2) return { items: [], totalPlayers: 0 };
        const q = searchQuery.toLowerCase();
        const items = [];
        let totalPlayers = 0;

        // Search players (with stats context)
        const seenPlayers = new Set();
        (data.players || []).forEach(p => {
            if (p.name && p.name.toLowerCase().includes(q) && !seenPlayers.has(p.playerId)) {
                seenPlayers.add(p.playerId);
                totalPlayers++;
                if (items.filter(r => r.type === 'player' || r.type === 'pitcher').length < 6) {
                    items.push({ type: 'player', label: p.name, sub: `${p.team || ''} • ${p.games}G, ${p.avg || ''} AVG, ${p.hr || 0} HR`, tab: 'players', id: p.playerId });
                }
            }
        });
        (data.pitchers || []).forEach(p => {
            if (p.name && p.name.toLowerCase().includes(q) && !seenPlayers.has(p.playerId)) {
                seenPlayers.add(p.playerId);
                totalPlayers++;
                if (items.filter(r => r.type === 'player' || r.type === 'pitcher').length < 6) {
                    items.push({ type: 'pitcher', label: p.name, sub: `${p.team || ''} • ${p.games}G, ${p.era || ''} ERA, ${p.so || 0} K`, tab: 'players', id: p.playerId });
                }
            }
        });

        // Search games (by team name or date)
        const seenGames = new Set();
        (data.games || []).forEach(g => {
            if (items.filter(r => r.type === 'game').length >= 4) return;
            const text = `${g.awayTeam || ''} ${g.homeTeam || ''} ${g.date || ''} ${g.venue || ''}`.toLowerCase();
            if (text.includes(q) && !seenGames.has(g.gameId)) {
                seenGames.add(g.gameId);
                items.push({ type: 'game', label: `${g.awayTeam} @ ${g.homeTeam}`, sub: g.date || '', tab: 'gamelog', id: g.gameId });
            }
        });

        // Search milestones
        (data.milestones || []).forEach(m => {
            if (items.filter(r => r.type === 'milestone').length >= 4) return;
            const text = `${m.player || ''} ${m.type || ''} ${m.description || ''}`.toLowerCase();
            if (text.includes(q)) {
                items.push({ type: 'milestone', label: m.player || m.type, sub: m.description || m.type || '', tab: 'milestones' });
            }
        });

        return { items, totalPlayers };
    }, [data, searchQuery]);

    useEffect(() => {
        if (!searchOpen) return;
        const handleClick = (e) => {
            if (searchRef.current && !searchRef.current.contains(e.target)) setSearchOpen(false);
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, [searchOpen]);

    if (loadError) {
        const isFileProtocol = loadError === 'file_protocol';
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
                <div className="bg-white rounded-xl shadow-lg p-8 max-w-lg text-center">
                    <h2 className="text-xl font-bold text-slate-800 mb-4">{isFileProtocol ? 'Local File Access' : 'Failed to Load Data'}</h2>
                    {isFileProtocol ? (
                        <div className="text-left text-slate-600 space-y-3">
                            <p>This page needs a local server to load data. Run one of these from the folder containing this file:</p>
                            <pre className="bg-slate-100 p-3 rounded text-sm overflow-x-auto">python3 -m http.server 8000</pre>
                            <p>Then open <a href="http://localhost:8000" className="text-blue-600 underline">http://localhost:8000</a></p>
                        </div>
                    ) : (
                        <p className="text-slate-600">{loadError}</p>
                    )}
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
                <div className="text-center">
                    <div className="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full" style={{ animation: 'spin 1s linear infinite' }}></div>
                    <p className="mt-4 text-lg font-medium text-slate-600">Loading baseball data...</p>
                </div>
            </div>
        );
    }

    const tabs = [
        { id: 'dashboard', label: 'Dashboard' },
        { id: 'gamelog', label: 'Games' },
        { id: 'players', label: 'Players' },
        { id: 'milestones', label: 'Milestones' },
        { id: 'venues', label: 'Venues' },
        { id: 'progress', label: 'Progress' },
        { id: 'special', label: 'Special' },
        { id: 'trivia', label: 'Frivolities' },
        { id: 'companions', label: 'With' },
        { id: 'orioles', label: 'Orioles' },
    ];
    
    return (
        <div className={`min-h-screen ${darkMode ? 'bg-slate-950' : 'bg-slate-50'}`}>
            <header className={`${darkMode ? 'bg-slate-900' : 'bg-white'} border-b ${darkMode ? 'border-slate-800' : 'border-slate-200'}`}>
                <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                    <div>
                        <h1 className={`text-base sm:text-lg font-bold tracking-tight ${darkMode ? 'text-white' : 'text-slate-900'}`}>Baseball Statistics Portal</h1>
                        <p className={`text-xs mt-0.5 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{data.games?.length || 0} games attended • {new Set([...(data.players || []).map(p => p.playerId), ...(data.pitchers || []).map(p => p.playerId), ...(data.playersWithoutStats || []).map(p => p.playerId)]).size} players seen</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div ref={searchRef} role="search" className="relative flex-1 sm:flex-none">
                            <input
                                type="text"
                                placeholder="Search..."
                                aria-label="Search players, games, and milestones"
                                value={searchQuery}
                                onChange={(e) => { setSearchQuery(e.target.value); setSearchOpen(true); }}
                                onFocus={() => setSearchOpen(true)}
                                className={`w-full sm:w-48 md:w-64 px-3 py-2 rounded-lg text-sm transition-colors border ${darkMode ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:border-blue-500' : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:border-blue-500'} outline-none`}
                            />
                            {searchOpen && searchQuery.length >= 2 && (
                                <div className={`absolute top-full right-0 mt-1 w-80 sm:w-96 rounded-lg shadow-md border z-[60] max-h-96 overflow-y-auto ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'}`}>
                                    {searchResults.items.length === 0 ? (
                                        <div className={`px-4 py-6 text-center text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>No results for "{searchQuery}"</div>
                                    ) : (<>
                                        {searchResults.items.map((r, i) => {
                                            const q = searchQuery.toLowerCase();
                                            const idx = r.label.toLowerCase().indexOf(q);
                                            const highlighted = idx >= 0 ? <>{r.label.slice(0, idx)}<span className="bg-yellow-200 text-yellow-900 rounded px-0.5">{r.label.slice(idx, idx + searchQuery.length)}</span>{r.label.slice(idx + searchQuery.length)}</> : r.label;
                                            return (
                                                <button key={`search-${r.type}-${r.id || r.label}-${i}`} onClick={() => { setTab(r.tab); if (r.id && r.type !== 'game') { window._pendingPlayerSelect = { id: r.id, name: r.label }; } if (r.type === 'game') { window._pendingGameId = r.id; } setSearchQuery(''); setSearchOpen(false); }}
                                                    className={`w-full text-left px-4 py-2 flex items-center gap-3 transition-colors ${darkMode ? 'hover:bg-slate-700 text-slate-200' : 'hover:bg-blue-50 text-slate-800'}`}>
                                                    <span className="text-xs font-medium uppercase opacity-50 w-14 shrink-0">{r.type}</span>
                                                    <div className="min-w-0">
                                                        <div className="text-sm font-medium truncate">{highlighted}</div>
                                                        {r.sub && <div className={`text-xs truncate ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{r.sub}</div>}
                                                    </div>
                                                </button>
                                            );
                                        })}
                                        {searchResults.totalPlayers > 6 && (
                                            <button onClick={() => { window._pendingPlayerSearch = searchQuery; setTab('players'); setSearchQuery(''); setSearchOpen(false); }}
                                                className={`w-full text-center px-4 py-2 text-xs font-medium border-t transition-colors ${darkMode ? 'text-blue-400 border-slate-700 hover:bg-slate-700' : 'text-blue-600 border-slate-100 hover:bg-blue-50'}`}>
                                                View all {searchResults.totalPlayers} player matches
                                            </button>
                                        )}
                                    </>)}
                                </div>
                            )}
                        </div>
                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className={`px-3 py-2 rounded-lg transition-colors border ${darkMode ? 'bg-slate-700 border-slate-600 hover:bg-slate-600 text-white' : 'bg-slate-50 border-slate-300 hover:bg-slate-100 text-slate-700'}`}
                            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            {darkMode ? '☀️' : '🌙'}
                        </button>
                    </div>
                </div>
            </header>
            <nav className={`sticky top-0 z-50 ${darkMode ? 'bg-slate-900 border-b border-slate-800' : 'bg-white border-b border-slate-200'}`} style={{ boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.04)' }}>
                <div className="max-w-7xl mx-auto px-2 sm:px-4">
                    <div className="relative">
                        <div ref={navScrollRef} className="flex overflow-x-auto" role="tablist" aria-label="Main navigation" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}
                            onScroll={(e) => {
                                const el = e.target;
                                setNavCanScrollLeft(el.scrollLeft > 4);
                                setNavCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
                            }}>
                            {tabs.map(t => (
                                <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)} className={`px-3 sm:px-4 py-2.5 text-xs sm:text-[13px] whitespace-nowrap flex-shrink-0 border-b-2 transition-colors ${
                                    tab === t.id
                                        ? (darkMode ? 'text-blue-400 border-blue-400 font-semibold' : 'text-blue-700 border-blue-700 font-semibold')
                                        : (darkMode ? 'text-slate-400 hover:text-slate-200 border-transparent' : 'text-slate-500 hover:text-slate-800 border-transparent')
                                }`}>
                                    {t.label}
                                </button>
                            ))}
                        </div>
                        {navCanScrollLeft && <div className="absolute left-0 top-0 bottom-0 w-8 pointer-events-none" style={{ background: `linear-gradient(to right, ${darkMode ? '#0f172a' : '#ffffff'}, transparent)` }} />}
                        {navCanScrollRight && <div className="absolute right-0 top-0 bottom-0 w-8 pointer-events-none" style={{ background: `linear-gradient(to left, ${darkMode ? '#0f172a' : '#ffffff'}, transparent)` }} />}
                    </div>
                </div>
            </nav>
            <main role="tabpanel" className="max-w-7xl mx-auto px-2 sm:px-4 py-4 sm:py-8">
                {tab === 'dashboard' && <Dashboard data={data} onTabChange={setTab} />}
                {tab === 'gamelog' && (data.games?.length ? <GameLogWithDetails games={data.games} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} careerFirstsByGame={data.careerFirstsByGame || {}} allTimePassingsByGame={data.allTimePassingsByGame || {}} /> : <EmptyState icon="📋" title="No Games" message="Add game HTML files to the Current Season Games folder and run the processor." />)}
                {tab === 'players' && <PlayersTabV2 data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'milestones' && <MilestonesTabV2 data={data} onTabChange={setTab} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'venues' && <VenuesTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'progress' && <ProgressTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'special' && <SpecialTab data={data} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'trivia' && <TriviaTab umpireLog={data.umpireLog || []} jerseyLog={data.jerseyLog || {}} playerBios={data.playerBios || {}} players={data.players || []} pitchers={data.pitchers || []} games={data.games || []} initialSubtab={subtab} onSubtabChange={setSubtab} />}
                {tab === 'companions' && <CompanionsView companionData={data.companionData} />}
                {tab === 'orioles' && <OriolesDashboard orioles={data.orioles || []} games={data.games || []} />}
            </main>
            <footer className={`border-t mt-8 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                <div className="max-w-7xl mx-auto px-4 py-5 flex items-center justify-between">
                    <p className={`small-text ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                        Baseball Statistics Portal
                    </p>
                    {data.generatedAt && <p className={`small-text ${darkMode ? 'text-slate-600' : 'text-slate-300'}`}>{data.generatedAt}</p>}
                </div>
            </footer>
            {showScrollTop && (
                <button
                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                    className={`fixed bottom-6 right-6 w-10 h-10 rounded-full shadow-lg flex items-center justify-center transition-all z-50 ${darkMode ? 'bg-slate-700 hover:bg-slate-600 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
                    title="Scroll to top"
                    aria-label="Scroll to top"
                >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3L3 8h3v5h4V8h3L8 3z" fill="currentColor"/></svg>
                </button>
            )}
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<ErrorBoundary><App /></ErrorBoundary>);
"""