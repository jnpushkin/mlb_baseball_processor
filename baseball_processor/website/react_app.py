"""React component code for the baseball statistics website."""

class ReactComponents:
    """React component templates."""
    
    @staticmethod
    def get_app_code():
        """Get the complete React app code with enhanced interactive insights."""
        return """const { useState, useMemo, useEffect, useRef } = React;

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
        window._pendingPlayerSelect = { id: playerId, name };
        if (window.__navigateTab) window.__navigateTab('players');
    };

    return (
        <span className="inline-flex items-center gap-1">
            <a href="#players" onClick={handleClick} className="text-blue-600 hover:underline">{name}</a>
            <a href={brefUrl} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-600 text-[10px]" title="View on Baseball Reference">↗</a>
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
        <h3 className="subsection-title font-bold text-gray-700 mb-2">{title}</h3>
        <p className="body-text text-gray-500 max-w-md">{message}</p>
    </div>
);

const MilestoneChart = ({ milestones }) => {
    const canvasRef = useRef(null);
    useEffect(() => {
        if (!canvasRef.current || !milestones?.length) return;
        const ctx = canvasRef.current.getContext('2d');
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
                        ticks: {
                            font: { size: 11 }
                        }
                    },
                    y: {
                        ticks: {
                            font: { size: 12 }
                        }
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
                            usePointStyle: true
                        }
                    }
                }, 
                scales: { 
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            font: { size: 11 }
                        }
                    },
                    x: {
                        ticks: {
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                } 
            }
        });
        return () => chart.destroy();
    }, [teams]);
    return <canvas ref={canvasRef} className="w-full" style={{ height: '280px' }} />;
};

const StatCard = ({ title, value, subtitle, color = 'blue', onClick }) => {
    const colors = {
        blue: 'border-blue-200 bg-blue-50', green: 'border-green-200 bg-green-50',
        purple: 'border-purple-200 bg-purple-50', orange: 'border-orange-200 bg-orange-50'
    };
    return (
        <div onClick={onClick} className={`bg-white rounded-lg shadow border-l-4 ${colors[color]} p-6 hover:shadow-lg transition-all ${onClick ? 'cursor-pointer' : ''}`}>
            <h3 className="small-text font-medium text-gray-600 mb-2">{title}</h3>
            <p className="text-3xl font-bold text-gray-900">{value}</p>
            {subtitle && <p className="body-text text-gray-500 mt-1">{subtitle}</p>}
        </div>
    );
};


const GameDetailsModal = ({ game, playerGames, pitcherGames, careerFirsts, allTimePassings, badges, onClose }) => {
    const [activeTab, setActiveTab] = useState('boxscore');
    
    const gameData = useMemo(() => {
        if (!game) return null;
        
        // Get all players/pitchers from this game
        const gamePlayers = playerGames.filter(pg => pg.gameId === game.gameId);
        const gamePitchers = pitcherGames.filter(pg => pg.gameId === game.gameId);
        
        // Separate by team
        const homeHitters = gamePlayers.filter(p => p.team === game.homeTeam).sort((a, b) => b.pa - a.pa);
        const awayHitters = gamePlayers.filter(p => p.team === game.awayTeam).sort((a, b) => b.pa - a.pa);
        const homePitchers = gamePitchers.filter(p => p.team === game.homeTeam).sort((a, b) => b.outs - a.outs);
        const awayPitchers = gamePitchers.filter(p => p.team === game.awayTeam).sort((a, b) => b.outs - a.outs);
        
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
        
        return { 
            homeHitters, awayHitters, homePitchers, awayPitchers,
            homeHittingTotals, awayHittingTotals
        };
    }, [game, playerGames, pitcherGames]);
    
    if (!game || !gameData) return null;
    
    const HitterRow = ({ player }) => (
        <tr className="hover:bg-gray-50">
            <td className="px-3 py-2">
                <PlayerLink playerId={player.playerId} name={player.name} />
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
    
    const PitcherRow = ({ pitcher }) => {
        const ip = `${Math.floor(pitcher.outs / 3)}.${pitcher.outs % 3}`;
        const decision = pitcher.wins ? 'W' : pitcher.losses ? 'L' : pitcher.saves ? 'SV' : '';
        
        return (
            <tr className="hover:bg-gray-50">
                <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                        <PlayerLink playerId={pitcher.playerId} name={pitcher.name} />
                        {decision && (
                            <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                                decision === 'W' ? 'bg-green-100 text-green-700' :
                                decision === 'L' ? 'bg-red-100 text-red-700' :
                                'bg-blue-100 text-blue-700'
                            }`}>
                                {decision}
                            </span>
                        )}
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
                        <thead className="bg-gray-50 border-b-2">
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
                        <thead className="bg-gray-50 border-b-2">
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
            <div className="p-6 bg-gray-50">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Away Pitchers */}
                    <div>
                        <h4 className="subsection-title font-bold mb-3">{game.awayTeam} Pitching</h4>
                        <div className="overflow-x-auto">
                            <table className="w-full small-text bg-white rounded">
                                <thead className="bg-gray-50 border-b-2">
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
                                <thead className="bg-gray-50 border-b-2">
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
                            <div key={pid} className="bg-gray-50 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-semibold body-text">{pd.name}</span>
                                    <span className="small-text text-gray-500">{pd.totalPitches} pitches</span>
                                </div>
                                <div className="grid grid-cols-3 gap-3 small-text mb-3">
                                    {pd.maxSpeed && (
                                        <div className="bg-white p-2 rounded text-center">
                                            <div className="text-gray-500">Max Velo</div>
                                            <div className="font-bold text-red-600">{pd.maxSpeed} mph</div>
                                        </div>
                                    )}
                                    {pd.avgSpeed && (
                                        <div className="bg-white p-2 rounded text-center">
                                            <div className="text-gray-500">Avg Velo</div>
                                            <div className="font-bold text-gray-900">{pd.avgSpeed} mph</div>
                                        </div>
                                    )}
                                    {pd.avgSpinRate && (
                                        <div className="bg-white p-2 rounded text-center">
                                            <div className="text-gray-500">Avg Spin</div>
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
                <div className="p-8 text-center text-gray-500 body-text">
                    Starting lineup data not available for this game
                </div>
            );
        }
        
        const LineupTable = ({ lineup, team }) => (
            <div>
                <h4 className="subsection-title font-bold mb-3">{team} Starting Lineup</h4>
                <div className="bg-white rounded-lg overflow-hidden">
                    <table className="w-full small-text">
                        <thead className="bg-gray-50 border-b-2">
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
                                            {player.jerseyNumber && <span className="text-xs text-gray-400">#{player.jerseyNumber}</span>}
                                        </div>
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                        <span className="px-2 py-1 bg-gray-100 rounded font-semibold">
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
        if (!game.substitutions || game.substitutions.length === 0) {
            return (
                <div className="p-8 text-center text-gray-500 body-text">
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
                    {game.substitutions.map((sub, idx) => (
                        <div key={`sub-${idx}-${sub.inning}-${sub.half}`} className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-blue-400 hover:shadow-md transition-all">
                            <div className="flex items-start gap-3">
                                <span className="text-2xl">{getSubIcon(sub.type)}</span>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-bold">
                                            {sub.half.toUpperCase()} {sub.inning}
                                        </span>
                                        <span className="body-text font-bold text-gray-700">
                                            {getSubLabel(sub.type)}
                                        </span>
                                    </div>
                                    <div className="body-text text-gray-800">
                                        {sub.playerIn && sub.playerOut ? (
                                            <>
                                                <span className="font-semibold text-green-600">{sub.playerIn}</span>
                                                {' '}replaces{' '}
                                                <span className="font-semibold text-red-600">{sub.playerOut}</span>
                                                {sub.position && <span className="text-gray-500"> at {sub.position}</span>}
                                            </>
                                        ) : (
                                            <span className="text-gray-600">{sub.text}</span>
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
                <div className="p-8 text-center text-gray-500 body-text">
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
                                                <div className="text-xs font-bold text-gray-500">
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
                                                    <span className="font-semibold text-gray-900">{play.batter}</span>
                                                    {' '}
                                                    <span className="text-gray-600">
                                                        {play.description}
                                                    </span>
                                                </div>
                                                <div className="small-text text-gray-500 mt-1">
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
            <div className="bg-white rounded-lg shadow-2xl w-full max-h-[90vh] flex flex-col overflow-hidden" style={{ maxWidth: 'min(72rem, 95vw)' }} onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className={`p-6 border-b ${game.gameType === 'spring' ? 'bg-gradient-to-r from-green-600 to-green-700' : 'bg-gradient-to-r from-blue-600 to-blue-700'} text-white flex-shrink-0`}>
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                            <h3 className="section-title font-bold">{game.awayTeam} @ {game.homeTeam}</h3>
                            {game.gameType === 'spring' && <span className="px-2 py-0.5 bg-white/20 text-white text-xs font-semibold rounded">Spring Training</span>}
                            {game.gameType === 'postseason' && <span className="px-2 py-0.5 bg-yellow-400/30 text-white text-xs font-semibold rounded">Postseason</span>}
                        </div>
                        <button onClick={onClose} className="text-white hover:text-gray-200 text-2xl leading-none">&times;</button>
                    </div>
                    <div className="flex items-center gap-4 body-text text-blue-100">
                        <span>{game.date}</span>
                        <span>•</span>
                        <span>{game.startTime}</span>
                        <span>•</span>
                        <span className="font-mono text-2xl text-white font-bold">{game.score}</span>
                    </div>
                    <div className="body-text text-blue-100 mt-2">
                        📍 {game.venue}
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
                            <h5 className="small-text font-bold mb-3 text-gray-700">📊 Line Score</h5>
                            <div className="overflow-x-auto">
                                <table className="w-full text-center small-text" style={{ tableLayout: 'fixed' }}>
                                    <thead className="bg-gray-50">
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
                            <h5 className="small-text font-bold mb-3 text-gray-700">👨‍⚖️ Umpires</h5>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                                {game.umpires.hp && (
                                    <div className="small-text">
                                        <span className="text-gray-500">HP:</span> <span className="font-medium">{game.umpires.hp}</span>
                                    </div>
                                )}
                                {game.umpires['1b'] && (
                                    <div className="small-text">
                                        <span className="text-gray-500">1B:</span> <span className="font-medium">{game.umpires['1b']}</span>
                                    </div>
                                )}
                                {game.umpires['2b'] && (
                                    <div className="small-text">
                                        <span className="text-gray-500">2B:</span> <span className="font-medium">{game.umpires['2b']}</span>
                                    </div>
                                )}
                                {game.umpires['3b'] && (
                                    <div className="small-text">
                                        <span className="text-gray-500">3B:</span> <span className="font-medium">{game.umpires['3b']}</span>
                                    </div>
                                )}
                                {game.umpires.lf && (
                                    <div className="small-text">
                                        <span className="text-gray-500">LF:</span> <span className="font-medium">{game.umpires.lf}</span>
                                    </div>
                                )}
                                {game.umpires.rf && (
                                    <div className="small-text">
                                        <span className="text-gray-500">RF:</span> <span className="font-medium">{game.umpires.rf}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Key Plays (Home Runs) */}
                    {game.keyPlays && game.keyPlays.length > 0 && (
                        <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
                            <h5 className="small-text font-bold mb-3 text-gray-700">⚾ Key Plays</h5>
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
                                            <div className="small-text text-gray-600">
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
                                <h5 className="small-text font-bold mb-3 text-gray-700">🏆 Milestones Achieved</h5>
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
                                                    <div className="body-text font-bold text-gray-900">{milestone.type}</div>
                                                    <div className="body-text text-gray-700 mt-1">{milestone.player}</div>
                                                    {milestone.detail && (
                                                        <div className="small-text text-gray-600 mt-1">{milestone.detail}</div>
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
                                                <div className="body-text text-gray-700 mt-1">{first.player_name}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
                
                {/* Tab Navigation */}
                <div className="border-b bg-gray-50 sticky top-0 z-10">
                    <div className="flex gap-1 px-6">
                        {['boxscore', 'lineups', 'substitutions', 'playbyplay', 'context'].map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-4 sm:px-6 py-3 body-text font-semibold transition-all whitespace-nowrap ${
                                    activeTab === tab
                                        ? 'bg-white text-blue-600 border-b-4 border-blue-600'
                                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
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
                            {(careerFirsts?.length || 0) === 0 && (allTimePassings?.length || 0) === 0 && (badges?.length || 0) === 0 && (
                                <div className="text-center py-8 text-gray-500 body-text">No special context for this game</div>
                            )}

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
                                                    {first.opponent && <div className="small-text text-gray-600">vs {first.opponent}</div>}
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
                                                    <div className="small-text text-gray-600">
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
                <div className="p-4 border-t bg-gray-50 flex justify-between items-center flex-shrink-0">
                    <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                    <button onClick={onClose} className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 body-text font-medium">
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

const PlayerTimeline = ({ playerId, playerName, playerGames, onGameClick }) => {
    const [activeView, setActiveView] = useState('timeline');
    const [sortKey, setSortKey] = useState('dateSort');
    const [sortDir, setSortDir] = useState('desc');

    // Get all games for this player
    const gamesForPlayer = useMemo(() => {
        return playerGames.filter(g => g.playerId === playerId).sort((a, b) => b.dateSort.localeCompare(a.dateSort));
    }, [playerId, playerGames]);

    const timelineData = useMemo(() => {
        if (gamesForPlayer.length === 0) return [];

        // Group by year and game type (separate spring training)
        const byYearType = {};
        gamesForPlayer.forEach(game => {
            const year = game.dateSort.substring(0, 4);
            const isSpring = game.gameType === 'spring' || game.gameType === 'exhibition';
            const key = isSpring ? `${year}_spring` : year;
            if (!byYearType[key]) {
                byYearType[key] = { year, isSpring, games: [] };
            }
            byYearType[key].games.push(game);
        });

        // Aggregate stats per year/type
        const yearlyStats = Object.values(byYearType).map(({ year, isSpring, games }) => {
            const aggregated = aggregateHitterStats(games)[0] || {};
            return { year, isSpring, ...aggregated };
        }).sort((a, b) => a.year !== b.year ? a.year - b.year : (a.isSpring ? -1 : 0) - (b.isSpring ? -1 : 0));

        return yearlyStats;
    }, [gamesForPlayer]);

    // Sorted game log
    const sortedGameLog = useMemo(() => {
        return [...gamesForPlayer].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal || '').localeCompare(String(bVal || ''));
            return sortDir === 'asc' ? result : -result;
        });
    }, [gamesForPlayer, sortKey, sortDir]);

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    if (gamesForPlayer.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="subsection-title font-bold mb-4">📊 Player Stats</h3>
                <p className="body-text text-gray-500 text-center py-8">No games found for this player</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <h3 className="subsection-title font-bold">📊 {playerName}</h3>
                <div className="flex rounded-lg overflow-hidden border">
                    <button
                        onClick={() => setActiveView('timeline')}
                        className={`px-4 py-2 text-sm font-medium transition-colors ${
                            activeView === 'timeline' ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                        }`}
                    >
                        📅 Timeline
                    </button>
                    <button
                        onClick={() => setActiveView('gamelog')}
                        className={`px-4 py-2 text-sm font-medium transition-colors ${
                            activeView === 'gamelog' ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                        }`}
                    >
                        📋 Game Log
                    </button>
                </div>
            </div>

            {/* Game Log View */}
            {activeView === 'gamelog' && (
                <div>
                    <div className="text-sm text-gray-500 mb-3">{gamesForPlayer.length} games</div>
                    <div className="overflow-x-auto border rounded-lg" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 sticky top-0">
                                <tr>
                                    {[
                                        { key: 'dateSort', label: 'Date' },
                                        { key: 'team', label: 'Team' },
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
                                        <th
                                            key={col.key}
                                            onClick={() => handleSort(col.key)}
                                            className="px-3 py-2 text-left font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 whitespace-nowrap"
                                        >
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
                                            <td className="px-3 py-2 whitespace-nowrap font-medium">{game.date}</td>
                                            <td className="px-3 py-2">{game.team}</td>
                                            <td className="px-3 py-2">{game.opponent}</td>
                                            <td className="px-3 py-2">{game.ab}</td>
                                            <td className={`px-3 py-2 ${isMultiHit ? 'font-bold text-green-600' : ''}`}>{game.h}</td>
                                            <td className="px-3 py-2">{game.r}</td>
                                            <td className="px-3 py-2">{game.rbi}</td>
                                            <td className={`px-3 py-2 ${isHR ? 'font-bold text-orange-600' : ''}`}>{game.hr || 0}</td>
                                            <td className="px-3 py-2">{game.bb}</td>
                                            <td className="px-3 py-2">{game.so}</td>
                                            <td className="px-3 py-2">{game.sb || 0}</td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                        <span className="px-2 py-1 bg-orange-50 rounded">HR games highlighted orange</span>
                        <span className="px-2 py-1 bg-green-50 rounded">Multi-hit games highlighted green</span>
                    </div>
                </div>
            )}

            {/* Timeline View */}
            {activeView === 'timeline' && (
                <div>
            
            {/* Career summary stats (regular season only) */}
            {(() => {
                const regSeasons = timelineData.filter(s => !s.isSpring);
                const springSeasons = timelineData.filter(s => s.isSpring);
                const totals = regSeasons.reduce((acc, season) => ({
                    games: acc.games + (season.games || 0),
                    pa: acc.pa + (season.pa || 0),
                    hr: acc.hr + (season.hr || 0),
                    rbi: acc.rbi + (season.rbi || 0),
                    h: acc.h + (season.h || 0)
                }), { games: 0, pa: 0, hr: 0, rbi: 0, h: 0 });
                const springTotals = springSeasons.reduce((acc, season) => ({
                    games: acc.games + (season.games || 0),
                    pa: acc.pa + (season.pa || 0),
                    h: acc.h + (season.h || 0)
                }), { games: 0, pa: 0, h: 0 });

                return (
                    <>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4 p-4 bg-blue-50 rounded-lg">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{totals.games}</div>
                                <div className="small-text text-gray-600">Games</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{totals.pa}</div>
                                <div className="small-text text-gray-600">PA</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{totals.h}</div>
                                <div className="small-text text-gray-600">Hits</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{totals.hr}</div>
                                <div className="small-text text-gray-600">HR</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{totals.rbi}</div>
                                <div className="small-text text-gray-600">RBI</div>
                            </div>
                        </div>
                        {springTotals.games > 0 && (
                            <div className="mb-6 px-4 py-2 bg-green-50 rounded-lg text-sm text-green-700">
                                🌴 Spring Training: {springTotals.games} games, {springTotals.pa} PA, {springTotals.h} H
                            </div>
                        )}
                    </>
                );
            })()}
            
            {/* Year-by-year timeline */}
            <div className="space-y-4">
                {timelineData.map((season) => (
                    <div key={`season-${season.year}${season.isSpring ? '-spring' : ''}`} className="relative pl-8 pb-4 border-l-2 border-blue-200 last:border-l-0">
                        <div className={`absolute left-0 top-0 -ml-2.5 w-5 h-5 ${season.isSpring ? 'bg-green-500' : 'bg-blue-600'} rounded-full border-2 border-white`}></div>
                        <div className={`${season.isSpring ? 'bg-green-50 hover:bg-green-100' : 'bg-gray-50 hover:bg-blue-50'} rounded-lg p-4 transition-colors`}>
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <span className={`text-2xl font-bold ${season.isSpring ? 'text-green-600' : 'text-blue-600'}`}>{season.year}</span>
                                    {season.isSpring && <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded">Spring Training</span>}
                                    <span className="ml-3 body-text text-gray-600">{season.team || 'Various Teams'}</span>
                                </div>
                                <span className="body-text text-gray-600 font-semibold">{season.games} games</span>
                            </div>
                            
                            {/* Stats grid */}
                            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 small-text">
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">PA</div>
                                    <div className="font-bold text-gray-900">{season.pa}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">AVG</div>
                                    <div className="font-bold text-gray-900">{season.avg}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">HR</div>
                                    <div className="font-bold text-orange-600">{season.hr}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">RBI</div>
                                    <div className="font-bold text-gray-900">{season.rbi}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">H</div>
                                    <div className="font-bold text-gray-900">{season.h}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">R</div>
                                    <div className="font-bold text-gray-900">{season.r}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">OBP</div>
                                    <div className="font-bold text-blue-600">{season.obp}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">OPS</div>
                                    <div className="font-bold text-purple-600">{season.ops}</div>
                                </div>
                            </div>
                            
                            {/* Notable achievements */}
                            <div className="mt-3 flex flex-wrap gap-2">
                                {season.hr >= 5 && (
                                    <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-semibold">
                                        💥 {season.hr} HR
                                    </span>
                                )}
                                {parseFloat(season.avg) >= 0.300 && (
                                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold">
                                        🎯 .300+ AVG
                                    </span>
                                )}
                                {parseFloat(season.ops) >= 0.800 && (
                                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-semibold">
                                        ⭐ .800+ OPS
                                    </span>
                                )}
                                {season.sb >= 5 && (
                                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                                        🏃 {season.sb} SB
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
                </div>
            )}
        </div>
    );
};

const PitcherTimeline = ({ playerId, playerName, pitcherGames, onGameClick }) => {
    const [activeView, setActiveView] = useState('timeline');
    const [sortKey, setSortKey] = useState('dateSort');
    const [sortDir, setSortDir] = useState('desc');

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

        // Group by year and game type (separate spring training)
        const byYearType = {};
        gamesForPitcher.forEach(game => {
            const year = game.dateSort.substring(0, 4);
            const isSpring = game.gameType === 'spring' || game.gameType === 'exhibition';
            const key = isSpring ? `${year}_spring` : year;
            if (!byYearType[key]) {
                byYearType[key] = { year, isSpring, games: [] };
            }
            byYearType[key].games.push(game);
        });

        // Aggregate stats per year/type
        const yearlyStats = Object.values(byYearType).map(({ year, isSpring, games }) => {
            const aggregated = aggregatePitcherStats(games)[0] || {};
            return { year, isSpring, ...aggregated };
        }).sort((a, b) => a.year !== b.year ? a.year - b.year : (a.isSpring ? -1 : 0) - (b.isSpring ? -1 : 0));

        return yearlyStats;
    }, [gamesForPitcher]);

    // Sorted game log
    const sortedGameLog = useMemo(() => {
        return [...gamesForPitcher].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal || '').localeCompare(String(bVal || ''));
            return sortDir === 'asc' ? result : -result;
        });
    }, [gamesForPitcher, sortKey, sortDir]);

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    if (gamesForPitcher.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="subsection-title font-bold mb-4">📊 Pitcher Stats</h3>
                <p className="body-text text-gray-500 text-center py-8">No games found for this pitcher</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <h3 className="subsection-title font-bold">📊 {playerName}</h3>
                <div className="flex rounded-lg overflow-hidden border">
                    <button
                        onClick={() => setActiveView('timeline')}
                        className={`px-4 py-2 text-sm font-medium transition-colors ${
                            activeView === 'timeline' ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                        }`}
                    >
                        📅 Timeline
                    </button>
                    <button
                        onClick={() => setActiveView('gamelog')}
                        className={`px-4 py-2 text-sm font-medium transition-colors ${
                            activeView === 'gamelog' ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                        }`}
                    >
                        📋 Game Log
                    </button>
                </div>
            </div>

            {/* Game Log View */}
            {activeView === 'gamelog' && (
                <div>
                    <div className="text-sm text-gray-500 mb-3">{gamesForPitcher.length} games</div>
                    <div className="overflow-x-auto border rounded-lg" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 sticky top-0">
                                <tr>
                                    {[
                                        { key: 'dateSort', label: 'Date' },
                                        { key: 'team', label: 'Team' },
                                        { key: 'opponent', label: 'vs' },
                                        { key: 'ip', label: 'IP' },
                                        { key: 'h', label: 'H' },
                                        { key: 'r', label: 'R' },
                                        { key: 'er', label: 'ER' },
                                        { key: 'bb', label: 'BB' },
                                        { key: 'so', label: 'SO' },
                                        { key: 'decision', label: 'Dec' },
                                    ].map(col => (
                                        <th
                                            key={col.key}
                                            onClick={() => handleSort(col.key)}
                                            className="px-3 py-2 text-left font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 whitespace-nowrap"
                                        >
                                            {col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {sortedGameLog.map((game) => {
                                    const isWin = game.decision === 'W';
                                    const isQS = parseFloat(game.ip) >= 6 && game.er <= 3;
                                    const isHighSO = game.so >= 8;
                                    return (
                                        <tr key={`${game.date}-${game.opponent}-${game.team}`} className={`hover:bg-blue-50 cursor-pointer ${isWin ? 'bg-green-50' : ''} ${isQS ? 'bg-blue-50' : ''}`} onClick={() => onGameClick && onGameClick(game.gameId)}>
                                            <td className="px-3 py-2 whitespace-nowrap font-medium">{game.date}</td>
                                            <td className="px-3 py-2">{game.team}</td>
                                            <td className="px-3 py-2">{game.opponent}</td>
                                            <td className="px-3 py-2 font-medium">{game.ip}</td>
                                            <td className="px-3 py-2">{game.h}</td>
                                            <td className="px-3 py-2">{game.r}</td>
                                            <td className="px-3 py-2">{game.er}</td>
                                            <td className="px-3 py-2">{game.bb}</td>
                                            <td className={`px-3 py-2 ${isHighSO ? 'font-bold text-orange-600' : ''}`}>{game.so}</td>
                                            <td className={`px-3 py-2 font-bold ${isWin ? 'text-green-600' : game.decision === 'L' ? 'text-red-600' : game.decision === 'S' ? 'text-blue-600' : ''}`}>
                                                {game.decision || '-'}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                        <span className="px-2 py-1 bg-green-50 rounded">Wins highlighted green</span>
                        <span className="px-2 py-1 bg-blue-50 rounded">Quality starts highlighted blue</span>
                    </div>
                </div>
            )}

            {/* Timeline View */}
            {activeView === 'timeline' && (
                <div>
            {/* Career summary stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6 p-4 bg-purple-50 rounded-lg">
                {(() => {
                    const totals = timelineData.reduce((acc, season) => ({
                        games: acc.games + (season.games || 0),
                        wins: acc.wins + (season.wins || 0),
                        losses: acc.losses + (season.losses || 0),
                        saves: acc.saves + (season.saves || 0),
                        outs: acc.outs + (season.outs || 0),
                        so: acc.so + (season.so || 0)
                    }), { games: 0, wins: 0, losses: 0, saves: 0, outs: 0, so: 0 });
                    
                    const ip = `${Math.floor(totals.outs / 3)}.${totals.outs % 3}`;
                    
                    return (
                        <>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{totals.games}</div>
                                <div className="small-text text-gray-600">Games</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{ip}</div>
                                <div className="small-text text-gray-600">IP</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{totals.wins}-{totals.losses}</div>
                                <div className="small-text text-gray-600">W-L</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{totals.saves}</div>
                                <div className="small-text text-gray-600">Saves</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{totals.so}</div>
                                <div className="small-text text-gray-600">SO</div>
                            </div>
                        </>
                    );
                })()}
            </div>
            
            {/* Year-by-year timeline */}
            <div className="space-y-4">
                {timelineData.map((season) => (
                    <div key={`season-${season.year}${season.isSpring ? '-spring' : ''}`} className="relative pl-8 pb-4 border-l-2 border-purple-200 last:border-l-0">
                        <div className={`absolute left-0 top-0 -ml-2.5 w-5 h-5 ${season.isSpring ? 'bg-green-500' : 'bg-purple-600'} rounded-full border-2 border-white`}></div>
                        <div className={`${season.isSpring ? 'bg-green-50 hover:bg-green-100' : 'bg-gray-50 hover:bg-purple-50'} rounded-lg p-4 transition-colors`}>
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <span className={`text-2xl font-bold ${season.isSpring ? 'text-green-600' : 'text-purple-600'}`}>{season.year}</span>
                                    {season.isSpring && <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded">Spring Training</span>}
                                    <span className="ml-3 body-text text-gray-600">{season.team || 'Various Teams'}</span>
                                </div>
                                <span className="body-text text-gray-600 font-semibold">{season.games} games</span>
                            </div>
                            
                            {/* Stats grid */}
                            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 small-text">
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">GS</div>
                                    <div className="font-bold text-gray-900">{season.gameStarts || 0}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">IP</div>
                                    <div className="font-bold text-gray-900">{season.ip}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">W-L</div>
                                    <div className="font-bold text-gray-900">{season.wins}-{season.losses}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">ERA</div>
                                    <div className="font-bold text-blue-600">{season.era}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">WHIP</div>
                                    <div className="font-bold text-purple-600">{season.whip}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">SO</div>
                                    <div className="font-bold text-orange-600">{season.so}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">H</div>
                                    <div className="font-bold text-gray-900">{season.h}</div>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <div className="text-gray-500">SV</div>
                                    <div className="font-bold text-green-600">{season.saves || 0}</div>
                                </div>
                            </div>
                            
                            {/* Notable achievements */}
                            <div className="mt-3 flex flex-wrap gap-2">
                                {season.wins >= 3 && (
                                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold">
                                        🏆 {season.wins} Wins
                                    </span>
                                )}
                                {season.saves >= 3 && (
                                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                                        💾 {season.saves} Saves
                                    </span>
                                )}
                                {season.so >= 20 && (
                                    <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-semibold">
                                        🔥 {season.so} SO
                                    </span>
                                )}
                                {season.era !== 'N/A' && parseFloat(season.era) <= 3.00 && (
                                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-semibold">
                                        ⭐ {season.era} ERA
                                    </span>
                                )}
                                {season.whip !== 'N/A' && parseFloat(season.whip) <= 1.20 && (
                                    <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-semibold">
                                        🎯 {season.whip} WHIP
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
                </div>
            )}
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
        if (gameCount === 0) return 'bg-gray-50 border-gray-200';
        const intensity = Math.min(gameCount / maxGamesOnDate, 1);
        if (intensity <= 0.25) return 'bg-blue-100 border-blue-200';
        if (intensity <= 0.5) return 'bg-blue-200 border-blue-300';
        if (intensity <= 0.75) return 'bg-blue-400 border-blue-500';
        return 'bg-blue-600 border-blue-700';
    };

    const getTextColor = (gameCount) => {
        if (gameCount === 0) return 'text-gray-700';
        const intensity = Math.min(gameCount / maxGamesOnDate, 1);
        return intensity > 0.5 ? 'text-white' : 'text-gray-700';
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
            <div className="bg-white rounded-lg border border-gray-200 p-2">
                <div className="text-center mb-2">
                    <h3 className="font-bold text-gray-800" style={{ fontSize: '13px' }}>{monthNames[monthIndices.indexOf(monthIndex)]}</h3>
                    <span className="text-gray-500" style={{ fontSize: '11px' }}>{gamesInMonth} game{gamesInMonth !== 1 ? 's' : ''}</span>
                </div>
                <div className="grid grid-cols-7 gap-0.5">
                    {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
                        <div key={`day-header-${i}`} className="text-center text-gray-500 font-medium" style={{ fontSize: '9px' }}>{day}</div>
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
            <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                    <div className="flex justify-between items-center">
                        <div>
                            <h2 className="section-title font-bold">📅 Season Calendar Heatmap</h2>
                            <p className="small-text text-gray-500 mt-1">
                                {totalStats.totalGames} games • {totalStats.uniqueDates} unique dates • Click any date with games for details
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="small-text text-gray-600">Legend:</span>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-gray-50 border border-gray-200 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-gray-500">0</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-gray-500">1</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-400 border border-blue-500 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-gray-500">2-3</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-600 border border-blue-700 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-gray-500">4+</span>
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
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                            <h3 className="section-title font-bold">{monthNames[monthIndices.indexOf(selectedMonthForModal)]} {selectedDate.day} • All Years</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedDate.games.length} game{selectedDate.games.length !== 1 ? 's' : ''} attended</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            <div className="divide-y">
                                {selectedDate.games.sort((a, b) => new Date(b.date) - new Date(a.date)).map((game) => (
                                    <div key={game.gameId} className="p-4 hover:bg-blue-50 transition-colors">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-3">
                                                <span className="body-text font-bold text-blue-600">{game.date}</span>
                                                <span className="small-text text-gray-500">{game.startTime}</span>
                                            </div>
                                            <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                                        </div>
                                        <div className="flex items-center gap-4 flex-wrap">
                                            <div className="flex items-center gap-2">
                                                <span className="body-text font-semibold w-12 text-right">{game.awayTeam}</span>
                                                <span className="body-text text-gray-500">@</span>
                                                <span className="body-text font-semibold w-12">{game.homeTeam}</span>
                                            </div>
                                            <span className="font-mono body-text bg-gray-100 px-3 py-1 rounded font-bold">{game.score}</span>
                                            <span className="body-text text-gray-600">{game.venue}</span>
                                            {game.attendance > 0 && <span className="small-text text-gray-500">👥 {game.attendance.toLocaleString()}</span>}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="p-4 border-t bg-gray-50">
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
        return <div className="bg-white rounded-lg shadow p-6 body-text">No matchup data available</div>;
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
        const aliases = { 'ATH': 'OAK', 'FLA': 'MIA' };
        return aliases[code] || code;
    };

    const handleCellClick = (team, opponent, count) => {
        if (count === 'X' || count === 0) return;
        const matchupGames = games.filter(game => {
            const home = normalizeCode(game.homeTeam);
            const away = normalizeCode(game.awayTeam);
            return (home === team && away === opponent) ||
                   (home === opponent && away === team);
        }).sort((a, b) => new Date(b.date) - new Date(a.date));
        setSelectedMatchup({ team, opponent, games: matchupGames, count });
        setShowModal(true);
    };

    return (
        <>
            <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h2 className="section-title font-bold">🎯 Team Matchup Matrix</h2>
                            <p className="body-text text-gray-500 mt-1">Click any cell to see games between those teams</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="text-center px-4 py-2 bg-blue-50 rounded-lg">
                                <div className="text-xl font-bold text-blue-600">{uniqueMatchupsSeen}/{totalPossibleMatchups}</div>
                                <div className="text-xs text-gray-500">Matchups Seen</div>
                            </div>
                            <div className="text-center px-4 py-2 bg-green-50 rounded-lg">
                                <div className="text-xl font-bold text-green-600">{completionPercent}%</div>
                                <div className="text-xs text-gray-500">Complete</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="p-2">
                    <table className="w-full border-collapse" style={{ tableLayout: 'fixed' }}>
                        <thead>
                            <tr>
                                <th className="border bg-gray-100 font-bold" style={{ fontSize: '9px', padding: '2px', width: '28px' }}></th>
                                {teams.map(team => (
                                    <th key={team} className="border bg-gray-50 font-medium" style={{ fontSize: '8px', padding: '1px', width: '24px' }}>{team}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {matrix.map((row) => (
                                <tr key={row.team}>
                                    <td className="border font-bold bg-gray-100" style={{ fontSize: '8px', padding: '1px' }}>{row.team}</td>
                                    {teams.map(opponent => {
                                        const value = row[opponent];
                                        const isX = value === 'X';
                                        const hasGames = !isX && value > 0;
                                        return (
                                            <td key={opponent} onClick={() => hasGames && handleCellClick(row.team, opponent, value)} className={`border text-center ${isX ? 'bg-gray-300' : hasGames ? 'bg-blue-100 font-bold cursor-pointer hover:bg-blue-300' : 'bg-white'}`} style={{ fontSize: '9px', padding: '1px' }}>
                                                {isX ? '' : (value || '')}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="p-2 border-t bg-gray-50">
                    <div className="flex items-center gap-4 justify-center text-gray-600" style={{ fontSize: '10px' }}>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-gray-300 border rounded"></div><span>Same team</span></div>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-white border rounded"></div><span>No games</span></div>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-blue-100 border rounded"></div><span>Has games (click)</span></div>
                    </div>
                </div>
            </div>
            {showModal && selectedMatchup && (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
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
                                            <div key={game.gameId} className="p-4 hover:bg-blue-50 transition-colors">
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-3">
                                                        <span className="body-text font-bold text-blue-600">{game.date}</span>
                                                        <span className="small-text text-gray-500">{game.startTime}</span>
                                                    </div>
                                                    <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                                                </div>
                                                <div className="flex items-center gap-4 flex-wrap">
                                                    <div className="flex items-center gap-2">
                                                        <span className={`body-text w-12 text-right ${isHomeGame ? 'font-normal' : 'font-bold'}`}>{game.awayTeam}</span>
                                                        <span className="body-text text-gray-500">@</span>
                                                        <span className={`body-text w-12 ${isHomeGame ? 'font-bold' : 'font-normal'}`}>{game.homeTeam}</span>
                                                    </div>
                                                    <span className="font-mono body-text bg-gray-100 px-3 py-1 rounded font-bold">{game.score}</span>
                                                    <span className="body-text text-gray-600">{game.venue}</span>
                                                    {game.attendance > 0 && <span className="small-text text-gray-500">👥 {game.attendance.toLocaleString()}</span>}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="p-8 text-center body-text text-gray-500">No games found between these teams</div>
                            )}
                        </div>
                        <div className="p-4 border-t bg-gray-50">
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
        <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b bg-gradient-to-r from-orange-500 to-orange-600 text-white">
                <h3 className="font-bold text-lg">🗺️ Orioles Stadium Quest</h3>
                <p className="text-sm text-orange-100 mt-1">See the Orioles at all 30 MLB stadiums</p>
            </div>
            <div ref={mapRef} style={{ height: '400px', width: '100%' }}></div>
            <div className="p-4 bg-orange-50 border-t">
                <div className="grid grid-cols-5 gap-4 text-center">
                    <div>
                        <div className="text-2xl font-bold text-orange-600">{stats.visitedCount}</div>
                        <div className="text-xs text-gray-600">Current</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-purple-600">{stats.historicalVisited}</div>
                        <div className="text-xs text-gray-600">Historical</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-gray-500">{stats.remaining}</div>
                        <div className="text-xs text-gray-600">Remaining</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-orange-600">{stats.percent}%</div>
                        <div className="text-xs text-gray-600">Complete</div>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1">
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                            <span className="text-xs text-gray-600">Current</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                            <span className="text-xs text-gray-600">Historical</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                            <span className="text-xs text-gray-600">Not yet</span>
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
        const match1 = scoreStr.match(/(\\w+)\\s+(\\d+)\\s*-\\s*(\\d+)\\s+(\\w+)/);
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
        const match2 = scoreStr.match(/(\\d+)\\s*-\\s*(\\d+)/);
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
        if (code === 'ATH' || code === 'OAK') return 'OAK';
        return code;
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
                <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                        <h3 className="font-bold text-lg">📈 Streaks</h3>
                    </div>
                    <div className="p-4">
                        <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="text-center p-3 bg-gray-50 rounded-lg">
                                <div className={`text-2xl font-bold ${streaksData.currentStreak.type === 'W' ? 'text-green-600' : 'text-red-600'}`}>
                                    {streaksData.currentStreak.type}{streaksData.currentStreak.count}
                                </div>
                                <div className="text-xs text-gray-500">Current</div>
                            </div>
                            <div className="text-center p-3 bg-green-50 rounded-lg">
                                <div className="text-2xl font-bold text-green-600">W{streaksData.longestWinStreak}</div>
                                <div className="text-xs text-gray-500">Longest Win Streak</div>
                            </div>
                            <div className="text-center p-3 bg-red-50 rounded-lg">
                                <div className="text-2xl font-bold text-red-600">L{streaksData.longestLossStreak}</div>
                                <div className="text-xs text-gray-500">Longest Loss Streak</div>
                            </div>
                        </div>
                        <h4 className="font-semibold text-sm text-gray-600 mb-2">Last 10 Games</h4>
                        <div className="flex gap-1 flex-wrap">
                            {streaksData.recentGames.map((g) => (
                                <div key={g.gameId || `${g.date}-${g.opponent}`} className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold text-white ${g.result === 'W' ? 'bg-green-500' : 'bg-red-500'}`} title={`${g.date}: ${g.result} ${g.score} vs ${g.opponent}`}>
                                    {g.result}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow">
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
                                        <div className="flex-1 bg-gray-200 rounded-full h-4 overflow-hidden">
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
                <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-t-lg">
                        <h3 className="font-bold text-lg">⚔️ vs AL East</h3>
                    </div>
                    <div className="p-4">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-gray-500 border-b">
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
                                    <tr key={o.team} className="border-b last:border-0 hover:bg-gray-50">
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

                <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                        <h3 className="font-bold text-lg">🏟️ vs Other Teams</h3>
                    </div>
                    <div className="p-4 max-h-64 overflow-y-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-gray-500 border-b">
                                    <th className="pb-2">Team</th>
                                    <th className="pb-2 text-center">G</th>
                                    <th className="pb-2 text-center">Record</th>
                                    <th className="pb-2 text-center">Diff</th>
                                </tr>
                            </thead>
                            <tbody>
                                {otherOpponents.map(o => (
                                    <tr key={o.team} className="border-b last:border-0 hover:bg-gray-50">
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
        <div className="bg-white rounded-lg shadow overflow-hidden mt-4">
            <div className="p-3 border-b bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                <h4 className="font-bold">🗺️ Stadiums with {companion.name}</h4>
            </div>
            <div ref={mapRef} style={{ height: '300px', width: '100%' }}></div>
            <div className="p-3 bg-gray-50 border-t">
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3 flex-wrap">
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-500"></span>
                            <span className="text-gray-600 text-xs">Visited ({stats.visitedCount - stats.oriolesCount})</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                            <span className="text-gray-600 text-xs">O's ({stats.oriolesCount})</span>
                        </div>
                        {stats.historicalVisited > 0 && (
                            <div className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                                <span className="text-gray-600 text-xs">Historical ({stats.historicalVisited})</span>
                            </div>
                        )}
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                            <span className="text-gray-600 text-xs">Not yet ({stats.remaining})</span>
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
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="section-title font-bold mb-4">👥 Games With Companions</h2>
                <div className="text-center py-8">
                    <p className="body-text text-gray-600 mb-4">No companion data found.</p>
                    <div className="bg-gray-50 rounded-lg p-4 max-w-lg mx-auto text-left">
                        <p className="font-semibold text-gray-800 mb-2">To track games with companions:</p>
                        <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                            <li>Edit <code className="bg-gray-200 px-1 rounded">companions.csv</code> in your MLB Game Tracker folder</li>
                            <li>Add rows with format: <code className="bg-gray-200 px-1 rounded">GameID,Companion1|Companion2</code></li>
                            <li>Example: <code className="bg-gray-200 px-1 rounded">BAL202505090,Dad</code></li>
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
            <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                    <h2 className="section-title font-bold">👥 Games With Companions</h2>
                    <p className="body-text text-gray-500 mt-1">Track who you've attended games with</p>
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
                                        <span className="text-gray-600">Stadiums visited:</span>
                                        <span className="font-semibold">{companion.uniqueStadiums}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Orioles games:</span>
                                        <span className="font-semibold text-orange-600">{companion.oriolesGames}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">O's stadiums:</span>
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
                <div key={companion.name} className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
                        <h3 className="font-bold text-lg">📊 {companion.name} - Detailed Stats</h3>
                    </div>
                    <div className="p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Stadiums visited */}
                            <div>
                                <h4 className="font-semibold text-gray-800 mb-2">🏟️ Stadiums Visited ({companion.uniqueStadiums})</h4>
                                <div className="flex flex-wrap gap-1">
                                    {companion.stadiumsList.map(stadium => (
                                        <span key={stadium} className="px-2 py-1 bg-gray-100 rounded text-xs">{stadium}</span>
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
                            <h4 className="font-semibold text-gray-800 mb-2">📋 Recent Games (last 5)</h4>
                            <div className="space-y-1">
                                {companion.games.slice(0, 5).map(game => {
                                    const formatDate = (dateStr) => {
                                        if (!dateStr) return '';
                                        const d = new Date(dateStr.split(' ')[0]);
                                        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                                    };
                                    return (
                                        <div key={game.gameId} className="grid grid-cols-3 text-sm bg-gray-50 px-3 py-2 rounded">
                                            <span className="font-medium">{formatDate(game.date)}</span>
                                            <span className="text-center">{game.awayTeam} @ {game.homeTeam}</span>
                                            <span className="text-gray-500 text-right">{game.venue}</span>
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
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                            <h3 className="section-title font-bold">Games with {selectedCompanion.name}</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedCompanion.totalGames} total games</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            <div className="divide-y">
                                {selectedCompanion.games.map((game) => (
                                    <div key={game.gameId || `${game.date}-${game.awayTeam}-${game.homeTeam}`} className="p-4 hover:bg-blue-50 transition-colors">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <span className="font-bold text-blue-600">{(game.date || '').split(' ')[0]}</span>
                                                <span className="font-semibold">{game.awayTeam} @ {game.homeTeam}</span>
                                            </div>
                                            <span className="text-gray-600">{game.venue}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="p-4 border-t bg-gray-50">
                            <button onClick={() => setShowGames(false)} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium w-full">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};


const DynamicPlayerTable = ({ allPlayers, playerGames }) => {
    const [search, setSearch] = useState('');
    const [sortKey, setSortKey] = useState('pa');
    const [sortDir, setSortDir] = useState('desc');
    const [activeFilter, setActiveFilter] = useState('all');
    const [gameTypeFilter, setGameTypeFilter] = useState('regular');

    // Check for pending player selection (from College tab)
    useEffect(() => {
        if (window._pendingPlayerSelect) {
            setSelectedPlayer(window._pendingPlayerSelect);
            window._pendingPlayerSelect = null;
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
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="section-title font-bold">👤 Hitter Statistics {gameTypeFilter !== 'all' && <span className="small-text text-green-600">({gameTypeLabels[gameTypeFilter]})</span>} {useFiltered && <span className="small-text text-blue-600">(Date Filtered)</span>}</h2>
                    <div className="flex items-center gap-2">
                        <span className="body-text text-gray-500">{sorted.length} players</span>
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
                    {(startDate || endDate) && <button onClick={() => { setStartDate(''); setEndDate(''); }} className="px-3 py-2 body-text text-gray-600 hover:text-gray-900">Clear Dates</button>}
                    <select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)} className="px-4 py-2 body-text border rounded-lg">
                        <option value="all">All Teams</option>
                        {filterValues.map(val => <option key={val} value={val}>{val}</option>)}
                    </select>
                </div>
                {useFiltered && <div className="bg-yellow-50 border border-yellow-200 rounded p-3"><p className="body-text text-yellow-900">⚡ Stats recalculated for selected date range</p></div>}
            </div>
            <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="w-full">
                    <thead className="bg-gray-50 sticky top-0">
                        <tr>{columns.map(col => <th key={col.key} onClick={() => handleSort(col.key)} className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100">{col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}</th>)}</tr>
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
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl max-w-[95vw] w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-purple-700 text-white">
                            <h3 className="section-title font-bold">Career Timeline</h3>
                            <button onClick={() => setSelectedPlayer(null)} className="text-white hover:text-gray-200 text-2xl leading-none">&times;</button>
                        </div>
                        <div className="overflow-y-auto p-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>
                            <PlayerTimeline
                                playerId={selectedPlayer.id}
                                playerName={selectedPlayer.name}
                                playerGames={playerGames}
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

const DynamicPitcherTable = ({ allPitchers, pitcherGames }) => {
    const [search, setSearch] = useState('');
    const [sortKey, setSortKey] = useState('ip');
    const [sortDir, setSortDir] = useState('desc');
    const [activeFilter, setActiveFilter] = useState('all');
    const [gameTypeFilter, setGameTypeFilter] = useState('regular');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [useFiltered, setUseFiltered] = useState(false);
    const [selectedPitcher, setSelectedPitcher] = useState(null);

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
        { key: 'ip', label: 'IP' }, { key: 'era', label: 'ERA' }, { key: 'whip', label: 'WHIP' },
        { key: 'so', label: 'SO' }, { key: 'bb', label: 'BB' },
        { key: 'maxSpeed', label: 'Max Velo', render: (v) => v ? `${v}` : '-' },
        { key: 'avgSpeed', label: 'Avg Velo', render: (v) => v ? `${v}` : '-' },
        { key: 'avgSpinRate', label: 'Avg Spin', render: (v) => v ? `${v}` : '-' },
    ];

    const gameTypeLabels = { all: 'All Games', spring: 'Spring Training', regular: 'Regular Season', postseason: 'Postseason' };

    return (
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="section-title font-bold">⚾ Pitcher Statistics {gameTypeFilter !== 'all' && <span className="small-text text-green-600">({gameTypeLabels[gameTypeFilter]})</span>} {useFiltered && <span className="small-text text-blue-600">(Date Filtered)</span>}</h2>
                    <div className="flex items-center gap-2">
                        <span className="body-text text-gray-500">{sorted.length} pitchers</span>
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
                    {(startDate || endDate) && <button onClick={() => { setStartDate(''); setEndDate(''); }} className="px-3 py-2 body-text text-gray-600 hover:text-gray-900">Clear Dates</button>}
                    <select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)} className="px-4 py-2 body-text border rounded-lg">
                        <option value="all">All Teams</option>
                        {filterValues.map(val => <option key={val} value={val}>{val}</option>)}
                    </select>
                </div>
                {useFiltered && <div className="bg-yellow-50 border border-yellow-200 rounded p-3"><p className="body-text text-yellow-900">⚡ Stats recalculated for selected date range</p></div>}
            </div>
            <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="w-full">
                    <thead className="bg-gray-50 sticky top-0">
                        <tr>{columns.map(col => <th key={col.key} onClick={() => handleSort(col.key)} className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100">{col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}</th>)}</tr>
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
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl max-w-[95vw] w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-purple-700 text-white">
                            <h3 className="section-title font-bold">Career Timeline</h3>
                            <button onClick={() => setSelectedPitcher(null)} className="text-white hover:text-gray-200 text-2xl leading-none">&times;</button>
                        </div>
                        <div className="overflow-y-auto p-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>
                            <PitcherTimeline
                                playerId={selectedPitcher.id}
                                playerName={selectedPitcher.name}
                                pitcherGames={pitcherGames}
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

const DataTable = ({ data, columns, title, defaultSortKey = null, filterOptions = null, enableDateFilter = false, enableExport = true, paginate = true, onRowClick = null }) => {
    const [search, setSearch] = useState('');
    const [sortKey, setSortKey] = useState(defaultSortKey || columns[0]?.key);
    const [sortDir, setSortDir] = useState('desc');
    const [activeFilters, setActiveFilters] = useState({});
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

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
        return [...filtered].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            if (sortKey === 'date') {
                const aDate = new Date(aVal), bDate = new Date(bVal);
                if (!isNaN(aDate) && !isNaN(bDate)) return sortDir === 'asc' ? aDate - bDate : bDate - aDate;
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
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="section-title font-bold">{title}</h2>
                    <div className="flex items-center gap-2">
                        <span className="body-text text-gray-500">{sorted.length} of {data.length}</span>
                        {enableExport && <>
                            <button onClick={() => exportToCSV(sorted, columns, `${title.replace(/[^a-z0-9]/gi, '_')}.csv`)} className="px-3 py-1 bg-green-600 text-white body-text rounded hover:bg-green-700">📥 CSV</button>
                            <button onClick={() => exportToJSON(sorted, `${title.replace(/[^a-z0-9]/gi, '_')}.json`)} className="px-3 py-1 bg-blue-600 text-white body-text rounded hover:bg-blue-700">📥 JSON</button>
                        </>}
                    </div>
                </div>
                <div className="flex flex-wrap gap-4">
                    <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1 min-w-[200px] px-4 py-2 body-text border rounded-lg" />
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
                            className="px-3 py-2 body-text text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
                        >
                            Clear filters
                        </button>
                    )}
                </div>
            </div>
            {paginate && <PaginationControls page={page} setPage={setPage} totalPages={totalPages} totalItems={totalItems} />}
            <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="w-full">
                    <thead className="bg-gray-50 sticky top-0">
                        <tr>{columns.map(col => <th key={col.key} onClick={() => handleSort(col.key)} aria-sort={sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'} className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100">{col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y">
                        {displayData.map((row, idx) => (
                            <tr key={row.gameId || row.id || `item-${idx}`} className={`hover:bg-blue-50 ${onRowClick ? 'cursor-pointer' : ''}`} onClick={() => onRowClick && onRowClick(row)}>
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
    const [minAB, setMinAB] = useState(50);
    const [minIP, setMinIP] = useState(30);
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
            <div className="bg-white rounded-lg shadow p-4">
                <h3 className="subsection-title font-bold text-gray-900 mb-1">{title}</h3>
                {isRateStat && <p className="small-text text-blue-600 italic mb-2">Qualified</p>}
                <div className="space-y-2">
                    {shown.map((player, idx) => (
                        <div key={player.playerId} className="flex items-center justify-between py-1 border-b last:border-0">
                            <div className="flex items-center gap-2">
                                <span className="text-gray-500 body-text w-6">{idx + 1}.</span>
                                <PlayerLink playerId={player.playerId} name={player.name} />
                                <span className="small-text text-gray-500">({player.team})</span>
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
            <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex gap-4">
                        <button onClick={() => setCategory('batting')} className={`px-6 py-2 rounded body-text font-medium ${category === 'batting' ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}>Batting</button>
                        <button onClick={() => setCategory('pitching')} className={`px-6 py-2 rounded body-text font-medium ${category === 'pitching' ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}>Pitching</button>
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
                            <span className="font-medium text-gray-700">Date Range:</span>
                            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="px-3 py-2 body-text border rounded-lg" />
                        </label>
                        <span className="text-gray-400">to</span>
                        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="px-3 py-2 body-text border rounded-lg" />
                        {(startDate || endDate) && <button onClick={() => { setStartDate(''); setEndDate(''); }} className="px-3 py-2 body-text text-gray-600 hover:text-gray-900 border rounded-lg hover:bg-gray-50">Clear Dates</button>}
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
    const [careerMilestoneSort, setCareerMilestoneSort] = useState('event'); // 'event' or 'date'
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
                        <h1 className="text-2xl font-bold text-gray-900">🏆 Milestones</h1>
                        <p className="text-gray-500 mt-1">Special performances you've witnessed</p>
                    </div>
                    <div className="flex items-center gap-4">
                        {activeCategory !== 'firsts' && (
                            <div className="flex rounded-lg overflow-hidden border">
                                <button onClick={() => setViewMode('date')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'date' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}>📅 By Date</button>
                                <button onClick={() => setViewMode('category')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'category' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}>📂 By Category</button>
                            </div>
                        )}
                        <input
                            type="text"
                            placeholder="Search player, team..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                        >
                            {cat.label} <span className="ml-1 opacity-75">({cat.count})</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Career Milestones Section */}
            {careerFirsts && careerFirsts.length > 0 && (activeCategory === 'all' || activeCategory === 'firsts') && (
                <div className="bg-white rounded-xl shadow overflow-hidden">
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

                                // Shorten milestone for date view
                                const shortenMilestone = (m) => (m || '').replace('First Career ', '1st Career ').replace('Home Run', 'HR').replace('Stolen Base', 'SB').replace('Run Scored', 'Run').replace('Strikeout', 'K').replace('Inning Pitched', 'IP').replace('Double', '2B').replace('Triple', '3B');

                                // DATE VIEW
                                if (careerMilestoneSort === 'date') {
                                    const sortedByDate = [...filtered].sort((a, b) => (a.date || '').localeCompare(b.date || ''));
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
                                                            <span className="font-medium text-gray-800">{m.player_name}</span>
                                                        )}
                                                        <span className="text-sm text-amber-800 font-bold">{shortenMilestone(m.milestone)}</span>
                                                        {m.venue && <span className="text-xs text-gray-500 ml-auto">@ {m.venue}</span>}
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
                                    const sortedPlayers = Object.values(byPlayer).sort((a, b) => {
                                        const getLastName = (name) => {
                                            const parts = (name || '').trim().split(' ');
                                            if (parts.length <= 1) return (name || '').toLowerCase();
                                            // Handle compound surnames (De La Rosa, Van Der Berg, etc.)
                                            // Find the first particle that starts the surname
                                            const particles = ['de', 'la', 'del', 'van', 'von', 'der', 'den', 'el', 'al'];
                                            for (let i = 1; i < parts.length; i++) {
                                                if (particles.includes(parts[i].toLowerCase())) {
                                                    // Return everything from this particle onwards
                                                    return parts.slice(i).join(' ').toLowerCase();
                                                }
                                            }
                                            // Default: return just the last word
                                            return parts[parts.length - 1].toLowerCase();
                                        };
                                        return getLastName(a.name).localeCompare(getLastName(b.name));
                                    });
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
                                                                                <span className="text-xs text-gray-500">({m.date_display || m.date})</span>
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
                                                                                    <span className="font-medium text-gray-800">{m.player_name}</span>
                                                                                )}
                                                                                <span className="text-xs text-gray-500">({m.date_display || m.date})</span>
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
                    const parseDate = (d) => {
                        if (!d) return '';
                        if (d.includes('/')) { const [m, dd, y] = d.split('/'); return `${y}${(m||'').padStart(2,'0')}${(dd||'').padStart(2,'0')}`; }
                        return d;
                    };
                    const da = gameA ? parseDate(gameA.date) : '';
                    const db = gameB ? parseDate(gameB.date) : '';
                    return db.localeCompare(da);
                });

                return (
                    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                        <div className="p-4 border-b bg-gray-50">
                            <span className="font-bold body-text">{allFiltered.length} milestones</span>
                        </div>
                        <div className="divide-y" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                            {allFiltered.map((m, i) => {
                                const config = categoryConfig[m.type] || {};
                                const game = gameMap[m.gameId];
                                return (
                                    <div key={`${m.gameId}-${m.type}-${m.player}-${i}`} className="p-3 hover:bg-gray-50 flex items-start gap-3">
                                        <span className="text-lg">{config.icon || '🏆'}</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="font-semibold text-sm">{m.player}</span>
                                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium bg-${config.color || 'gray'}-100 text-${config.color || 'gray'}-700`}>{m.type}</span>
                                            </div>
                                            {m.detail && <div className="text-xs text-gray-600 mt-0.5 truncate">{m.detail}</div>}
                                        </div>
                                        <div className="text-right flex-shrink-0">
                                            <div className="text-xs text-gray-500">{game?.date || ''}</div>
                                            <div className="text-[10px] text-gray-400">{game?.awayTeam || ''} @ {game?.homeTeam || ''}</div>
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
                        const getHrCount = (detail) => {
                            const match = detail?.match(/(\d+)\s*HR/);
                            return match ? parseInt(match[1], 10) : 0;
                        };
                        filteredItems.sort((a, b) => {
                            const hrDiff = getHrCount(b.detail) - getHrCount(a.detail);
                            if (hrDiff !== 0) return hrDiff;
                            return new Date(b.date) - new Date(a.date);
                        });
                    }

                    if (filteredItems.length === 0) return null;

                    return (
                        <div key={type} className="bg-white rounded-xl shadow overflow-hidden">
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
                                <div className="p-4 bg-gray-50">
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
                                                            <span className="text-sm text-gray-500">({hrGroups[hrCount].length})</span>
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
                                                                    <div key={`${m.gameId}-${m.playerId}-${m.type}`} className="bg-white rounded-lg p-3 border border-gray-200 hover:border-rose-300 hover:shadow transition-all">
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
                                                                                        <span className="font-bold text-gray-900">{m.player || 'Team'}</span>
                                                                                    )}
                                                                                    <span className="text-xs px-2 py-0.5 rounded bg-rose-100 text-rose-700 font-semibold">
                                                                                        {m.team}
                                                                                    </span>
                                                                                </div>
                                                                                {m.detail && (
                                                                                    <p className="text-xs text-gray-600 mb-1 line-clamp-2">{m.detail}</p>
                                                                                )}
                                                                                <div className="flex items-center gap-2 text-xs text-gray-500">
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
                                                <div key={`${m.gameId}-${m.playerId}-${m.type}`} className="bg-white rounded-lg p-3 border border-gray-200 hover:border-blue-300 hover:shadow transition-all">
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
                                                                    <span className="font-bold text-gray-900">{m.player || 'Team'}</span>
                                                                )}
                                                                <span className={`text-xs px-2 py-0.5 rounded bg-${config.color}-100 text-${config.color}-700 font-semibold`}>
                                                                    {m.team}
                                                                </span>
                                                            </div>
                                                            {m.detail && (
                                                                <p className="text-xs text-gray-600 mb-1 line-clamp-2">{m.detail}</p>
                                                            )}
                                                            <div className="flex items-center gap-2 text-xs text-gray-500">
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
                                        <p className="text-center text-sm text-gray-500 mt-3">
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
    const allPlayers = [...(data.players || []), ...(data.pitchers || [])];
    const { seenPlayers, notSeenPlayers } = useMemo(() => {
        const matched = [];
        const seen = new Set();
        const buildPlayerRow = (ncaa, overrides = {}) => {
            const ncaaStats = ncaa.ncaa_stats || {};
            const proStats = ncaa.pro_stats || {};
            const hasNCAA = (ncaaStats.G || 0) > 0;
            const stats = hasNCAA ? ncaaStats : proStats;
            const college = (ncaa.ncaa_teams || []).join(', ');
            const levels = (ncaa.levels || []);
            const hasNCAALevel = levels.includes('NCAA');
            const isPitcher = stats.is_pitcher || false;
            return {
                college: college || (hasNCAALevel ? 'Unknown' : '—'),
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

        // Players seen in both college and MLB games
        allPlayers.forEach(p => {
            const pid = p.playerId;
            if (pid && ncaaRef[pid] && !seen.has(pid)) {
                seen.add(pid);
                const ncaa = ncaaRef[pid];
                matched.push(buildPlayerRow(ncaa, {
                    name: p.name,
                    playerId: pid,
                    mlbTeam: p.team,
                    seenInMlb: true,
                }));
            }
        });
        // NCAA players who reached MLB but weren't at user's MLB games
        const notSeen = [];
        Object.entries(ncaaRef).forEach(([key, ncaa]) => {
            if (seen.has(key)) return;
            const levels = ncaa.levels || [];
            if (!levels.includes('MLB') || !levels.includes('NCAA')) return;
            if (ncaa.seen_in_mlb) return;
            const mlbBrefId = ncaa.mlb_bref_id || '';
            if (seen.has(mlbBrefId)) return;
            seen.add(key);
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
        return <EmptyState icon="🎓" title="No College Data" message="Run the NCAA processor with --export-players to generate cross-reference data." />;
    }
    if (seenPlayers.length === 0 && notSeenPlayers.length === 0) {
        return <EmptyState icon="🎓" title="No College Matches" message="No players in your games were found in the NCAA processor data." />;
    }

    return (
        <div className="space-y-6">
            {seenPlayers.length > 0 && (
                <DataTable
                    title={`🎓 Seen in College & MLB (${seenPlayers.length} players)`}
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
                                <a href={`https://www.baseball-reference.com/players/${(r.playerId || '').charAt(0).toLowerCase()}/${r.playerId}.shtml`} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-600 text-xs" title="View on Baseball Reference">↗</a>
                            </div>
                        )},
                        { key: 'mlbTeam', label: 'MLB Team' },
                        { key: 'college', label: 'College' },
                        { key: 'levels', label: 'Levels' },
                        { key: 'source', label: 'Stats From', render: (v) => (
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${v === 'NCAA' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}`}>{v}</span>
                        )},
                        { key: 'G', label: 'G' },
                        { key: 'statLine', label: 'College Stats', render: (v, r) => (
                            <span className="font-mono text-sm">{v}</span>
                        )},
                        { key: 'websiteUrl', label: '', render: (v) => v ? <a href={v} target="_blank" rel="noopener noreferrer" className="text-green-600 hover:text-green-800 small-text font-medium">View on NCAA site →</a> : null },
                    ]}
                />
            )}
            {notSeenPlayers.length > 0 && (
                <DataTable
                    title={`🎓 Saw in College, Now in MLB (${notSeenPlayers.length} players)`}
                    data={notSeenPlayers}
                    defaultSortKey="name"
                    defaultSortDirection="asc"
                    columns={[
                        { key: 'name', label: 'Player', render: (v, r) => r.playerId ? <PlayerLink playerId={r.playerId} name={v} /> : v },
                        { key: 'college', label: 'College' },
                        { key: 'levels', label: 'Levels' },
                        { key: 'G', label: 'College G' },
                        { key: 'statLine', label: 'College Stats', render: (v, r) => (
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
            return { ...p, gameList, regGameCount: regGames.length };
        }).filter(p => p.regGameCount > 0);
    }, [data]);

    return (
        <div className="space-y-4">
            <DataTable
                title={`👻 Players Without Regular Season Stats (${allNoStats.length})`}
                data={allNoStats}
                defaultSortKey="games"
                onRowClick={(row) => setSelectedPlayer(selectedPlayer?.playerId === row.playerId ? null : row)}
                columns={[
                    { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                    { key: 'teams', label: 'Team(s)' },
                    { key: 'games', label: 'Games' },
                    { key: 'positions', label: 'Position(s)' },
                ]}
            />
            {selectedPlayer && selectedPlayer.gameList && selectedPlayer.gameList.length > 0 && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPlayer(null)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-md w-full max-h-[70vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b bg-gray-700 text-white rounded-t-lg flex items-center justify-between">
                            <h3 className="font-bold">{selectedPlayer.name} — {selectedPlayer.gameList.length} game{selectedPlayer.gameList.length > 1 ? 's' : ''}</h3>
                            <button onClick={() => setSelectedPlayer(null)} className="text-white hover:text-gray-200 text-xl leading-none">&times;</button>
                        </div>
                        <div className="p-3 space-y-2">
                            {selectedPlayer.gameList.map((g, i) => (
                                <div key={i} className="bg-gray-50 rounded p-3">
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium text-sm">{g.awayTeam} @ {g.homeTeam}</span>
                                        <span className="text-xs text-gray-500">{g.date}</span>
                                    </div>
                                    <div className="text-xs text-gray-400 mt-1">{g.score} • {g.venue || ''}</div>
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
                    <div className={`w-14 h-14 ${passing.new_rank <= 10 ? 'bg-gradient-to-br from-yellow-400 to-amber-500 ring-2 ring-yellow-300' : passing.new_rank <= 25 ? 'bg-gradient-to-br from-purple-500 to-violet-600' : passing.new_rank <= 50 ? 'bg-gradient-to-br from-purple-400 to-purple-500' : 'bg-gradient-to-br from-gray-400 to-gray-500'} rounded-full flex items-center justify-center text-white font-bold text-lg shadow-md`}>
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
                            <span className="font-bold text-gray-900 text-lg">{passing.player_name}</span>
                        )}
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-700">{passing.stat_name}</span>
                    </div>
                    <p className="text-purple-600 mt-1">{passedText}</p>
                    <div className="mt-2 flex items-center gap-3 text-xs text-gray-500 flex-wrap">
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
                        <h1 className="text-2xl font-bold text-gray-900">📜 History Witnessed</h1>
                        <p className="text-gray-500 mt-1">Players climbing the all-time leaderboards at games you attended</p>
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
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
                        <option value="all">All Stats</option>
                        {availableStats.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <select value={rankFilter} onChange={(e) => setRankFilter(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
                        <option value="all">All Ranks</option>
                        <option value="top10">Top 10</option>
                        <option value="top25">Top 25</option>
                        <option value="top50">Top 50</option>
                    </select>
                    <input type="text" placeholder="Search player..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm flex-1 min-w-[150px]" />
                    <div className="flex rounded-lg overflow-hidden border border-gray-300">
                        <button onClick={() => setViewMode('timeline')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'timeline' ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}>Timeline</button>
                        <button onClick={() => setViewMode('by-stat')} className={`px-3 py-2 text-sm font-medium ${viewMode === 'by-stat' ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}>By Stat</button>
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
                                        <div className="font-bold text-gray-900 text-sm">{p.player_name}</div>
                                        <div className="text-xs text-gray-500">{p.stat_name} - {p.date_display || p.date}</div>
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
                        <div key={stat} className="bg-white rounded-xl shadow overflow-hidden">
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
        <div className="bg-white rounded-lg shadow">
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
                                <span className="text-[10px] text-gray-500 mt-1">{d.year.slice(2)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
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
        const parseDate = (d) => {
            if (!d) return '';
            if (d.includes('/')) { const [m, dd, y] = d.split('/'); return `${y}${(m||'').padStart(2,'0')}${(dd||'').padStart(2,'0')}`; }
            return d;
        };

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
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
                <h2 className="subsection-title font-bold">Cumulative Stats Witnessed</h2>
            </div>
            <div className="p-4">
                <div className="flex flex-wrap gap-1.5 mb-3">
                    {statDefs.map(s => (
                        <button key={s.key} onClick={() => setActiveStat(s.key)}
                            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${activeStat === s.key ? 'text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                            style={activeStat === s.key ? { backgroundColor: s.color } : {}}>
                            {s.label}
                        </button>
                    ))}
                </div>
                <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
                    {yLabels.map((l, i) => (
                        <g key={i}>
                            <line x1={pad.left} y1={l.y} x2={width - pad.right} y2={l.y} stroke="#e5e7eb" strokeWidth="1" />
                            <text x={pad.left - 8} y={l.y + 4} textAnchor="end" fill="#6b7280" fontSize="10">{l.val.toLocaleString()}</text>
                        </g>
                    ))}
                    <polygon points={`${pad.left},${pad.top + chartH} ${points} ${width - pad.right},${pad.top + chartH}`} fill={activeColor} fillOpacity="0.1" />
                    <polyline points={points} fill="none" stroke={activeColor} strokeWidth="2" strokeLinejoin="round" />
                </svg>
                <div className="text-center text-xs text-gray-500 mt-1">
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
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
                <h2 className="subsection-title font-bold">Attendance Patterns</h2>
            </div>
            <div className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h3 className="small-text font-bold text-gray-500 uppercase mb-3">Day of Week</h3>
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
                                            <span className="text-[10px] text-gray-500 mt-1">{day}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                    <div>
                        <h3 className="small-text font-bold text-gray-500 uppercase mb-3">Most Seen Teams</h3>
                        <div className="space-y-1.5">
                            {patterns.topTeams.map(([team, count], i) => (
                                <div key={team} className="flex items-center justify-between text-sm">
                                    <div className="flex items-center gap-2">
                                        <span className="text-gray-400 w-4">{i + 1}.</span>
                                        <span className="font-medium">{team}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-20 bg-gray-200 rounded-full h-2">
                                            <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${(count / patterns.topTeams[0][1]) * 100}%` }}></div>
                                        </div>
                                        <span className="text-xs text-gray-500 w-6 text-right">{count}</span>
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

const Dashboard = ({ data, onTabChange }) => {
    // Get recent highlights for the dashboard
    const toSortDate = (d) => { const p = (d || '').split('/'); return p.length === 3 ? `${p[2]}${p[0]}${p[1]}` : d || ''; };
    const recentDebuts = useMemo(() => [...(data.debuts || [])].sort((a, b) => toSortDate(b.date).localeCompare(toSortDate(a.date))).slice(0, 5), [data.debuts]);
    const recentFinalGames = useMemo(() => [...(data.finalGames || [])].sort((a, b) => toSortDate(b.date).localeCompare(toSortDate(a.date))).slice(0, 5), [data.finalGames]);

    // Notable career milestones (round number milestones like 100th, 200th, 500th HR)
    const notableCareerMilestones = useMemo(() => {
        return [...(data.careerFirsts || [])]
            .filter(f => {
                const match = f.milestone?.match(/#?(\\d+)/);
                if (match) {
                    const num = parseInt(match[1]);
                    return num >= 100 && num % 100 === 0;
                }
                return false;
            })
            .sort((a, b) => {
                const numA = parseInt((a.milestone?.match(/#?(\\d+)/) || [])[1] || 0);
                const numB = parseInt((b.milestone?.match(/#?(\\d+)/) || [])[1] || 0);
                return numB - numA;
            })
            .slice(0, 8);
    }, [data.careerFirsts]);

    // Top all-time passings for dashboard preview
    const topPassings = useMemo(() => {
        return [...(data.allTimePassings || [])].sort((a, b) => a.new_rank - b.new_rank).slice(0, 5);
    }, [data.allTimePassings]);

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Games" value={data.games?.length || 0} color="blue" onClick={() => onTabChange && onTabChange('gamelog')} />
                <StatCard title="Players" value={data.players?.length || 0} color="green" onClick={() => onTabChange && onTabChange('players')} />
                <StatCard title="Milestones" value={data.milestones?.length || 0} color="purple" onClick={() => onTabChange && onTabChange('milestones')} />
                <StatCard title="Teams" value={data.teams?.length || 0} color="orange" onClick={() => onTabChange && onTabChange('venues')} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6"><MilestoneChart milestones={data.milestones} /></div>
                <div className="bg-white rounded-lg shadow p-6"><TeamChart teams={data.teams} /></div>
            </div>

            {/* Trends & Patterns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <GamesPerYearChart games={data.games} />
                <AttendancePatterns games={data.games} />
            </div>
            <CumulativeStatsChart games={data.games} playerGames={data.playerGames} pitcherGames={data.pitcherGames} />

            {/* Recent Highlights */}
            {(recentDebuts.length > 0 || recentFinalGames.length > 0) && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {recentDebuts.length > 0 && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="subsection-title font-bold text-gray-900">🌟 Recent MLB Debuts</h3>
                                <button onClick={() => onTabChange && onTabChange('special')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                            </div>
                            <div className="space-y-3">
                                {recentDebuts.map((d, i) => (
                                    <div key={`debut-${d.playerId || i}`} className="flex items-center justify-between py-2 border-b last:border-0">
                                        <div>
                                            <PlayerLink playerId={d.playerId} name={d.player} />
                                            <span className="small-text text-gray-500 ml-2">{d.team}</span>
                                        </div>
                                        <span className="small-text text-gray-400">{d.date}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    {recentFinalGames.length > 0 && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="subsection-title font-bold text-gray-900">👋 Recent Final Games</h3>
                                <button onClick={() => onTabChange && onTabChange('special')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                            </div>
                            <div className="space-y-3">
                                {recentFinalGames.map((d, i) => (
                                    <div key={`final-${d.playerId || i}`} className="flex items-center justify-between py-2 border-b last:border-0">
                                        <div>
                                            <PlayerLink playerId={d.playerId} name={d.player} />
                                            <span className="small-text text-gray-500 ml-2">{d.team}</span>
                                        </div>
                                        <span className="small-text text-gray-400">{d.date}</span>
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
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="subsection-title font-bold text-gray-900">⭐ Notable Career Milestones</h3>
                                <button onClick={() => onTabChange && onTabChange('milestones')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                            </div>
                            <div className="space-y-3">
                                {notableCareerMilestones.map((m, i) => {
                                    const num = (m.milestone?.match(/#?(\\d+)/) || [])[1] || '';
                                    return (
                                        <div key={`cm-${i}`} className="flex items-center gap-3 py-2 border-b last:border-0">
                                            <span className="inline-flex items-center justify-center min-w-[48px] h-8 bg-gradient-to-r from-amber-400 to-yellow-500 text-white text-sm font-bold rounded-full px-2">#{num}</span>
                                            <div className="flex-1">
                                                <PlayerLink playerId={m.player_id} name={m.player_name} />
                                                <span className="small-text text-gray-500 ml-1">{m.milestone?.replace(/#?\\d+\\w*\\s*/, '').trim()}</span>
                                            </div>
                                            <span className="small-text text-gray-400">{m.date_display || m.date}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                    {topPassings.length > 0 && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="subsection-title font-bold text-gray-900">📜 History Witnessed</h3>
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
                                        <span className="small-text text-gray-400">{p.date_display || p.date}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Companions summary */}
            {data.companionData?.companions?.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="subsection-title font-bold text-gray-900">👥 Top Game Companions</h3>
                        <button onClick={() => onTabChange && onTabChange('companions')} className="small-text text-blue-600 hover:text-blue-800 font-medium">View all →</button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {data.companionData.companions.slice(0, 6).map((c, i) => (
                            <div key={`comp-${c.name || i}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <span className="body-text font-medium text-gray-900">{c.name}</span>
                                <span className="small-text text-gray-500">{c.games} games</span>
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
    const [expanded, setExpanded] = useState(false);
    if (!badges || badges.length === 0) return null;
    const displayBadges = expanded ? badges : badges.slice(0, 3);
    return (
        <div className="flex flex-wrap gap-1 max-w-xs">
            {displayBadges.map((badge, i) => (
                <span
                    key={`${badge.type}-${badge.text}-${i}`}
                    className={`px-1.5 py-0.5 rounded text-xs whitespace-nowrap ${badgeColors[badge.type] || 'bg-gray-100 text-gray-700'}`}
                    title={badge.title}
                >
                    {badge.text}
                </span>
            ))}
            {badges.length > 3 && (
                <button
                    onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
                    className="px-1.5 py-0.5 rounded text-xs bg-gray-200 text-gray-600 hover:bg-gray-300 cursor-pointer"
                >
                    {expanded ? '−' : `+${badges.length - 3}`}
                </button>
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

    const parseDate = (d) => {
        if (!d) return '';
        if (d.includes('/')) { const [m, dd, y] = d.split('/'); return `${y}${(m||'').padStart(2,'0')}${(dd||'').padStart(2,'0')}`; }
        return d;
    };
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
        const venue = game.venue || '';

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

    // Compute total stats witnessed across all games (excluding spring training)
    const totalStats = useMemo(() => {
        const springGameIds = new Set((games || []).filter(g => g.gameType === 'spring').map(g => g.gameId));
        const stats = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
        let pitK = 0;
        (playerGames || []).forEach(pg => {
            if (springGameIds.has(pg.gameId)) return;
            stats.H += (pg.h || 0);
            stats.R += (pg.r || 0);
            stats.HR += (pg.hr || 0);
            stats.RBI += (pg.rbi || 0);
            stats.SO += (pg.so || 0);
            stats.BB += (pg.bb || 0);
            stats.SB += (pg.sb || 0);
            stats['2B'] += (pg.doubles || 0);
            stats['3B'] += (pg.triples || 0);
        });
        (pitcherGames || []).forEach(pg => {
            if (springGameIds.has(pg.gameId)) return;
            pitK += (pg.so || 0);
        });
        return { ...stats, pitK, gameCount: (games || []).length - springGameIds.size };
    }, [games, playerGames, pitcherGames]);

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
        'matchup': 'bg-gray-100 text-gray-700',
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
        const shortenMilestone = (m) => (m || '').replace('First Career ', '1st Career ').replace('Home Run', 'HR').replace('Stolen Base', 'SB').replace('Run Scored', 'Run').replace('Strikeout', 'K').replace('Inning Pitched', 'IP').replace('Double', '2B').replace('Triple', '3B');
        const getLastName = (name) => { const parts = (name || '').split(' '); return parts[parts.length - 1] || name || '?'; };
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
            result[gid] = [...regularBadges, ...careerFirstBadges, ...(cumulativeBadges[gid] || [])];
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
            <div className="bg-white rounded-lg shadow mb-2 p-3">
                <div className="flex flex-wrap items-center gap-3">
                    <span className="small-text font-semibold text-gray-600">🏅 Badge Filter:</span>
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
                            className="px-3 py-1.5 body-text text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
                        >
                            Clear
                        </button>
                    )}
                    {hasBadgeFilter && (
                        <span className="small-text text-gray-500">{badgeFilteredGames.length} of {games.length} games</span>
                    )}
                </div>
            </div>
            <DataTable
                title="📋 Game Log"
                data={badgeFilteredGames}
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
                            <span>{v}</span>
                            {row.gameType === 'spring' && <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-[10px] font-semibold rounded">ST</span>}
                            {row.gameType === 'postseason' && <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 text-[10px] font-semibold rounded">PS</span>}
                        </div>
                    )},
                    { key: 'awayTeam', label: 'Away' },
                    { key: 'homeTeam', label: 'Home' },
                    { key: 'score', label: 'Score' },
                    { key: 'venue', label: 'Venue' },
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
            
            {selectedGame && (
                <GameDetailsModal
                    game={selectedGame}
                    playerGames={playerGames}
                    pitcherGames={pitcherGames}
                    careerFirsts={careerFirstsByGame?.[selectedGame.gameId] || []}
                    allTimePassings={(allTimePassingsByGame || {})[selectedGame.gameId] || []}
                    badges={allBadgesByGame?.[selectedGame.gameId] || []}
                    onClose={() => setSelectedGame(null)}
                />
            )}
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
                    <h2 className="section-title font-bold text-gray-900">🗺️ Stadium Checklist</h2>

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
                    <span className="text-gray-600">Legend:</span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-gray-400 opacity-40"></span>
                        <span className="text-gray-600">Not Visited</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-green-500"></span>
                        <span className="text-gray-600">Visited</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-orange-500"></span>
                        <span className="text-gray-600">Visited + Saw Orioles</span>
                    </span>
                </div>
            </div>

            {/* Map Container */}
            <div ref={mapRef} style={{ height: '500px', width: '100%' }}></div>

            {/* Progress Stats */}
            <div className="p-4 border-t bg-gray-50">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">{stats.visitedCurrent}/{stats.currentTotal}</div>
                        <div className="small-text text-gray-600">Current Stadiums</div>
                        <div className="text-xs text-gray-400">{stats.percentCurrent}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-500">{stats.oriolesCurrent}/{stats.currentTotal}</div>
                        <div className="small-text text-gray-600">Saw Orioles</div>
                        <div className="text-xs text-gray-400">{stats.percentOrioles}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">{stats.totalVisited}</div>
                        <div className="small-text text-gray-600">Total Stadiums</div>
                        <div className="text-xs text-gray-400">Including historical</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">{stats.totalOrioles}</div>
                        <div className="small-text text-gray-600">O's Venues</div>
                        <div className="text-xs text-gray-400">Total Orioles venues</div>
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
                            <h3 className="font-semibold text-gray-700 mb-3">
                                Visited Stadiums
                                <span className="text-sm font-normal text-gray-500 ml-2">({visitedStadiums.length})</span>
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
                                                <div className="font-medium truncate text-gray-900">{stadium.name}</div>
                                                <div className="text-xs text-gray-500">
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
                            <h3 className="font-semibold text-gray-700 mb-3">
                                Still To Visit
                                <span className="text-sm font-normal text-gray-500 ml-2">({toVisit.length} remaining)</span>
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                {toVisit.map(stadium => (
                                    <div
                                        key={stadium.id}
                                        className="flex items-center gap-2 p-2 rounded text-sm bg-gray-50 border border-gray-200"
                                    >
                                        <span className="text-lg opacity-30">⬜</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium truncate text-gray-400">{stadium.name}</div>
                                            <div className="text-xs text-gray-400">{stadium.team}</div>
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
    'AL West': ['ANA', 'HOU', 'OAK', 'SEA', 'TEX'],
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
    'MIN': 'MIN', 'HOU': 'HOU', 'OAK': 'OAK', 'SEA': 'SEA', 'TEX': 'TEX',
    'ATL': 'ATL', 'MIA': 'MIA', 'PHI': 'PHI', 'CIN': 'CIN', 'MIL': 'MIL',
    'PIT': 'PIT', 'ARI': 'ARI', 'COL': 'COL',
};

const TEAM_CODE_TO_NAME = {
    // Retrosheet codes
    'BAL': 'Baltimore Orioles', 'BOS': 'Boston Red Sox', 'NYA': 'New York Yankees',
    'TBA': 'Tampa Bay Rays', 'TOR': 'Toronto Blue Jays', 'CHA': 'Chicago White Sox',
    'CLE': 'Cleveland Guardians', 'DET': 'Detroit Tigers', 'KCA': 'Kansas City Royals',
    'MIN': 'Minnesota Twins', 'ANA': 'Los Angeles Angels', 'HOU': 'Houston Astros',
    'OAK': 'Oakland Athletics', 'SEA': 'Seattle Mariners', 'TEX': 'Texas Rangers',
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
    'ATH': 'OAK',  // Athletics (Sacramento 2025) -> Oakland Athletics
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
        const parseDate = (d) => {
            if (!d) return '';
            if (d.includes('/')) {
                const [m, dd, y] = d.split('/');
                return `${y}${(m || '').padStart(2, '0')}${(dd || '').padStart(2, '0')}`;
            }
            return d;
        };
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
        <div className="bg-white rounded-lg shadow">
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
                                className={`px-3 py-2 ${viewMode === 'teams' ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
                            >
                                Teams
                            </button>
                            <button
                                onClick={() => setViewMode('stadiums')}
                                className={`px-3 py-2 ${viewMode === 'stadiums' ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
                            >
                                Stadiums
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Progress Summary */}
            <div className="p-4 bg-gray-50 border-b">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">
                            {currentData.teamsSeen}/{currentData.totalTeams}
                        </div>
                        <div className="text-sm text-gray-600">Teams Seen</div>
                        <div className="text-xs text-gray-400">{teamProgress}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">
                            {currentData.stadiumsVisited}/{currentData.totalStadiums}
                        </div>
                        <div className="text-sm text-gray-600">Stadiums Visited</div>
                        <div className="text-xs text-gray-400">{stadiumProgress}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">
                            {Object.keys(tracking.divisionTeamsCompleted || {}).length}/6
                        </div>
                        <div className="text-sm text-gray-600">Div. Teams</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-indigo-600">
                            {Object.keys(tracking.divisionStadiumsCompleted || {}).length}/6
                        </div>
                        <div className="text-sm text-gray-600">Div. Stadiums</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-600">
                            {tracking.totalGames || games?.length || 0}
                        </div>
                        <div className="text-sm text-gray-600">Total Games</div>
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
                                className={`flex items-center gap-3 p-3 rounded-lg border ${
                                    isSeen
                                        ? 'bg-green-50 border-green-200'
                                        : 'bg-gray-50 border-gray-200'
                                }`}
                            >
                                <span className="text-2xl">{isSeen ? '✅' : '⬜'}</span>
                                <div className="flex-1 min-w-0">
                                    <div className={`font-medium truncate ${!isSeen && 'text-gray-400'}`}>
                                        {displayName || 'Unknown'}
                                    </div>
                                    <div className="text-xs text-gray-500">
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
                    <h3 className="font-semibold text-gray-700 mb-4">Division Progress</h3>
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
                                        isComplete ? 'bg-green-50 border-green-300' : 'bg-white border-gray-200'
                                    }`}
                                >
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-semibold">{div}</span>
                                        <span className="text-sm">{divData.teamsSeen}/{divData.totalTeams}</span>
                                    </div>
                                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
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
        const sortedGames = [...(games || [])].sort((a, b) => {
            const parseDate = (d) => {
                if (!d) return '';
                if (d.includes('/')) {
                    const [m, dd, y] = d.split('/');
                    return `${y}${(m || '').padStart(2, '0')}${(dd || '').padStart(2, '0')}`;
                }
                return d;
            };
            return parseDate(b.date).localeCompare(parseDate(a.date));
        });

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
        return colors[type] || 'bg-gray-100 border-gray-300';
    };

    return (
        <div className="bg-white rounded-lg shadow">
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
            <div className="p-4 bg-gray-50 border-b">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">{badgeCounts.all}</div>
                        <div className="text-sm text-gray-600">Total Badges</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">{badgeCounts['div-complete'] || 0}</div>
                        <div className="text-sm text-gray-600">Divisions Complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">{milestoneData.tracking?.venueOrder?.length || 0}</div>
                        <div className="text-sm text-gray-600">Unique Venues</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-600">{Object.keys(milestoneData.tracking?.matchupsSeen || {}).length}</div>
                        <div className="text-sm text-gray-600">Unique Matchups</div>
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
                            >
                                <div className="flex items-start gap-3">
                                    <span className="text-2xl">{getBadgeIcon(badge.type)}</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold text-gray-800 truncate">{badge.text}</div>
                                        <div className="text-xs text-gray-600 truncate">{badge.away} vs {badge.home}</div>
                                        <div className="text-xs text-gray-400 mt-1">{badge.date}</div>
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
                <div className="min-h-screen flex items-center justify-center bg-gray-50">
                    <div className="bg-white rounded-xl shadow-lg p-8 max-w-lg text-center">
                        <h2 className="text-xl font-bold text-red-600 mb-4">Something went wrong</h2>
                        <p className="text-gray-600 mb-4">{this.state.error?.message || 'An unexpected error occurred while rendering.'}</p>
                        <button onClick={() => { this.setState({ hasError: false, error: null }); }} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 mr-2">Try Again</button>
                        <button onClick={() => window.location.reload()} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">Reload Page</button>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}

const UmpireTracker = ({ umpireLog }) => {
    const [search, setSearch] = useState('');

    const filtered = useMemo(() => {
        if (!search) return umpireLog;
        const q = search.toLowerCase();
        return umpireLog.filter(u => u.name.toLowerCase().includes(q));
    }, [umpireLog, search]);

    const totalUmpires = umpireLog.length;
    const multipleGames = umpireLog.filter(u => u.games > 1).length;

    return (
        <div className="space-y-4">
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                    <div>
                        <h2 className="section-title font-bold">Umpire Tracker</h2>
                        <p className="body-text text-gray-500 mt-1">{totalUmpires} unique umpires seen, {multipleGames} seen multiple times</p>
                    </div>
                    <input
                        type="text"
                        placeholder="Search umpires..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="px-4 py-2 body-text border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                    />
                </div>
                <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                    <table className="w-full">
                        <thead className="bg-gray-50 sticky top-0">
                            <tr>
                                <th className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase">Umpire</th>
                                <th className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase">Games</th>
                                <th className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase">Positions</th>
                                <th className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase">First Seen</th>
                                <th className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase">Last Seen</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {filtered.map(u => (
                                <tr key={u.name} className="hover:bg-blue-50">
                                    <td className="px-4 py-3 body-text font-semibold">{u.name}</td>
                                    <td className="px-4 py-3 body-text font-bold text-blue-600">{u.games}</td>
                                    <td className="px-4 py-3">
                                        <div className="flex gap-1">
                                            {Object.entries(u.positions || {}).sort((a, b) => b[1] - a[1]).map(([pos, count]) => (
                                                <span key={pos} className="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-medium">
                                                    {pos}: {count}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 body-text text-gray-600">{u.firstSeen}</td>
                                    <td className="px-4 py-3 body-text text-gray-600">{u.lastSeen}</td>
                                </tr>
                            ))}
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

    // Build grid of numbers 00-99, filtering spring training if needed
    const numbers = useMemo(() => {
        const grid = [];
        const filterFn = (players) => includeSpring ? players : players.filter(p => {
            // Game IDs starting with 'M' are MLB API (spring training) games
            return !p.gameId?.startsWith('M');
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

    return (
        <div className="space-y-4">
            <div className="bg-white rounded-lg shadow p-6">
                <div className="mb-4">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h2 className="section-title font-bold">Jersey Number Collection</h2>
                            <p className="body-text text-gray-500 mt-1">
                                {collected} of {total} numbers collected ({Math.round(collected / total * 100)}%)
                            </p>
                        </div>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={includeSpring} onChange={(e) => setIncludeSpring(e.target.checked)} className="rounded" />
                            <span className="body-text text-gray-600">Include Spring Training</span>
                        </label>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 mt-2">
                        <div className="bg-blue-600 h-3 rounded-full transition-all" style={{ width: `${(collected / total * 100)}%` }}></div>
                    </div>
                </div>

                <div className="grid gap-1.5" style={{ gridTemplateColumns: 'repeat(10, 1fr)' }}>
                    {numbers.map(({ num, players }) => {
                        const hasPlayers = players.length > 0;
                        return (
                            <button
                                key={num}
                                onClick={() => hasPlayers && setSelectedNumber(selectedNumber === num ? null : num)}
                                className={`aspect-square flex items-center justify-center rounded-lg text-sm font-bold transition-all ${
                                    hasPlayers
                                        ? selectedNumber === num
                                            ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                                            : 'bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer'
                                        : 'bg-gray-100 text-gray-400'
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
                                        <span className="text-xs text-gray-500">{p.team}</span>
                                    </div>
                                    <span className="text-xs text-gray-400">{p.date}</span>
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
    'Japan': 'Japan', 'South Korea': 'South Korea', 'Colombia': 'Colombia',
    'Panama': 'Panama', 'Nicaragua': 'Nicaragua', 'Taiwan': 'Taiwan',
    'Australia': 'Australia', 'Brazil': 'Brazil', 'Germany': 'Germany',
    'Honduras': 'Honduras', 'Netherlands': 'Netherlands', 'Italy': 'Italy',
    'Jamaica': 'Jamaica', 'Peru': 'Peru', 'Saudi Arabia': 'Saudi Arabia',
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
    }, [geoData, dataByPlace, selectedPlace]);

    useEffect(() => {
        if (mapInstanceRef.current) {
            setTimeout(() => mapInstanceRef.current.invalidateSize(), 100);
        }
    });

    return <div ref={mapRef} style={{ height: '500px', borderRadius: '8px' }} className="border"></div>;
};

const PlayerOrigins = ({ playerBios, allPlayers }) => {
    const [viewMode, setViewMode] = useState('statesMap');
    const [selectedPlace, setSelectedPlace] = useState(null);
    const [statesGeo, setStatesGeo] = useState(null);
    const [countriesGeo, setCountriesGeo] = useState(null);

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
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <div>
                    <h2 className="section-title font-bold">Player Origins</h2>
                    <p className="body-text text-gray-500 mt-1">{data.total} players from {Object.keys(data.byCountry).length} countries, {Object.keys(data.byState).length} US states</p>
                </div>
                <div className="flex rounded-lg overflow-hidden border">
                    <button onClick={() => { setViewMode('statesMap'); setSelectedPlace(null); }} className={`px-4 py-2 text-sm font-medium ${viewMode === 'statesMap' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}>US States</button>
                    <button onClick={() => { setViewMode('countriesMap'); setSelectedPlace(null); }} className={`px-4 py-2 text-sm font-medium ${viewMode === 'countriesMap' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}>World</button>
                    <button onClick={() => { setViewMode('list'); setSelectedPlace(null); }} className={`px-4 py-2 text-sm font-medium ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}>List</button>
                </div>
            </div>

            {viewMode === 'statesMap' && statesGeo && (
                <ChoroplethMap
                    geoData={statesGeo}
                    dataByPlace={data.byStateName}
                    nameMapper={(name) => name}
                    center={[39.8, -98.6]}
                    zoom={4}
                    onSelect={(name) => setSelectedPlace(STATE_NAME_TO_ABBR[name] || name)}
                    selectedPlace={selectedPlace ? (STATE_ABBR_TO_NAME[selectedPlace] || selectedPlace) : null}
                />
            )}

            {viewMode === 'countriesMap' && countriesGeo && (
                <ChoroplethMap
                    key="countries"
                    geoData={countriesGeo}
                    dataByPlace={Object.fromEntries(
                        Object.entries(data.byCountry).map(([mlb, players]) => [COUNTRY_NAME_MAP[mlb] || mlb, players])
                    )}
                    nameMapper={(name) => name}
                    center={[20, -40]}
                    zoom={2}
                    onSelect={(geoName) => { const mlb = countryGeoToMlb(geoName); setSelectedPlace(prev => prev === mlb ? null : mlb); }}
                    selectedPlace={selectedPlace ? (COUNTRY_NAME_MAP[selectedPlace] || selectedPlace) : null}
                />
            )}

            {selectedPlace && selectedPlayers.length > 0 && viewMode !== 'list' && (
                <div className="mt-4 bg-blue-50 rounded-lg p-4">
                    <h3 className="subsection-title font-bold mb-2">{selectedPlace} — {selectedPlayers.length} players</h3>
                    <div className="flex flex-wrap gap-2">
                        {selectedPlayers.sort((a, b) => (a.name || '').localeCompare(b.name || '')).map(p => (
                            <span key={p.playerId} className="px-2 py-1 bg-white rounded text-sm">
                                <PlayerLink playerId={p.playerId} name={p.name} />
                                {p.birthCity && <span className="text-gray-400 text-xs ml-1">({p.birthCity})</span>}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {viewMode === 'list' && (
                <div className="space-y-2">
                    {Object.entries(data.byCountry).sort((a, b) => b[1].length - a[1].length).map(([place, players]) => (
                        <details key={place} className="bg-gray-50 rounded-lg">
                            <summary className="px-4 py-3 cursor-pointer hover:bg-gray-100 flex items-center justify-between">
                                <span className="font-semibold body-text">{place}</span>
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-bold">{players.length}</span>
                            </summary>
                            <div className="px-4 pb-3 flex flex-wrap gap-2">
                                {players.sort((a, b) => (a.name || '').localeCompare(b.name || '')).map(p => (
                                    <span key={p.playerId} className="px-2 py-1 bg-white rounded text-sm">
                                        <PlayerLink playerId={p.playerId} name={p.name} />
                                        {p.birthCity && <span className="text-gray-400 text-xs ml-1">({p.birthCity})</span>}
                                    </span>
                                ))}
                            </div>
                        </details>
                    ))}
                </div>
            )}
        </div>
    );
};

const PlayerBirthdays = ({ playerBios, allPlayers }) => {
    const [selectedDay, setSelectedDay] = useState(null);
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
        <div className="bg-white rounded-lg shadow p-6">
            <div className="mb-4">
                <h2 className="section-title font-bold">Birthday Calendar</h2>
                <p className="body-text text-gray-500 mt-1">
                    {data.collected} of {data.totalDays} days collected ({Math.round(data.collected / data.totalDays * 100)}%)
                </p>
                <div className="w-full bg-gray-200 rounded-full h-3 mt-2">
                    <div className="bg-purple-600 h-3 rounded-full transition-all" style={{ width: `${(data.collected / data.totalDays * 100)}%` }}></div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {monthNames.map((month, mi) => {
                    const monthNum = String(mi + 1).padStart(2, '0');
                    const days = daysInMonth[mi];
                    // Get day of week for first day of month (use 2024 as a leap year reference)
                    const firstDow = new Date(2024, mi, 1).getDay();
                    const collected = Array.from({ length: days }, (_, di) => {
                        const key = `${monthNum}-${String(di + 1).padStart(2, '0')}`;
                        return (data.byDay[key] || []).length > 0 ? 1 : 0;
                    }).reduce((a, b) => a + b, 0);

                    return (
                        <div key={month} className="bg-gray-50 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                                <div className="text-sm font-bold text-gray-700">{month}</div>
                                <div className="text-xs text-gray-500">{collected}/{days}</div>
                            </div>
                            <div className="grid grid-cols-7 gap-0.5 text-center">
                                {['S','M','T','W','T','F','S'].map((d, i) => (
                                    <div key={`hdr-${i}`} className="text-[10px] font-medium text-gray-400 py-0.5">{d}</div>
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
                                    const hasPlayers = players.length > 0;
                                    const count = players.length;
                                    return (
                                        <button
                                            key={key}
                                            onClick={() => hasPlayers && setSelectedDay(isSelected ? null : key)}
                                            className={`aspect-square flex items-center justify-center rounded text-xs font-medium transition-all ${
                                                isToday ? 'ring-2 ring-yellow-400 ' : ''
                                            }${
                                                isSelected ? 'bg-purple-600 text-white' :
                                                count >= 10 ? 'bg-purple-500 text-white cursor-pointer' :
                                                count >= 5 ? 'bg-purple-300 text-purple-900 cursor-pointer' :
                                                hasPlayers ? 'bg-purple-100 text-purple-800 hover:bg-purple-200 cursor-pointer' :
                                                'text-gray-400'
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
                    <div className="bg-white rounded-lg shadow-2xl max-w-md w-full max-h-[70vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b bg-purple-600 text-white rounded-t-lg flex items-center justify-between">
                            <h3 className="font-bold">
                                {monthNames[parseInt(selectedDay.split('-')[0]) - 1]} {parseInt(selectedDay.split('-')[1])} — {data.byDay[selectedDay].length} player{data.byDay[selectedDay].length > 1 ? 's' : ''}
                            </h3>
                            <button onClick={() => setSelectedDay(null)} className="text-white hover:text-gray-200 text-xl leading-none">&times;</button>
                        </div>
                        <div className="p-4 space-y-2">
                            {data.byDay[selectedDay]
                                .filter((p, i, arr) => arr.findIndex(x => x.playerId === p.playerId) === i)
                                .sort((a, b) => (a.birthDate || '').localeCompare(b.birthDate || ''))
                                .map((p, i) => (
                                <div key={`${p.playerId}-${i}`} className="flex items-center justify-between bg-gray-50 rounded p-2">
                                    <PlayerLink playerId={p.playerId} name={p.name} />
                                    <span className="text-xs text-gray-400">{p.birthDate}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
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
    return <span className="text-gray-500 italic small-text">Defensive replacement</span>;
};

const PersonalRecords = ({ data }) => {
    // Render the categorized summary stats directly (extracted from SmartInsights 'records' view)
    const gameMap = useMemo(() => {
        const map = {};
        (data.games || []).forEach(game => { if (game.gameId) map[game.gameId] = game; });
        return map;
    }, [data.games]);

    const categoryConfig = {
        'Game Format': { icon: '🎮', gradient: 'from-emerald-500 to-green-600' },
        'Hitting': { icon: '🏏', gradient: 'from-orange-500 to-amber-600' },
        'Pitching': { icon: '⚾', gradient: 'from-blue-500 to-indigo-600' },
        'Home Runs': { icon: '💣', gradient: 'from-red-500 to-pink-600' },
        'Runs Scored': { icon: '🏃', gradient: 'from-purple-500 to-violet-600' },
        'Defense': { icon: '🧤', gradient: 'from-teal-500 to-cyan-600' },
        'Baserunning': { icon: '👟', gradient: 'from-lime-500 to-green-600' },
        'Other': { icon: '📌', gradient: 'from-gray-500 to-gray-600' }
    };

    const categories = useMemo(() => {
        const cats = { 'Game Format': [], 'Hitting': [], 'Pitching': [], 'Home Runs': [], 'Runs Scored': [], 'Defense': [], 'Baserunning': [], 'Other': [] };
        (data.summary || []).forEach(row => {
            const r = row.record.toLowerCase();
            if (r.includes('extra inning') || r.includes('doubleheader') || r.includes('game length') || r.includes('attendance') || r.includes('longest') || r.includes('shortest') || r.includes('1-run game') || r.includes('1-0 game') || r.includes('temperature') || r.includes('coldest') || r.includes('hottest') || r.includes('wind') || r.includes('precipitation') || r.includes('start time') || r.includes('day game') || r.includes('weekend') || r.includes('biggest victory') || r.includes('comeback') || r.includes('matchup')) cats['Game Format'].push(row);
            else if (r.includes('hr') || r.includes('home run') || r.includes('grand slam') || r.includes('multi-hr') || r.includes('inside-the-park') || r.includes('back-to-back')) cats['Home Runs'].push(row);
            else if ((r.includes('hit') && !r.includes('pitcher') && !r.includes('shutout')) || r.includes('batting') || r.includes('cycle') || r.includes('average leader') || r.includes('obp leader') || r.includes('ops leader') || r.includes('unique player') || r.includes('risp') || r.includes('bases loaded') || r.includes('wpa') || r.includes('clutch') || r.includes('rbi')) cats['Hitting'].push(row);
            else if (r.includes('pitch') || r.includes('strikeout') || r.includes('combined strikeout') || r.includes(' k ') || r.includes('shutout') || r.includes('complete game') || r.includes('quality start') || r.includes('earned run') || r.includes('no-hit') || r.includes('walk') || r.includes('era leader') || r.includes('unique pitcher') || r.includes('win') || r.includes('loss') || r.includes('save')) cats['Pitching'].push(row);
            else if (r.includes('run') || r.includes('10+ run')) cats['Runs Scored'].push(row);
            else if (r.includes('fewest') || r.includes('error') || r.includes('defense')) cats['Defense'].push(row);
            else if (r.includes('steal') || r.includes(' sb') || r.includes('caught') || r.includes('baserun')) cats['Baserunning'].push(row);
            else cats['Other'].push(row);
        });
        return cats;
    }, [data.summary]);

    return (
        <div className="space-y-4">
            {Object.entries(categories).map(([name, records]) => {
                if (records.length === 0) return null;
                const config = categoryConfig[name];
                return (
                    <div key={name} className="bg-white rounded-xl shadow overflow-hidden">
                        <details open>
                            <summary className={`cursor-pointer p-4 bg-gradient-to-r ${config.gradient} text-white hover:opacity-95`}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xl">{config.icon}</span>
                                        <span className="font-bold body-text">{name}</span>
                                    </div>
                                    <span className="bg-white/20 px-2 py-0.5 rounded text-sm">{records.length}</span>
                                </div>
                            </summary>
                            <div className="divide-y">
                                {records.map((record, i) => (
                                    <div key={i} className="p-3 hover:bg-gray-50">
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="font-semibold body-text text-gray-800">{record.record}</div>
                                            <div className="font-bold text-blue-600 whitespace-nowrap">{record.value}</div>
                                        </div>
                                        {record.detail && <div className="small-text text-gray-600 mt-1">{record.detail}</div>}
                                        {record.score && <div className="small-text text-gray-500 mt-0.5">{record.score}</div>}
                                    </div>
                                ))}
                            </div>
                        </details>
                    </div>
                );
            })}
        </div>
    );
};

const SpecialTab = ({ data }) => {
    const [view, setView] = useState('records');
    return (
        <div>
            <SubNav tabs={[
                { id: 'records', label: 'Records' },
                { id: 'debuts', label: 'Debuts' },
                { id: 'finals', label: 'Final Games' },
                { id: 'splash', label: 'Signature HRs' },
            ]} active={view} onChange={setView} />
            {view === 'records' && <PersonalRecords data={data} />}
            {view === 'debuts' && (
                <DataTable title="🌟 MLB Debuts" data={data.debuts || []} defaultSortKey="date" enableDateFilter={true} columns={[
                    { key: 'date', label: 'Date' }, { key: 'player', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                    { key: 'team', label: 'Team' }, { key: 'opponent', label: 'vs' }, { key: 'position', label: 'Pos' },
                    { key: 'stats', label: 'Debut Performance', render: (v, r) => <DebutPerformance r={r} /> },
                    { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                ]} />
            )}
            {view === 'finals' && (
                <DataTable title="👋 Final MLB Games" data={data.finalGames || []} defaultSortKey="date" enableDateFilter={true} columns={[
                    { key: 'date', label: 'Date' }, { key: 'player', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                    { key: 'team', label: 'Team' }, { key: 'position', label: 'Pos' },
                    { key: 'stats', label: 'Final Performance', render: (v, r) => <DebutPerformance r={r} /> },
                    { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                ]} />
            )}
            {view === 'splash' && (
                <DataTable title="💦 Signature HRs" data={data.signatureHRs || []} defaultSortKey="date" enableDateFilter={true} columns={[
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
            const nums = score.match(/\\d+/g);
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
        <div className="bg-white rounded-lg shadow p-6">
            <div className="mb-4">
                <h2 className="section-title font-bold">Personal Scorigami</h2>
                <p className="body-text text-gray-500 mt-1">{data.unique} unique final scores witnessed</p>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full border-collapse" style={{ tableLayout: 'fixed' }}>
                    <thead>
                        <tr>
                            <th className="p-0 text-xs text-gray-500 text-center" style={{width:'30px'}}></th>
                            {Array.from({ length: data.displayMaxWinner + 1 }, (_, i) => (
                                <th key={i} className="p-0 text-xs text-gray-500 text-center">{i}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {Array.from({ length: data.displayMaxLoser + 1 }, (_, loser) => (
                            <tr key={loser}>
                                <td className="p-0 text-xs text-gray-500 text-center font-medium" style={{width:'30px'}}>{loser}</td>
                                {Array.from({ length: data.displayMaxWinner + 1 }, (_, winner) => {
                                    if (winner <= loser) {
                                        return <td key={winner} className="p-px"><div className="w-full aspect-square bg-gray-200 rounded-sm"></div></td>;
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
                                                    'bg-white border border-gray-200'
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
                <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span>Losing score ↓</span>
                    <span>Winning score →</span>
                    <div className="flex items-center gap-1 ml-4">
                        <div className="w-3 h-3 bg-white border border-gray-200 rounded-sm"></div> <span>0</span>
                        <div className="w-3 h-3 bg-green-100 rounded-sm ml-1"></div> <span>1</span>
                        <div className="w-3 h-3 bg-green-300 rounded-sm ml-1"></div> <span>2</span>
                        <div className="w-3 h-3 bg-green-400 rounded-sm ml-1"></div> <span>3-4</span>
                        <div className="w-3 h-3 bg-green-600 rounded-sm ml-1"></div> <span>5+</span>
                    </div>
                </div>
            </div>

            {selectedCell && data.scoreGames[selectedCell] && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedCell(null)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-lg w-full max-h-[70vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b bg-green-600 text-white rounded-t-lg flex items-center justify-between">
                            <h3 className="font-bold">Final Score: {selectedCell.replace('-', ' - ')} ({data.scoreGames[selectedCell].length} game{data.scoreGames[selectedCell].length > 1 ? 's' : ''})</h3>
                            <button onClick={() => setSelectedCell(null)} className="text-white hover:text-gray-200 text-xl leading-none">&times;</button>
                        </div>
                        <div className="p-3 space-y-2">
                            {data.scoreGames[selectedCell].map((g, i) => (
                                <div key={i} className="bg-gray-50 rounded p-3">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-green-700">{g.winnerTeam} {g.winnerScore}</span>
                                            <span className="text-gray-400">def.</span>
                                            <span className="text-gray-600">{g.loserTeam} {g.loserScore}</span>
                                        </div>
                                        <span className="text-xs text-gray-500">{g.date}</span>
                                    </div>
                                    <div className="text-xs text-gray-400 mt-1">{g.awayTeam} @ {g.homeTeam} • {g.venue || ''}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const TriviaTab = ({ umpireLog, jerseyLog, playerBios, players, pitchers, games }) => {
    const [view, setView] = useState('jerseys');
    const allPlayers = useMemo(() => [...(players || []), ...(pitchers || [])], [players, pitchers]);
    return (
        <div>
            <SubNav tabs={[
                { id: 'jerseys', label: 'Jersey Numbers' },
                { id: 'origins', label: 'Origins' },
                { id: 'birthdays', label: 'Birthdays' },
                { id: 'scorigami', label: 'Scorigami' },
                { id: 'umpires', label: 'Umpires' },
            ]} active={view} onChange={setView} />
            {view === 'jerseys' && <JerseyCollection jerseyLog={jerseyLog} />}
            {view === 'origins' && <PlayerOrigins playerBios={playerBios} allPlayers={allPlayers} />}
            {view === 'birthdays' && <PlayerBirthdays playerBios={playerBios} allPlayers={allPlayers} />}
            {view === 'scorigami' && <ScorigamiChart games={games} />}
            {view === 'umpires' && <UmpireTracker umpireLog={umpireLog} />}
        </div>
    );
};

// Reusable subtab navigation
const SubNav = ({ tabs, active, onChange }) => (
    <div className="bg-white rounded-lg shadow mb-4">
        <div className="flex flex-wrap gap-1 p-2">
            {tabs.map(t => (
                <button key={t.id} onClick={() => onChange(t.id)} className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    active === t.id
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}>
                    {t.label}
                </button>
            ))}
        </div>
    </div>
);

// === MERGED TAB WRAPPERS ===

// Players tab: absorbs Leaderboards
const PlayersTabV2 = ({ data }) => {
    const hasCollegeData = Object.keys(data.ncaaCrossRef || {}).length > 0;
    const [view, setView] = useState('hitters');

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
        ...(hasCollegeData ? [{ id: 'college', label: 'College' }] : []),
        { id: 'leaders', label: 'Leaderboards' },
    ];

    return (
        <div>
            <SubNav tabs={subtabs} active={view} onChange={setView} />
            {view === 'hitters' && <DynamicPlayerTable allPlayers={data.players || []} playerGames={data.playerGames || []} />}
            {view === 'pitchers' && <DynamicPitcherTable allPitchers={data.pitchers || []} pitcherGames={data.pitcherGames || []} />}
            {view === 'nostats' && <NoStatsPlayers data={data} />}
            {view === 'college' && <CollegePlayersView data={data} onViewPlayer={handleViewPlayer} />}
            {view === 'leaders' && (data.players?.length ? <Leaderboards data={data} /> : <EmptyState icon="🏅" title="No Player Data" message="No player statistics available." />)}
        </div>
    );
};

// Milestones tab: absorbs History
const MilestonesTabV2 = ({ data, onTabChange }) => {
    const [view, setView] = useState('milestones');
    return (
        <div>
            <SubNav tabs={[
                { id: 'milestones', label: 'Game Milestones' },
                { id: 'history', label: 'All-Time Passings' },
            ]} active={view} onChange={setView} />
            {view === 'milestones' && (data.milestones?.length ? <MilestonesView milestones={data.milestones} games={data.games || []} careerFirsts={data.careerFirsts || []} allTimePassings={data.allTimePassings || []} onTabChange={onTabChange} /> : <EmptyState icon="🏆" title="No Milestones" message="No milestones have been recorded yet." />)}
            {view === 'history' && <HistoryWitnessedView allTimePassings={data.allTimePassings || []} careerFirsts={data.careerFirsts || []} games={data.games || []} />}
        </div>
    );
};

// Venues tab: absorbs Calendar
const VenuesTab = ({ data }) => {
    const [view, setView] = useState('map');
    return (
        <div>
            <SubNav tabs={[
                { id: 'map', label: 'Map & Tables' },
                { id: 'calendar', label: 'Calendar' },
            ]} active={view} onChange={setView} />
            {view === 'map' && ((data.stadiums?.length || data.teams?.length) ? (
                <div className="space-y-6">
                    <StadiumMap stadiums={data.stadiums || []} games={data.games || []} orioles={data.orioles || []} />
                    <DataTable title="Teams" data={data.teams || []} defaultSortKey="games" columns={[
                        { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'record', label: 'Record' },
                        { key: 'runs', label: 'R' }, { key: 'runsAllowed', label: 'RA' }, { key: 'diff', label: 'Diff' },
                        { key: 'homeRecord', label: 'Home' }, { key: 'awayRecord', label: 'Away' },
                        { key: 'oneRunGames', label: '1-Run' }, { key: 'blowouts', label: 'Blowouts' }
                    ]} />
                    <DataTable title="Stadiums" data={data.stadiums || []} defaultSortKey="games" columns={[
                        { key: 'stadium', label: 'Stadium' }, { key: 'games', label: 'G' }, { key: 'firstVisit', label: 'First' },
                        { key: 'lastVisit', label: 'Last' }, { key: 'span', label: 'Span' }, { key: 'avgAttendance', label: 'Avg Att.' },
                        { key: 'homeRunsSeen', label: 'HRs' }, { key: 'hitsSeen', label: 'Hits' }, { key: 'strikeoutsSeen', label: 'SOs' },
                        { key: 'teamsSeen', label: 'Teams' }, { key: 'homeTeamRecord', label: 'Home Record' }
                    ]} />
                </div>
            ) : <EmptyState icon="🏟️" title="No Venue Data" message="No stadium or team records available." />)}
            {view === 'calendar' && (data.games?.length ? <Calendar games={data.games} /> : <EmptyState icon="📅" title="No Games" message="No games to display on the calendar." />)}
        </div>
    );
};

// Progress tab: absorbs Matchups
const ProgressTab = ({ data }) => {
    const [view, setView] = useState('checklist');
    return (
        <div>
            <SubNav tabs={[
                { id: 'checklist', label: 'Division Checklist' },
                { id: 'badges', label: 'Badges' },
                { id: 'matchups', label: 'Matchups' },
            ]} active={view} onChange={setView} />
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
    const [tab, setTab] = useState(() => {
        const hash = window.location.hash.slice(1);
        if (hash && VALID_TABS.has(hash)) return hash;
        if (hash && TAB_REDIRECTS[hash]) return TAB_REDIRECTS[hash];
        const saved = localStorage.getItem('baseballActiveTab');
        if (saved && VALID_TABS.has(saved)) return saved;
        if (saved && TAB_REDIRECTS[saved]) return TAB_REDIRECTS[saved];
        return 'dashboard';
    });
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
    const searchRef = useRef(null);

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
        if (window.location.hash.slice(1) !== tab) {
            history.replaceState(null, '', '#' + tab);
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [tab]);

    useEffect(() => {
        const onHashChange = () => {
            const hash = window.location.hash.slice(1);
            if (hash && VALID_TABS.has(hash)) setTab(hash);
            else if (hash && TAB_REDIRECTS[hash]) setTab(TAB_REDIRECTS[hash]);
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
        window.__navigateTab = (tabId) => { if (VALID_TABS.has(tabId)) setTab(tabId); else if (TAB_REDIRECTS[tabId]) setTab(TAB_REDIRECTS[tabId]); };
        return () => { window.__navigateTab = null; };
    }, []);

    // Scroll-to-top visibility
    useEffect(() => {
        const onScroll = () => setShowScrollTop(window.scrollY > 400);
        window.addEventListener('scroll', onScroll, { passive: true });
        return () => window.removeEventListener('scroll', onScroll);
    }, []);

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
        if (!data || !searchQuery || searchQuery.length < 2) return [];
        const q = searchQuery.toLowerCase();
        const results = [];
        const limit = 8;

        // Search players
        const seenPlayers = new Set();
        (data.playerGames || []).forEach(pg => {
            if (results.length >= limit) return;
            if (pg.name && pg.name.toLowerCase().includes(q) && !seenPlayers.has(pg.playerId)) {
                seenPlayers.add(pg.playerId);
                results.push({ type: 'player', label: pg.name, sub: pg.team || '', tab: 'players', id: pg.playerId });
            }
        });
        (data.pitcherGames || []).forEach(pg => {
            if (results.length >= limit) return;
            if (pg.name && pg.name.toLowerCase().includes(q) && !seenPlayers.has(pg.playerId)) {
                seenPlayers.add(pg.playerId);
                results.push({ type: 'pitcher', label: pg.name, sub: pg.team || '', tab: 'pitchers', id: pg.playerId });
            }
        });

        // Search games (by team name or date)
        const seenGames = new Set();
        (data.games || []).forEach(g => {
            if (results.length >= limit) return;
            const text = `${g.awayTeam || ''} ${g.homeTeam || ''} ${g.date || ''} ${g.venue || ''}`.toLowerCase();
            if (text.includes(q) && !seenGames.has(g.gameId)) {
                seenGames.add(g.gameId);
                results.push({ type: 'game', label: `${g.awayTeam} @ ${g.homeTeam}`, sub: g.date || '', tab: 'gamelog', id: g.gameId });
            }
        });

        // Search milestones
        (data.milestones || []).slice(0, 200).forEach(m => {
            if (results.length >= limit) return;
            const text = `${m.player || ''} ${m.type || ''} ${m.description || ''}`.toLowerCase();
            if (text.includes(q)) {
                results.push({ type: 'milestone', label: m.player || m.type, sub: m.description || m.type || '', tab: 'milestones' });
            }
        });

        return results;
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
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
                <div className="bg-white rounded-xl shadow-lg p-8 max-w-lg text-center">
                    <h2 className="text-xl font-bold text-gray-800 mb-4">{isFileProtocol ? 'Local File Access' : 'Failed to Load Data'}</h2>
                    {isFileProtocol ? (
                        <div className="text-left text-gray-600 space-y-3">
                            <p>This page needs a local server to load data. Run one of these from the folder containing this file:</p>
                            <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">python3 -m http.server 8000</pre>
                            <p>Then open <a href="http://localhost:8000" className="text-blue-600 underline">http://localhost:8000</a></p>
                        </div>
                    ) : (
                        <p className="text-gray-600">{loadError}</p>
                    )}
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
                <div className="text-center">
                    <div className="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full" style={{ animation: 'spin 1s linear infinite' }}></div>
                    <p className="mt-4 text-lg font-medium text-gray-600">Loading baseball data...</p>
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
        <div className={`min-h-screen transition-colors duration-200 ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
            <header className={`${darkMode ? 'bg-gray-800 border-b border-gray-700' : 'bg-white border-b border-gray-200'}`}>
                <div className="max-w-7xl mx-auto px-4 py-3 sm:py-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                    <div>
                        <h1 className={`text-lg sm:text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Baseball Statistics Portal</h1>
                        <p className={`text-xs mt-0.5 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{data.games?.length || 0} games attended • {(data.players?.length || 0) + (data.pitchers?.length || 0)} players seen</p>
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
                                className={`w-full sm:w-48 md:w-64 px-3 py-2 rounded-lg text-sm transition-colors border ${darkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-blue-500' : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:border-blue-500'} outline-none`}
                            />
                            {searchOpen && searchResults.length > 0 && (
                                <div className={`absolute top-full right-0 mt-1 w-80 rounded-lg shadow-xl border z-[60] max-h-96 overflow-y-auto ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                                    {searchResults.map((r, i) => (
                                        <button key={`search-${r.type}-${r.id || r.label}-${i}`} onClick={() => { setTab(r.tab); setSearchQuery(''); setSearchOpen(false); }}
                                            className={`w-full text-left px-4 py-2 flex items-center gap-3 transition-colors ${darkMode ? 'hover:bg-gray-700 text-gray-200' : 'hover:bg-blue-50 text-gray-800'}`}>
                                            <span className="text-xs font-medium uppercase opacity-50 w-14 shrink-0">{r.type}</span>
                                            <div className="min-w-0">
                                                <div className="text-sm font-medium truncate">{r.label}</div>
                                                {r.sub && <div className={`text-xs truncate ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{r.sub}</div>}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className={`px-3 py-2 rounded-lg transition-colors border ${darkMode ? 'bg-gray-700 border-gray-600 hover:bg-gray-600 text-white' : 'bg-gray-50 border-gray-300 hover:bg-gray-100 text-gray-700'}`}
                            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            {darkMode ? '☀️' : '🌙'}
                        </button>
                    </div>
                </div>
            </header>
            <nav className={`shadow-md sticky top-0 z-50 border-b-2 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-blue-100'}`}>
                <div className="max-w-7xl mx-auto px-2 sm:px-4 relative">
                    <div className="flex overflow-x-auto scrollbar-hide" role="tablist" aria-label="Main navigation" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}>
                        {tabs.map(t => (
                            <button key={t.id} role="tab" aria-selected={tab === t.id} aria-current={tab === t.id ? 'page' : undefined} onClick={() => setTab(t.id)} className={`px-3 sm:px-5 py-2.5 sm:py-3 font-medium text-xs sm:text-sm whitespace-nowrap transition-all flex-shrink-0 ${
                                tab === t.id
                                    ? (darkMode ? 'text-blue-400 border-b-[3px] border-blue-400' : 'text-blue-600 border-b-[3px] border-blue-600 font-semibold')
                                    : (darkMode ? 'text-gray-400 hover:text-gray-200 border-b-[3px] border-transparent' : 'text-gray-500 hover:text-gray-900 border-b-[3px] border-transparent')
                            }`}>
                                {t.label}
                            </button>
                        ))}
                    </div>
                </div>
            </nav>
            <main role="tabpanel" className="max-w-7xl mx-auto px-2 sm:px-4 py-4 sm:py-8">
                {tab === 'dashboard' && <Dashboard data={data} onTabChange={setTab} />}
                {tab === 'gamelog' && (data.games?.length ? <GameLogWithDetails games={data.games} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} careerFirstsByGame={data.careerFirstsByGame || {}} allTimePassingsByGame={data.allTimePassingsByGame || {}} /> : <EmptyState icon="📋" title="No Games" message="Add game HTML files to the Current Season Games folder and run the processor." />)}
                {tab === 'players' && <PlayersTabV2 data={data} />}
                {tab === 'milestones' && <MilestonesTabV2 data={data} onTabChange={setTab} />}
                {tab === 'venues' && <VenuesTab data={data} />}
                {tab === 'progress' && <ProgressTab data={data} />}
                {tab === 'special' && <SpecialTab data={data} />}
                {tab === 'trivia' && <TriviaTab umpireLog={data.umpireLog || []} jerseyLog={data.jerseyLog || {}} playerBios={data.playerBios || {}} players={data.players || []} pitchers={data.pitchers || []} games={data.games || []} />}
                {tab === 'companions' && <CompanionsView companionData={data.companionData} />}
                {tab === 'orioles' && <OriolesDashboard orioles={data.orioles || []} games={data.games || []} />}
            </main>
            <footer className={`border-t mt-8 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                <div className="max-w-7xl mx-auto px-4 py-6 text-center">
                    <p className={`small-text ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                        Baseball Statistics Portal{data.generatedAt ? ` • Updated ${data.generatedAt}` : ''}
                    </p>
                </div>
            </footer>
            {showScrollTop && (
                <button
                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                    className={`fixed bottom-6 right-6 w-10 h-10 rounded-full shadow-lg flex items-center justify-center transition-all z-50 ${darkMode ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
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