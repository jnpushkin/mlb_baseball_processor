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
                doubles: 0, triples: 0, sb: 0, cs: 0, bb: 0, so: 0, hbp: 0, gidp: 0
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
    });
    
    return Object.values(grouped).map(p => {
        const singles = p.h - p.doubles - p.triples - p.hr;
        const tb = singles + (p.doubles * 2) + (p.triples * 3) + (p.hr * 4);
        const xbh = p.doubles + p.triples + p.hr;
        const avg = p.ab > 0 ? (p.h / p.ab).toFixed(3) : '0.000';
        const obp = p.pa > 0 ? ((p.h + p.bb + p.hbp) / p.pa).toFixed(3) : '0.000';
        const slg = p.ab > 0 ? (tb / p.ab).toFixed(3) : '0.000';
        const ops = (parseFloat(obp) + parseFloat(slg)).toFixed(3);
        
        return {
            ...p,
            team: Array.from(p.teams).join(', '),
            tb, xbh, avg, obp, slg, ops
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
                outs: 0, h: 0, r: 0, er: 0, bb: 0, so: 0, hr: 0
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
    });
    
    return Object.values(grouped).map(p => {
        const innings = p.outs / 3;
        const ip = `${Math.floor(innings)}.${p.outs % 3}`;
        const era = innings > 0 ? ((p.er * 9) / innings).toFixed(2) : 'N/A';
        const whip = innings > 0 ? ((p.h + p.bb) / innings).toFixed(3) : 'N/A';
        
        return {
            ...p,
            team: Array.from(p.teams).join(', '),
            ip, era, whip
        };
    });
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

const PlayerLink = ({ playerId, name }) => {
    if (!playerId || playerId === 'UNKNOWN') return <span>{name}</span>;
    const firstLetter = playerId.charAt(0).toLowerCase();
    const url = `https://www.baseball-reference.com/players/${firstLetter}/${playerId}.shtml`;
    return <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{name}</a>;
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

const LoadingSpinner = ({ size = 'md', text = 'Loading...' }) => {
    const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
    return (
        <div className="flex flex-col items-center justify-center p-8">
            <div className={`${sizes[size]} border-4 border-blue-200 border-t-blue-600 rounded-full`}
                 style={{ animation: 'spin 1s linear infinite' }}></div>
            {text && <p className="mt-3 body-text text-gray-500">{text}</p>}
        </div>
    );
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

const StatCard = ({ title, value, subtitle, color = 'blue' }) => {
    const colors = {
        blue: 'border-blue-200 bg-blue-50', green: 'border-green-200 bg-green-50',
        purple: 'border-purple-200 bg-purple-50', orange: 'border-orange-200 bg-orange-50'
    };
    return (
        <div className={`bg-white rounded-lg shadow border-l-4 ${colors[color]} p-6 hover:shadow-lg transition-all`}>
            <h3 className="small-text font-medium text-gray-600 mb-2">{title}</h3>
            <p className="text-3xl font-bold text-gray-900">{value}</p>
            {subtitle && <p className="body-text text-gray-500 mt-1">{subtitle}</p>}
        </div>
    );
};

const PlayerComparison = ({ players, playerGames }) => {
    const [selectedPlayers, setSelectedPlayers] = useState([]);
    const [comparisonStats, setComparisonStats] = useState([]);
    const chartRef = useRef(null);
    const chartInstance = useRef(null);
    
    const aggregatedPlayers = useMemo(() => players || [], [players]);
    
    useEffect(() => {
        if (selectedPlayers.length > 0) {
            const stats = selectedPlayers.map(playerId => 
                aggregatedPlayers.find(p => p.playerId === playerId)
            ).filter(Boolean);
            setComparisonStats(stats);
        } else {
            setComparisonStats([]);
        }
    }, [selectedPlayers, aggregatedPlayers]);
    
    useEffect(() => {
        if (comparisonStats.length === 0 || !chartRef.current) return;
        
        // Destroy previous chart
        if (chartInstance.current) {
            chartInstance.current.destroy();
        }
        
        const ctx = chartRef.current.getContext('2d');
        const colors = [
            { border: 'rgb(59, 130, 246)', bg: 'rgba(59, 130, 246, 0.2)' },
            { border: 'rgb(239, 68, 68)', bg: 'rgba(239, 68, 68, 0.2)' },
            { border: 'rgb(34, 197, 94)', bg: 'rgba(34, 197, 94, 0.2)' }
        ];
        
        chartInstance.current = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['AVG', 'OBP', 'SLG', 'HR', 'RBI'],
                datasets: comparisonStats.map((player, idx) => ({
                    label: player.name,
                    data: [
                        parseFloat(player.avg) * 1000,      // .300 → 300
                        parseFloat(player.obp) * 1000,      // .380 → 380
                        parseFloat(player.slg) * 1000,      // .450 → 450
                        player.hr * 20,                      // 25 HR → 500
                        player.rbi * 7                       // 80 RBI → 560
                    ],
                    backgroundColor: colors[idx].bg,
                    borderColor: colors[idx].border,
                    pointBackgroundColor: colors[idx].border,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: colors[idx].border
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 800,
                        ticks: { 
                            backdropColor: 'transparent',
                            stepSize: 200
                        }
                    }
                },
                plugins: {
                    legend: { position: 'top' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const dataIndex = context.dataIndex;
                                const player = comparisonStats[context.datasetIndex];
                                
                                // Show actual values in tooltips
                                let value;
                                switch(dataIndex) {
                                    case 0: value = player.avg; break;
                                    case 1: value = player.obp; break;
                                    case 2: value = player.slg; break;
                                    case 3: value = `${player.hr} HR`; break;
                                    case 4: value = `${player.rbi} RBI`; break;
                                    default: value = context.parsed.r;
                                }
                                
                                return `${label}: ${value}`;
                            }
                        }
                    }
                }
            }
        });
        
        return () => {
            if (chartInstance.current) {
                chartInstance.current.destroy();
            }
        };
    }, [comparisonStats]);

    const handlePlayerToggle = (playerId) => {
        setSelectedPlayers(prev => {
            if (prev.includes(playerId)) {
                return prev.filter(id => id !== playerId);
            } else if (prev.length < 3) {
                return [...prev, playerId];
            }
            return prev;
        });
    };
    
    return (
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
                <h2 className="section-title font-bold">⚖️ Player Comparison</h2>
                <p className="body-text text-gray-500 mt-1">Select up to 3 players to compare (minimum 10 PA)</p>
            </div>
            
            <div className="p-4">
                {/* Player selection grid */}
                <div className="mb-6">
                    <label className="body-text font-semibold mb-2 block">Select Players:</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-64 overflow-y-auto border rounded p-2">
                        {aggregatedPlayers
                            .filter(p => p.pa >= 10)
                            .sort((a, b) => b.pa - a.pa)
                            .map(p => (
                                <label 
                                    key={p.playerId} 
                                    className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-50 ${
                                        selectedPlayers.includes(p.playerId) ? 'bg-blue-50 border-2 border-blue-500' : 'border-2 border-transparent'
                                    }`}
                                >
                                    <input
                                        type="checkbox"
                                        checked={selectedPlayers.includes(p.playerId)}
                                        onChange={() => handlePlayerToggle(p.playerId)}
                                        disabled={!selectedPlayers.includes(p.playerId) && selectedPlayers.length >= 3}
                                        className="rounded"
                                    />
                                    <div className="small-text">
                                        <div className="font-semibold">{p.name}</div>
                                        <div className="text-gray-500">{p.team} • {p.pa} PA</div>
                                    </div>
                                </label>
                            ))
                        }
                    </div>
                </div>
                
                {comparisonStats.length > 0 && (
                    <>
                        {/* Side-by-side stats table */}
                        <div className="overflow-x-auto mb-6">
                            <table className="w-full">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-2 text-left small-text font-bold">Stat</th>
                                        {comparisonStats.map(p => (
                                            <th key={p.playerId} className="px-4 py-2 text-center body-text font-bold">
                                                <div>{p.name}</div>
                                                <div className="small-text text-gray-500 font-normal">{p.team}</div>
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {[
                                        { key: 'games', label: 'Games', format: v => v },
                                        { key: 'pa', label: 'PA', format: v => v },
                                        { key: 'ab', label: 'AB', format: v => v },
                                        { key: 'avg', label: 'AVG', format: v => v },
                                        { key: 'obp', label: 'OBP', format: v => v },
                                        { key: 'slg', label: 'SLG', format: v => v },
                                        { key: 'ops', label: 'OPS', format: v => v },
                                        { key: 'h', label: 'Hits', format: v => v },
                                        { key: 'hr', label: 'HR', format: v => v },
                                        { key: 'rbi', label: 'RBI', format: v => v },
                                        { key: 'r', label: 'Runs', format: v => v },
                                        { key: 'doubles', label: '2B', format: v => v },
                                        { key: 'triples', label: '3B', format: v => v },
                                        { key: 'sb', label: 'SB', format: v => v },
                                        { key: 'bb', label: 'BB', format: v => v },
                                        { key: 'so', label: 'SO', format: v => v },
                                    ].map(({ key, label, format }) => {
                                        const values = comparisonStats.map(p => parseFloat(String(p[key]).replace(/[^0-9.-]/g, '')) || 0);
                                        const maxVal = Math.max(...values);
                                        const minVal = Math.min(...values);
                                        
                                        return (
                                            <tr key={key}>
                                                <td className="px-4 py-2 body-text font-semibold">{label}</td>
                                                {comparisonStats.map(p => {
                                                    const val = p[key];
                                                    const numVal = parseFloat(String(val).replace(/[^0-9.-]/g, '')) || 0;
                                                    const isMax = numVal === maxVal && comparisonStats.length > 1;
                                                    const isMin = numVal === minVal && comparisonStats.length > 1 && key === 'so';
                                                    
                                                    return (
                                                        <td 
                                                            key={p.playerId} 
                                                            className={`px-4 py-2 text-center body-text ${
                                                                (isMax) ? 'bg-green-100 font-bold' : ''
                                                            }`}
                                                        >
                                                            {format(val)}
                                                        </td>
                                                    );
                                                })}
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                        
                        {/* Radar chart */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h3 className="subsection-title font-bold mb-4 text-center">Performance Radar</h3>
                            <div style={{ height: '400px' }}>
                                <canvas ref={chartRef} />
                            </div>
                        </div>
                    </>
                )}
                
                {selectedPlayers.length === 0 && (
                    <div className="text-center py-12 text-gray-500 body-text">
                        Select players above to begin comparison
                    </div>
                )}
            </div>
        </div>
    );
};

const GameDetailsModal = ({ game, playerGames, pitcherGames, careerFirsts, onClose }) => {
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
            bb: acc.bb + p.bb,
            so: acc.so + p.so
        }), { ab: 0, h: 0, r: 0, rbi: 0, hr: 0, bb: 0, so: 0 });
        
        const awayHittingTotals = awayHitters.reduce((acc, p) => ({
            ab: acc.ab + p.ab,
            h: acc.h + p.h,
            r: acc.r + p.r,
            rbi: acc.rbi + p.rbi,
            hr: acc.hr + p.hr,
            bb: acc.bb + p.bb,
            so: acc.so + p.so
        }), { ab: 0, h: 0, r: 0, rbi: 0, hr: 0, bb: 0, so: 0 });
        
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
            <td className="px-2 py-2 text-center">{player.ab}</td>
            <td className="px-2 py-2 text-center font-semibold">{player.h}</td>
            <td className="px-2 py-2 text-center">{player.r}</td>
            <td className="px-2 py-2 text-center">{player.rbi}</td>
            <td className="px-2 py-2 text-center font-bold text-blue-600">{player.hr > 0 ? player.hr : '-'}</td>
            <td className="px-2 py-2 text-center">{player.doubles > 0 ? player.doubles : '-'}</td>
            <td className="px-2 py-2 text-center">{player.triples > 0 ? player.triples : '-'}</td>
            <td className="px-2 py-2 text-center">{player.bb}</td>
            <td className="px-2 py-2 text-center">{player.so}</td>
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
                <td className="px-2 py-2 text-center">{pitcher.h}</td>
                <td className="px-2 py-2 text-center">{pitcher.r}</td>
                <td className="px-2 py-2 text-center">{pitcher.er}</td>
                <td className="px-2 py-2 text-center">{pitcher.bb}</td>
                <td className="px-2 py-2 text-center font-semibold">{pitcher.so}</td>
                <td className="px-2 py-2 text-center">{pitcher.hr > 0 ? pitcher.hr : '-'}</td>
            </tr>
        );
    };
    
    // Tab content components
    const BoxScoreTab = () => (
        <>
            {/* Away Team Hitters */}
            <div className="p-6 border-b bg-gray-50">
                <h4 className="subsection-title font-bold mb-3">{game.awayTeam} Batting</h4>
                <div className="overflow-x-auto">
                    <table className="w-full small-text">
                        <thead className="bg-white border-b-2">
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
                            {gameData.awayHitters.map((p, idx) => <HitterRow key={idx} player={p} />)}
                            <tr className="bg-blue-50 font-bold">
                                <td className="px-3 py-2">Team Totals</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.ab}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.h}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.r}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.rbi}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.hr}</td>
                                <td className="px-2 py-2 text-center">-</td>
                                <td className="px-2 py-2 text-center">-</td>
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
                            {gameData.homeHitters.map((p, idx) => <HitterRow key={idx} player={p} />)}
                            <tr className="bg-blue-50 font-bold">
                                <td className="px-3 py-2">Team Totals</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.ab}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.h}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.r}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.rbi}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.hr}</td>
                                <td className="px-2 py-2 text-center">-</td>
                                <td className="px-2 py-2 text-center">-</td>
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
                                    {gameData.awayPitchers.map((p, idx) => <PitcherRow key={idx} pitcher={p} />)}
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
                                    {gameData.homePitchers.map((p, idx) => <PitcherRow key={idx} pitcher={p} />)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
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
                            {lineup.sort((a, b) => a.slot - b.slot).map((player, idx) => (
                                <tr key={idx} className="hover:bg-blue-50">
                                    <td className="px-3 py-2 text-center font-bold text-blue-600">{player.slot}</td>
                                    <td className="px-3 py-2">
                                        <PlayerLink playerId={player.playerId} name={player.name} />
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
                        <div key={idx} className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-blue-400 hover:shadow-md transition-all">
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
                    {sortedInnings.map((inning, idx) => (
                        <div key={idx} className="bg-white rounded-lg shadow-sm overflow-hidden">
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
                                    <div key={playIdx} className={`p-3 hover:bg-blue-50 ${
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="section-title font-bold">{game.awayTeam} @ {game.homeTeam}</h3>
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
                    {(game.weather || game.temperature) && (
                        <div className="body-text text-blue-100 mt-1">
                            {game.weather && <span>🌤️ {game.weather}</span>}
                            {game.temperature && <span> • 🌡️ {game.temperature}°F</span>}
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
                
                {/* Game Context Section */}
                <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50 overflow-y-auto max-h-[40vh]">
                    {/* Linescore */}
                    {game.linescore && (
                        <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
                            <h5 className="small-text font-bold mb-3 text-gray-700">📊 Line Score</h5>
                            <div className="overflow-x-auto">
                                <table className="w-full text-center small-text">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-3 py-2 text-left">Team</th>
                                            {Array.from({ length: Math.max(game.linescore.away?.innings?.length || 9, game.linescore.home?.innings?.length || 9, 9) }, (_, i) => (
                                                <th key={i} className="px-2 py-2 w-8">{i + 1}</th>
                                            ))}
                                            <th className="px-3 py-2 font-bold border-l-2">R</th>
                                            <th className="px-3 py-2 font-bold">H</th>
                                            <th className="px-3 py-2 font-bold">E</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="border-b">
                                            <td className="px-3 py-2 text-left font-semibold">{game.awayTeam}</td>
                                            {Array.from({ length: Math.max(game.linescore.away?.innings?.length || 9, game.linescore.home?.innings?.length || 9, 9) }, (_, i) => (
                                                <td key={i} className="px-2 py-2">
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
                                                <td key={i} className="px-2 py-2">
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
                                    <div key={idx} className="flex items-start gap-2 p-2 bg-orange-50 rounded border-l-4 border-orange-400">
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
                                        <div key={idx} className="bg-white rounded-lg p-3 shadow-sm border-l-4 border-purple-400">
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
                                    <div key={idx} className="bg-white rounded-lg p-3 shadow-sm border-l-4 border-amber-400">
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
                <div className="border-b bg-gray-50">
                    <div className="flex gap-1 px-6">
                        {['boxscore', 'lineups', 'substitutions', 'playbyplay'].map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-6 py-3 body-text font-semibold transition-all ${
                                    activeTab === tab 
                                        ? 'bg-white text-blue-600 border-b-4 border-blue-600' 
                                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                                }`}
                            >
                                {tab === 'boxscore' ? '📊 Box Score' :
                                 tab === 'lineups' ? '📋 Lineups' :
                                 tab === 'substitutions' ? '🔄 Substitutions' :
                                 '⚡ Play-by-Play'}
                            </button>
                        ))}
                    </div>
                </div>
                
                {/* Tab Content - Scrollable */}
                <div className="overflow-y-auto" style={{ maxHeight: 'calc(90vh - 500px)' }}>
                    {activeTab === 'boxscore' && <BoxScoreTab />}
                    {activeTab === 'lineups' && <LineupsTab />}
                    {activeTab === 'substitutions' && <SubstitutionsTab />}
                    {activeTab === 'playbyplay' && <PlayByPlayTab />}
                </div>
                
                {/* Footer */}
                <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
                    <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                    <button onClick={onClose} className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 body-text font-medium">
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

const PlayerTimeline = ({ playerId, playerName, playerGames }) => {
    const [activeView, setActiveView] = useState('timeline');
    const [sortKey, setSortKey] = useState('dateSort');
    const [sortDir, setSortDir] = useState('desc');

    // Get all games for this player
    const gamesForPlayer = useMemo(() => {
        return playerGames.filter(g => g.playerId === playerId).sort((a, b) => b.dateSort.localeCompare(a.dateSort));
    }, [playerId, playerGames]);

    const timelineData = useMemo(() => {
        if (gamesForPlayer.length === 0) return [];

        // Group by year
        const byYear = {};
        gamesForPlayer.forEach(game => {
            const year = game.dateSort.substring(0, 4);
            if (!byYear[year]) {
                byYear[year] = [];
            }
            byYear[year].push(game);
        });

        // Aggregate stats per year
        const yearlyStats = Object.entries(byYear).map(([year, games]) => {
            const aggregated = aggregateHitterStats(games)[0] || {};
            return { year, ...aggregated };
        }).sort((a, b) => a.year - b.year);

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
                                {sortedGameLog.map((game, idx) => {
                                    const isMultiHit = game.h >= 2;
                                    const isHR = game.hr > 0;
                                    return (
                                        <tr key={idx} className={`hover:bg-blue-50 ${isHR ? 'bg-orange-50' : isMultiHit ? 'bg-green-50' : ''}`}>
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
            
            {/* Career summary stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6 p-4 bg-blue-50 rounded-lg">
                {(() => {
                    const totals = timelineData.reduce((acc, season) => ({
                        games: acc.games + (season.games || 0),
                        pa: acc.pa + (season.pa || 0),
                        hr: acc.hr + (season.hr || 0),
                        rbi: acc.rbi + (season.rbi || 0),
                        h: acc.h + (season.h || 0)
                    }), { games: 0, pa: 0, hr: 0, rbi: 0, h: 0 });
                    
                    return (
                        <>
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
                        </>
                    );
                })()}
            </div>
            
            {/* Year-by-year timeline */}
            <div className="space-y-4">
                {timelineData.map((season, idx) => (
                    <div key={idx} className="relative pl-8 pb-4 border-l-2 border-blue-200 last:border-l-0">
                        <div className="absolute left-0 top-0 -ml-2.5 w-5 h-5 bg-blue-600 rounded-full border-2 border-white"></div>
                        <div className="bg-gray-50 rounded-lg p-4 hover:bg-blue-50 transition-colors">
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <span className="text-2xl font-bold text-blue-600">{season.year}</span>
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

const PitcherTimeline = ({ playerId, playerName, pitcherGames }) => {
    const [activeView, setActiveView] = useState('timeline');
    const [sortKey, setSortKey] = useState('dateSort');
    const [sortDir, setSortDir] = useState('desc');

    // Get all games for this pitcher
    const gamesForPitcher = useMemo(() => {
        return pitcherGames.filter(g => g.playerId === playerId).sort((a, b) => b.dateSort.localeCompare(a.dateSort));
    }, [playerId, pitcherGames]);

    const timelineData = useMemo(() => {
        if (gamesForPitcher.length === 0) return [];

        // Group by year
        const byYear = {};
        gamesForPitcher.forEach(game => {
            const year = game.dateSort.substring(0, 4);
            if (!byYear[year]) {
                byYear[year] = [];
            }
            byYear[year].push(game);
        });

        // Aggregate stats per year
        const yearlyStats = Object.entries(byYear).map(([year, games]) => {
            const aggregated = aggregatePitcherStats(games)[0] || {};
            return { year, ...aggregated };
        }).sort((a, b) => a.year - b.year);

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
                                {sortedGameLog.map((game, idx) => {
                                    const isWin = game.decision === 'W';
                                    const isQS = parseFloat(game.ip) >= 6 && game.er <= 3;
                                    const isHighSO = game.so >= 8;
                                    return (
                                        <tr key={idx} className={`hover:bg-blue-50 ${isWin ? 'bg-green-50' : ''} ${isQS ? 'bg-blue-50' : ''}`}>
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
                {timelineData.map((season, idx) => (
                    <div key={idx} className="relative pl-8 pb-4 border-l-2 border-purple-200 last:border-l-0">
                        <div className="absolute left-0 top-0 -ml-2.5 w-5 h-5 bg-purple-600 rounded-full border-2 border-white"></div>
                        <div className="bg-gray-50 rounded-lg p-4 hover:bg-purple-50 transition-colors">
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <span className="text-2xl font-bold text-purple-600">{season.year}</span>
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

const AdvancedFilters = ({ games, onFilterChange }) => {
    const [filters, setFilters] = useState({
        dateRange: { start: '', end: '' },
        teams: [],
        venues: [],
        dayOfWeek: [],
        homeAway: 'all',
        minScore: '',
        maxScore: '',
        extraInnings: false
    });
    
    const [showFilters, setShowFilters] = useState(false);
    
    const availableTeams = useMemo(() => {
        const teams = new Set();
        games.forEach(g => {
            teams.add(g.homeTeam);
            teams.add(g.awayTeam);
        });
        return Array.from(teams).sort();
    }, [games]);
    
    const availableVenues = useMemo(() => {
        const venues = new Set();
        games.forEach(g => venues.add(g.venue));
        return Array.from(venues).sort();
    }, [games]);
    
    const applyFilters = () => {
        const filtered = games.filter(game => {
            // Date range
            if (filters.dateRange.start) {
                const gameDate = new Date(game.date);
                const startDate = new Date(filters.dateRange.start);
                if (gameDate < startDate) return false;
            }
            if (filters.dateRange.end) {
                const gameDate = new Date(game.date);
                const endDate = new Date(filters.dateRange.end);
                if (gameDate > endDate) return false;
            }
            
            // Teams
            if (filters.teams.length > 0) {
                if (!filters.teams.includes(game.homeTeam) && !filters.teams.includes(game.awayTeam)) {
                    return false;
                }
            }
            
            // Venues
            if (filters.venues.length > 0) {
                if (!filters.venues.includes(game.venue)) return false;
            }
            
            // Day of week
            if (filters.dayOfWeek.length > 0) {
                const gameDate = new Date(game.date);
                const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                const gameDayName = dayNames[gameDate.getDay()];
                if (!filters.dayOfWeek.includes(gameDayName)) return false;
            }
            
            // Home/Away
            if (filters.homeAway !== 'all') {
                const favoriteTeam = 'BAL'; // You could make this configurable
                if (filters.homeAway === 'home' && game.homeTeam !== favoriteTeam) return false;
                if (filters.homeAway === 'away' && game.awayTeam !== favoriteTeam) return false;
            }
            
            // Score filters
            if (filters.minScore || filters.maxScore) {
                const cleanScore = game.score.replace(/\\s*\\(\\d+\\)\\s*$/, '');
                const scores = cleanScore.match(/\\d+/g);
                if (scores && scores.length === 2) {
                    const totalScore = parseInt(scores[0]) + parseInt(scores[1]);
                    if (filters.minScore && totalScore < parseInt(filters.minScore)) return false;
                    if (filters.maxScore && totalScore > parseInt(filters.maxScore)) return false;
                }
            }
            
            // Extra innings
            if (filters.extraInnings) {
                // Check if game went to extra innings (you might need to add this to your data)
                // For now, we'll skip this filter
            }
            
            return true;
        });
        
        onFilterChange(filtered);
    };
    
    const resetFilters = () => {
        const resetState = {
            dateRange: { start: '', end: '' },
            teams: [],
            venues: [],
            dayOfWeek: [],
            homeAway: 'all',
            minScore: '',
            maxScore: '',
            extraInnings: false
        };
        setFilters(resetState);
        onFilterChange(games); // Reset to all games
    };
    
    const activeFilterCount = useMemo(() => {
        let count = 0;
        if (filters.dateRange.start || filters.dateRange.end) count++;
        if (filters.teams.length > 0) count++;
        if (filters.venues.length > 0) count++;
        if (filters.dayOfWeek.length > 0) count++;
        if (filters.homeAway !== 'all') count++;
        if (filters.minScore || filters.maxScore) count++;
        if (filters.extraInnings) count++;
        return count;
    }, [filters]);
    
    return (
        <div className="bg-white rounded-lg shadow mb-6">
            <div className="p-4 border-b flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <h3 className="subsection-title font-bold">🔍 Advanced Filters</h3>
                    {activeFilterCount > 0 && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-bold">
                            {activeFilterCount} active
                        </span>
                    )}
                </div>
                <button 
                    onClick={() => setShowFilters(!showFilters)}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 body-text"
                >
                    {showFilters ? 'Hide Filters' : 'Show Filters'}
                </button>
            </div>
            
            {showFilters && (
                <div className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                        {/* Date Range */}
                        <div>
                            <label className="small-text font-semibold block mb-2">📅 Date Range</label>
                            <input 
                                type="date" 
                                value={filters.dateRange.start}
                                onChange={(e) => setFilters({...filters, dateRange: {...filters.dateRange, start: e.target.value}})}
                                className="w-full px-3 py-2 border rounded small-text mb-2"
                                placeholder="Start date"
                            />
                            <input 
                                type="date" 
                                value={filters.dateRange.end}
                                onChange={(e) => setFilters({...filters, dateRange: {...filters.dateRange, end: e.target.value}})}
                                className="w-full px-3 py-2 border rounded small-text"
                                placeholder="End date"
                            />
                        </div>
                        
                        {/* Teams */}
                        <div>
                            <label className="small-text font-semibold block mb-2">⚾ Teams (select multiple)</label>
                            <select 
                                multiple
                                size="5"
                                value={filters.teams}
                                onChange={(e) => {
                                    const selected = Array.from(e.target.selectedOptions, opt => opt.value);
                                    setFilters({...filters, teams: selected});
                                }}
                                className="w-full px-3 py-2 border rounded small-text"
                            >
                                {availableTeams.map(team => (
                                    <option key={team} value={team}>{team}</option>
                                ))}
                            </select>
                        </div>
                        
                        {/* Day of Week */}
                        <div>
                            <label className="small-text font-semibold block mb-2">📆 Day of Week</label>
                            <div className="space-y-1">
                                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                                    <label key={day} className="flex items-center small-text hover:bg-gray-50 p-1 rounded cursor-pointer">
                                        <input 
                                            type="checkbox"
                                            checked={filters.dayOfWeek.includes(day)}
                                            onChange={(e) => {
                                                const newDays = e.target.checked 
                                                    ? [...filters.dayOfWeek, day]
                                                    : filters.dayOfWeek.filter(d => d !== day);
                                                setFilters({...filters, dayOfWeek: newDays});
                                            }}
                                            className="mr-2"
                                        />
                                        {day}
                                    </label>
                                ))}
                            </div>
                        </div>
                        
                        {/* Venues */}
                        <div>
                            <label className="small-text font-semibold block mb-2">🏟️ Venues (select multiple)</label>
                            <select 
                                multiple
                                size="5"
                                value={filters.venues}
                                onChange={(e) => {
                                    const selected = Array.from(e.target.selectedOptions, opt => opt.value);
                                    setFilters({...filters, venues: selected});
                                }}
                                className="w-full px-3 py-2 border rounded small-text"
                            >
                                {availableVenues.map(venue => (
                                    <option key={venue} value={venue} title={venue}>
                                        {venue.length > 30 ? venue.substring(0, 30) + '...' : venue}
                                    </option>
                                ))}
                            </select>
                        </div>
                        
                        {/* Home/Away */}
                        <div>
                            <label className="small-text font-semibold block mb-2">🏠 Home/Away (Orioles)</label>
                            <select 
                                value={filters.homeAway}
                                onChange={(e) => setFilters({...filters, homeAway: e.target.value})}
                                className="w-full px-3 py-2 border rounded small-text"
                            >
                                <option value="all">All Games</option>
                                <option value="home">Home Games Only</option>
                                <option value="away">Away Games Only</option>
                            </select>
                        </div>
                        
                        {/* Score Range */}
                        <div>
                            <label className="small-text font-semibold block mb-2">🎯 Total Score Range</label>
                            <input 
                                type="number"
                                value={filters.minScore}
                                onChange={(e) => setFilters({...filters, minScore: e.target.value})}
                                placeholder="Min total runs"
                                className="w-full px-3 py-2 border rounded small-text mb-2"
                            />
                            <input 
                                type="number"
                                value={filters.maxScore}
                                onChange={(e) => setFilters({...filters, maxScore: e.target.value})}
                                placeholder="Max total runs"
                                className="w-full px-3 py-2 border rounded small-text"
                            />
                        </div>
                    </div>
                    
                    {/* Action buttons */}
                    <div className="flex gap-3 pt-4 border-t">
                        <button 
                            onClick={applyFilters}
                            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 body-text font-semibold"
                        >
                            Apply Filters
                        </button>
                        <button 
                            onClick={resetFilters}
                            className="px-6 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 body-text font-semibold"
                        >
                            Reset All
                        </button>
                        <div className="flex-1"></div>
                        <div className="body-text text-gray-600 flex items-center">
                            Showing <strong className="mx-1">{games.length}</strong> games
                        </div>
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
                        <div key={i} className="text-center text-gray-500 font-medium" style={{ fontSize: '9px' }}>{day}</div>
                    ))}
                    {days.map((day, idx) => {
                        if (!day) return <div key={idx} className="aspect-square" />;
                        const hasGames = day.games.length > 0;
                        const bgColor = getHeatmapColor(day.games.length);
                        const textColor = getTextColor(day.games.length);
                        return (
                            <div
                                key={idx}
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
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                            <h3 className="section-title font-bold">{monthNames[monthIndices.indexOf(selectedMonthForModal)]} {selectedDate.day} • All Years</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedDate.games.length} game{selectedDate.games.length !== 1 ? 's' : ''} attended</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            <div className="divide-y">
                                {selectedDate.games.sort((a, b) => new Date(b.date) - new Date(a.date)).map((game, idx) => (
                                    <div key={idx} className="p-4 hover:bg-blue-50 transition-colors">
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

    const handleCellClick = (team, opponent, count) => {
        if (count === 'X' || count === 0) return;
        const matchupGames = games.filter(game =>
            (game.homeTeam === team && game.awayTeam === opponent) ||
            (game.homeTeam === opponent && game.awayTeam === team)
        ).sort((a, b) => new Date(b.date) - new Date(a.date));
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
                            {matrix.map((row, idx) => (
                                <tr key={idx}>
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
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                            <h3 className="section-title font-bold">{selectedMatchup.team} vs {selectedMatchup.opponent}</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedMatchup.count} game{selectedMatchup.count !== 1 ? 's' : ''} attended</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            {selectedMatchup.games.length > 0 ? (
                                <div className="divide-y">
                                    {selectedMatchup.games.map((game, idx) => {
                                        const isHomeGame = game.homeTeam === selectedMatchup.team;
                                        return (
                                            <div key={idx} className="p-4 hover:bg-blue-50 transition-colors">
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
                            {streaksData.recentGames.map((g, i) => (
                                <div key={i} className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold text-white ${g.result === 'W' ? 'bg-green-500' : 'bg-red-500'}`} title={`${g.date}: ${g.result} ${g.score} vs ${g.opponent}`}>
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
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowGames(false)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                            <h3 className="section-title font-bold">Games with {selectedCompanion.name}</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedCompanion.totalGames} total games</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            <div className="divide-y">
                                {selectedCompanion.games.map((game, idx) => (
                                    <div key={idx} className="p-4 hover:bg-blue-50 transition-colors">
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

const SmartInsights = ({ data }) => {
    const [insightsView, setInsightsView] = useState('overview');
    const [selectedYear, setSelectedYear] = useState('all');
    const [selectedMonth, setSelectedMonth] = useState('all');
    const [selectedTeam, setSelectedTeam] = useState('all');
    const [selectedGameType, setSelectedGameType] = useState('all');
    
    const today = new Date();
    const todayMonth = today.getMonth();
    const todayDay = today.getDate();
    
    const normalizeTeamCode = (code) => {
        const mapping = {
            'OAK': 'ATH',  // Map old Oakland games to Athletics
            'SDP': 'SD', 'SFG': 'SF', 'CHW': 'CWS',
            'KCR': 'KC', 'TBR': 'TB', 'WSN': 'WSH', 'CHN': 'CHC',
            'SDN': 'SD', 'SFN': 'SF', 'TBA': 'TB', 'KCA': 'KC',
            'CHA': 'CWS', 'WAS': 'WSH', 'NYA': 'NYY', 'NYN': 'NYM',
            'LAN': 'LAD', 'SLN': 'STL', 'ANA': 'LAA', 'FLO': 'MIA',
        };
        return mapping[code] || code;
    };
    
    // Filter games based on selections
    const filteredGames = useMemo(() => {
        let games = data.games || [];

        if (selectedYear !== 'all') {
            games = games.filter(game => {
                const date = new Date(game.date);
                return !isNaN(date) && date.getFullYear().toString() === selectedYear;
            });
        }

        if (selectedMonth !== 'all') {
            games = games.filter(game => {
                const date = new Date(game.date);
                return !isNaN(date) && date.getMonth() === parseInt(selectedMonth);
            });
        }

        if (selectedTeam !== 'all') {
            games = games.filter(game =>
                normalizeTeamCode(game.homeTeam) === selectedTeam ||
                normalizeTeamCode(game.awayTeam) === selectedTeam
            );
        }

        if (selectedGameType !== 'all') {
            games = games.filter(game => (game.gameType || 'regular') === selectedGameType);
        }

        return games;
    }, [data.games, selectedYear, selectedMonth, selectedTeam, selectedGameType]);
    
    // Get unique years and teams
    const availableYears = useMemo(() => {
        const years = new Set();
        (data.games || []).forEach(game => {
            const date = new Date(game.date);
            if (!isNaN(date)) years.add(date.getFullYear().toString());
        });
        return Array.from(years).sort().reverse();
    }, [data.games]);
    
    const availableTeams = useMemo(() => {
        const teams = new Set();
        (data.games || []).forEach(game => {
            teams.add(normalizeTeamCode(game.homeTeam));
            teams.add(normalizeTeamCode(game.awayTeam));
        });
        return Array.from(teams).sort();
    }, [data.games]);
    
    // TREND ANALYSIS: Games per year
    const yearlyTrends = useMemo(() => {
        const byYear = {};
        (data.games || []).forEach(game => {
            const date = new Date(game.date);
            if (!isNaN(date)) {
                const year = date.getFullYear();
                byYear[year] = (byYear[year] || 0) + 1;
            }
        });
        
        return Object.entries(byYear)
            .sort((a, b) => a[0] - b[0])
            .map(([year, count]) => ({ year, games: count }));
    }, [data.games]);
    
    // SMART INSIGHT: Best/Most Exciting Games
    const bestGames = useMemo(() => {
        const games = data.games || [];
        
        // Highest scoring
        const highestScoring = [...games].sort((a, b) => {
            // Remove innings in parentheses before extracting scores
            // "LAD 10 - 11 SF (10)" → "LAD 10 - 11 SF"
            const aScore = a.score.replace(/\\s*\\(\\d+\\)\\s*$/, '');
            const bScore = b.score.replace(/\\s*\\(\\d+\\)\\s*$/, '');
            
            const aTotal = (aScore.match(/\\d+/g) || []).reduce((sum, n) => sum + parseInt(n), 0);
            const bTotal = (bScore.match(/\\d+/g) || []).reduce((sum, n) => sum + parseInt(n), 0);
            return bTotal - aTotal;
        }).slice(0, 5);
        
        // Closest games (1-run games)
        const closestGames = games.filter(game => {
            const scores = game.score.match(/\\d+/g);
            if (scores && scores.length === 2) {
                return Math.abs(parseInt(scores[0]) - parseInt(scores[1])) === 1;
            }
            return false;
        }).slice(0, 5);
        
        // Walk-off games
        const walkoffMilestones = (data.milestones || []).filter(m => m.type === 'Walk-Offs');
        const walkoffGameIds = new Set(walkoffMilestones.map(m => m.gameId));
        const walkoffGames = games.filter(game => walkoffGameIds.has(game.gameId));
        
        return { highestScoring, closestGames, walkoffGames };
    }, [data.games, data.milestones]);
    
    // SMART INSIGHT: Attendance Streaks
    const attendanceStreaks = useMemo(() => {
        const games = [...(data.games || [])].sort((a, b) => 
            new Date(a.date) - new Date(b.date)
        );
        
        let longestGap = 0;
        let longestGapGames = null;
        let maxGamesInWindow = 0;
        let maxWindowStart = null;
        let maxWindowEnd = null;
        
        // Find longest gap
        for (let i = 1; i < games.length; i++) {
            const prevDate = new Date(games[i-1].date);
            const currDate = new Date(games[i].date);
            const gap = Math.floor((currDate - prevDate) / (1000 * 60 * 60 * 24));
            
            if (gap > longestGap) {
                longestGap = gap;
                longestGapGames = { before: games[i-1], after: games[i] };
            }
        }
        
        // Find most games in 30-day window
        for (let i = 0; i < games.length; i++) {
            const startDate = new Date(games[i].date);
            const endDate = new Date(startDate);
            endDate.setDate(endDate.getDate() + 30);
            
            let count = 0;
            let windowEnd = i;
            
            for (let j = i; j < games.length; j++) {
                const gameDate = new Date(games[j].date);
                if (gameDate <= endDate) {
                    count++;
                    windowEnd = j;
                } else {
                    break;
                }
            }
            
            if (count > maxGamesInWindow) {
                maxGamesInWindow = count;
                maxWindowStart = games[i];
                maxWindowEnd = games[windowEnd];
            }
        }
        
        return { longestGap, longestGapGames, maxGamesInWindow, maxWindowStart, maxWindowEnd };
    }, [data.games]);
    
    // SMART INSIGHT: Top Rivalries
    const topRivalries = useMemo(() => {
        const matchups = {};
        
        filteredGames.forEach(game => {
            const team1 = normalizeTeamCode(game.homeTeam);
            const team2 = normalizeTeamCode(game.awayTeam);
            const pair = [team1, team2].sort().join(' vs ');
            
            if (!matchups[pair]) {
                matchups[pair] = {
                    teams: [team1, team2].sort(),
                    games: [],
                    teamWins: {}
                };
                matchups[pair].teamWins[team1] = 0;
                matchups[pair].teamWins[team2] = 0;
            }
            
            matchups[pair].games.push(game);
            
            // Determine winner (use first 2 numbers, handles extra innings like "5 - 4 (10)")
            const scores = game.score.match(/\\d+/g);
            if (scores && scores.length >= 2) {
                const awayScore = parseInt(scores[0]);
                const homeScore = parseInt(scores[1]);
                const winner = homeScore > awayScore ? normalizeTeamCode(game.homeTeam) : 
                              awayScore > homeScore ? normalizeTeamCode(game.awayTeam) : null;
                
                if (winner) {
                    matchups[pair].teamWins[winner]++;
                }
            }
        });
        
        return Object.entries(matchups)
            .sort((a, b) => b[1].games.length - a[1].games.length)
            .slice(0, 5)
            .map(([name, data]) => {
                const [team1, team2] = data.teams;
                return {
                    name,
                    count: data.games.length,
                    team1,
                    team2,
                    team1Wins: data.teamWins[team1] || 0,
                    team2Wins: data.teamWins[team2] || 0
                };
            });
    }, [filteredGames]);
    
    // This Week in History - games from this week in previous years
    const thisWeekGames = useMemo(() => {
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay()); // Sunday
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6); // Saturday

        return filteredGames.filter(game => {
            const gameDate = new Date(game.date);
            if (isNaN(gameDate)) return false;
            // Check if game falls within this calendar week (same month/day range, any year)
            const gameMonth = gameDate.getMonth();
            const gameDay = gameDate.getDate();
            const startMonth = startOfWeek.getMonth();
            const startDay = startOfWeek.getDate();
            const endMonth = endOfWeek.getMonth();
            const endDay = endOfWeek.getDate();

            // Simple check: is this game's month/day within this week's range?
            if (startMonth === endMonth) {
                return gameMonth === startMonth && gameDay >= startDay && gameDay <= endDay;
            } else {
                // Week spans two months
                return (gameMonth === startMonth && gameDay >= startDay) ||
                       (gameMonth === endMonth && gameDay <= endDay);
            }
        }).sort((a, b) => {
            // Sort by month/day first, then by year (most recent)
            const aDate = new Date(a.date);
            const bDate = new Date(b.date);
            const aMonthDay = aDate.getMonth() * 100 + aDate.getDate();
            const bMonthDay = bDate.getMonth() * 100 + bDate.getDate();
            if (aMonthDay !== bMonthDay) return aMonthDay - bMonthDay;
            return bDate.getFullYear() - aDate.getFullYear();
        });
    }, [filteredGames, today]);
    
    // Attendance patterns
    const attendancePatterns = useMemo(() => {
        const byMonth = {};
        const byDayOfWeek = [0,0,0,0,0,0,0];
        const byTeam = {};
        const byVenue = {};
        
        filteredGames.forEach(game => {
            const date = new Date(game.date);
            if (isNaN(date)) return;
            const month = date.toLocaleString('default', { month: 'long' });
            byMonth[month] = (byMonth[month] || 0) + 1;
            byDayOfWeek[date.getDay()]++;
            const homeTeam = normalizeTeamCode(game.homeTeam);
            const awayTeam = normalizeTeamCode(game.awayTeam);
            byTeam[homeTeam] = (byTeam[homeTeam] || 0) + 1;
            byTeam[awayTeam] = (byTeam[awayTeam] || 0) + 1;
            let venue = game.venue;
            
            // Normalize venue names for counting
            if (venue.includes('AT&T Park')) venue = 'Oracle Park';
            if (venue.includes('O.co') || venue.includes('RingCentral') || venue.includes('Oakland Coliseum') || venue.includes('Network Associates')) venue = 'Oakland Coliseum';
            if (venue.includes('Yankee Stadium')) venue = 'Yankee Stadium';
            if (venue.includes('Busch Stadium')) venue = 'Busch Stadium';
            if (venue.includes('Angel Stadium')) venue = 'Angel Stadium';
            if (venue.includes('U.S. Cellular')) venue = 'Guaranteed Rate Field';
            if (venue.includes('Miller Park')) venue = 'American Family Field';
            if (venue.includes('Safeco')) venue = 'T-Mobile Park';
            if (venue.includes('SunTrust')) venue = 'Truist Park';
            if (venue.includes('Marlins Park')) venue = 'loanDepot park';
            
            byVenue[venue] = (byVenue[venue] || 0) + 1;
        });
        
        const favoriteMonth = Object.entries(byMonth).sort((a, b) => b[1] - a[1])[0];
        const favoriteDayName = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const favoriteDay = byDayOfWeek.indexOf(Math.max(...byDayOfWeek));
        const favoriteTeam = Object.entries(byTeam).sort((a, b) => b[1] - a[1])[0];
        const favoriteVenue = Object.entries(byVenue).sort((a, b) => b[1] - a[1])[0];
        
        return {
            byMonth, byDayOfWeek, byVenue, byTeam,
            favoriteMonth: favoriteMonth ? favoriteMonth[0] : 'N/A',
            favoriteMonthCount: favoriteMonth ? favoriteMonth[1] : 0,
            favoriteDay: favoriteDayName[favoriteDay],
            favoriteDayCount: byDayOfWeek[favoriteDay],
            favoriteTeam: favoriteTeam ? favoriteTeam[0] : 'N/A',
            favoriteTeamCount: favoriteTeam ? favoriteTeam[1] : 0,
            favoriteVenue: favoriteVenue ? favoriteVenue[0] : 'N/A',
            favoriteVenueCount: favoriteVenue ? favoriteVenue[1] : 0,
        };
    }, [filteredGames]);
    
    // Enhanced bucket list with Athletics updates
    const bucketList = useMemo(() => {
        const allMLBTeams = new Set([
            'ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CWS', 'CIN', 'CLE', 'COL', 'DET', 
            'HOU', 'KC', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'ATH',
            'PHI', 'PIT', 'SD', 'SEA', 'SF', 'STL', 'TB', 'TEX', 'TOR', 'WSH'
        ]);
        
        // Current MLB Stadiums (30 teams = 30 stadiums)
        const mlbStadiums = {
            'Oracle Park': 'SF',
            'Dodger Stadium': 'LAD',
            'Petco Park': 'SD',
            'Chase Field': 'ARI',
            'Coors Field': 'COL',
            'T-Mobile Park': 'SEA',
            'Sutter Health Park': 'ATH',
            'Angel Stadium': 'LAA',
            'Minute Maid Park': 'HOU',
            'Globe Life Field': 'TEX',
            'Kauffman Stadium': 'KC',
            'Target Field': 'MIN',
            'Guaranteed Rate Field': 'CWS',
            'Comerica Park': 'DET',
            'Progressive Field': 'CLE',
            'American Family Field': 'MIL',
            'Wrigley Field': 'CHC',
            'Busch Stadium': 'STL',
            'Great American Ball Park': 'CIN',
            'PNC Park': 'PIT',
            'Truist Park': 'ATL',
            'loanDepot park': 'MIA',
            'Nationals Park': 'WSH',
            'Citizens Bank Park': 'PHI',
            'Citi Field': 'NYM',
            'Yankee Stadium': 'NYY',
            'Fenway Park': 'BOS',
            'Oriole Park at Camden Yards': 'BAL',
            'Tropicana Field': 'TB',
            'Rogers Centre': 'TOR'
        };
        
        const visitedTeams = new Set();
        const visitedStadiums = new Set();
        const oriolesStadiums = new Set();
        
        filteredGames.forEach(game => {
            const homeTeam = normalizeTeamCode(game.homeTeam);
            const awayTeam = normalizeTeamCode(game.awayTeam);
            
            visitedTeams.add(homeTeam);
            visitedTeams.add(awayTeam);
            
            // Normalize venue name
            let venue = game.venue;
            
            // Handle historical stadium names
            if (venue.includes('AT&T Park')) venue = 'Oracle Park';
            if (venue.includes('U.S. Cellular')) venue = 'Guaranteed Rate Field';
            if (venue.includes('Miller Park')) venue = 'American Family Field';
            if (venue.includes('Safeco')) venue = 'T-Mobile Park';
            if (venue.includes('SunTrust')) venue = 'Truist Park';
            if (venue.includes('Marlins Park')) venue = 'loanDepot park';
            
            // Handle CURRENT stadium number suffixes ONLY
            if (venue === 'Yankee Stadium III') venue = 'Yankee Stadium';
            if (venue === 'Busch Stadium III') venue = 'Busch Stadium';
            if (venue.includes('Angel Stadium of Anaheim')) venue = 'Angel Stadium';
            
            // Oakland Coliseum doesn't count toward current 30 (A's moved to Sacramento)
            // Don't normalize Oakland Coliseum variants
            
            // Check if it's a current MLB stadium
            if (mlbStadiums[venue]) {
                visitedStadiums.add(venue);
            }
            
            // Track Orioles games
            if (homeTeam === 'BAL' || awayTeam === 'BAL') {
                if (mlbStadiums[venue]) {
                    oriolesStadiums.add(venue);
                }
            }
        });
        
        const unseenTeams = Array.from(allMLBTeams).filter(team => !visitedTeams.has(team));
        const unseenStadiums = Object.keys(mlbStadiums).filter(stadium => !visitedStadiums.has(stadium));
        const oriolesUnseenStadiums = Object.keys(mlbStadiums).filter(stadium => !oriolesStadiums.has(stadium));
        
        return {
            unseenTeams,
            teamsCompleted: visitedTeams.size,
            totalMLBTeams: allMLBTeams.size,
            stadiumsVisited: visitedStadiums.size,
            totalMLBStadiums: Object.keys(mlbStadiums).length,
            visitedStadiumsList: Array.from(visitedStadiums).sort(),
            unseenStadiums,
            oriolesStadiumsVisited: oriolesStadiums.size,
            oriolesStadiumsList: Array.from(oriolesStadiums).sort(),
            oriolesUnseenStadiums
        };
    }, [filteredGames]);
    
    const timeSinceLastGame = useMemo(() => {
        if (!filteredGames || filteredGames.length === 0) return null;
        const sortedGames = [...filteredGames].sort((a, b) => new Date(b.date) - new Date(a.date));
        const lastGame = sortedGames[0];
        const lastDate = new Date(lastGame.date);
        if (isNaN(lastDate)) return null;
        const daysSince = Math.floor((today - lastDate) / (1000 * 60 * 60 * 24));
        return {
            game: lastGame, daysSince,
            message: daysSince === 0 ? 'Today!' : daysSince === 1 ? 'Yesterday' :
                     daysSince < 7 ? `${daysSince} days ago` : daysSince < 30 ? `${Math.floor(daysSince / 7)} weeks ago` :
                     daysSince < 365 ? `${Math.floor(daysSince / 30)} months ago` : `${Math.floor(daysSince / 365)} years ago`
        };
    }, [filteredGames]);

    // Orioles Win/Loss record when attending
    const oriolesRecord = useMemo(() => {
        let wins = 0, losses = 0, ties = 0;

        filteredGames.forEach(game => {
            const homeTeam = normalizeTeamCode(game.homeTeam);
            const awayTeam = normalizeTeamCode(game.awayTeam);

            // Only count Orioles games
            if (homeTeam !== 'BAL' && awayTeam !== 'BAL') return;

            const scores = game.score.match(/\\d+/g);
            if (scores && scores.length >= 2) {
                const awayScore = parseInt(scores[0]);
                const homeScore = parseInt(scores[1]);

                const oriolesScore = homeTeam === 'BAL' ? homeScore : awayScore;
                const opponentScore = homeTeam === 'BAL' ? awayScore : homeScore;

                if (oriolesScore > opponentScore) wins++;
                else if (oriolesScore < opponentScore) losses++;
                else ties++;
            }
        });

        const total = wins + losses + ties;
        const winPct = total > 0 ? ((wins / total) * 100).toFixed(1) : '0.0';

        return { wins, losses, ties, total, winPct };
    }, [filteredGames]);

    // First and most recent game
    const firstAndLastGame = useMemo(() => {
        if (!filteredGames || filteredGames.length === 0) return null;
        const sortedGames = [...filteredGames].sort((a, b) => new Date(a.date) - new Date(b.date));
        return {
            first: sortedGames[0],
            last: sortedGames[sortedGames.length - 1],
            spanYears: Math.abs(new Date(sortedGames[sortedGames.length - 1].date).getFullYear() -
                               new Date(sortedGames[0].date).getFullYear())
        };
    }, [filteredGames]);

    const InsightCard = ({ icon, title, description, action, color = 'blue' }) => {
        const colors = {
            blue: 'border-blue-200 bg-blue-50', green: 'border-green-200 bg-green-50',
            purple: 'border-purple-200 bg-purple-50', orange: 'border-orange-200 bg-orange-50',
            red: 'border-red-200 bg-red-50'
        };
        return (
            <div className={`bg-white rounded-lg shadow border-l-4 ${colors[color]} p-4 hover:shadow-lg transition-all`}>
                <div className="flex items-start gap-3">
                    <span className="text-2xl">{icon}</span>
                    <div className="flex-1">
                        <h3 className="subsection-title font-bold text-gray-900">{title}</h3>
                        <p className="body-text text-gray-600 mt-1">{description}</p>
                        {action && <p className="small-text text-blue-600 font-medium mt-2">{action}</p>}
                    </div>
                </div>
            </div>
        );
    };
    
    return (
        <div className="space-y-6">
            {/* Filter Controls */}
            <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center gap-4 flex-wrap">
                    <span className="body-text font-bold text-gray-700">Filter Insights:</span>
                    <select 
                        value={selectedYear} 
                        onChange={(e) => setSelectedYear(e.target.value)}
                        className="px-4 py-2 body-text border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                    >
                        <option value="all">All Years</option>
                        {availableYears.map(year => (
                            <option key={year} value={year}>{year}</option>
                        ))}
                    </select>
                    
                    <select 
                        value={selectedMonth} 
                        onChange={(e) => setSelectedMonth(e.target.value)}
                        className="px-4 py-2 body-text border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                    >
                        <option value="all">All Months</option>
                        <option value="2">March</option>
                        <option value="3">April</option>
                        <option value="4">May</option>
                        <option value="5">June</option>
                        <option value="6">July</option>
                        <option value="7">August</option>
                        <option value="8">September</option>
                        <option value="9">October</option>
                    </select>
                    
                    <select
                        value={selectedTeam}
                        onChange={(e) => setSelectedTeam(e.target.value)}
                        className="px-4 py-2 body-text border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                    >
                        <option value="all">All Teams</option>
                        {availableTeams.map(team => (
                            <option key={team} value={team}>{team}</option>
                        ))}
                    </select>

                    {/* Game Type Filter */}
                    {(data.gameTypeCounts?.spring > 0 || data.gameTypeCounts?.postseason > 0) && (
                        <select
                            value={selectedGameType}
                            onChange={(e) => setSelectedGameType(e.target.value)}
                            className="px-4 py-2 body-text border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                        >
                            <option value="all">All Game Types</option>
                            <option value="regular">Regular Season ({data.gameTypeCounts?.regular || 0})</option>
                            {data.gameTypeCounts?.postseason > 0 && (
                                <option value="postseason">Postseason ({data.gameTypeCounts?.postseason})</option>
                            )}
                            {data.gameTypeCounts?.spring > 0 && (
                                <option value="spring">Spring Training ({data.gameTypeCounts?.spring})</option>
                            )}
                        </select>
                    )}

                    {(selectedYear !== 'all' || selectedMonth !== 'all' || selectedTeam !== 'all' || selectedGameType !== 'all') && (
                        <button
                            onClick={() => { setSelectedYear('all'); setSelectedMonth('all'); setSelectedTeam('all'); setSelectedGameType('all'); }}
                            className="px-4 py-2 body-text text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg border-2 border-gray-300"
                        >
                            Clear Filters
                        </button>
                    )}
                    
                    <div className="ml-auto body-text text-gray-600">
                        Showing <strong>{filteredGames.length}</strong> of <strong>{data.games?.length || 0}</strong> games
                    </div>
                </div>
            </div>
            
            {/* Sub-navigation */}
            <div className="flex gap-2 flex-wrap">
                {[
                    { id: 'overview', label: 'Overview', icon: '📊' },
                    { id: 'records', label: 'Records', icon: '📋' },
                    { id: 'trends', label: 'Trends', icon: '📈' },
                    { id: 'patterns', label: 'Patterns', icon: '🎯' },
                    { id: 'progress', label: 'Progress', icon: '🏆' },
                ].map(view => (
                    <button
                        key={view.id}
                        onClick={() => setInsightsView(view.id)}
                        className={`px-5 py-2.5 body-text rounded-lg font-semibold transition-all flex items-center gap-2 ${
                            insightsView === view.id
                                ? 'bg-blue-600 text-white shadow-md'
                                : 'bg-white text-gray-700 hover:bg-gray-100 shadow'
                        }`}
                    >
                        <span>{view.icon}</span>
                        {view.label}
                    </button>
                ))}
            </div>
            
            {/* Overview View */}
            {insightsView === 'overview' && (
                <div className="space-y-6">
                    {/* Quick Stats Row */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">⚾</span>
                                <div>
                                    <div className="text-2xl font-bold text-gray-900">{filteredGames.length}</div>
                                    <div className="small-text text-gray-600">Total Games</div>
                                </div>
                            </div>
                        </div>
                        {oriolesRecord.total > 0 && (
                            <div className="bg-white rounded-lg shadow p-4 border-l-4 border-orange-500">
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">🧡</span>
                                    <div>
                                        <div className="text-2xl font-bold text-gray-900">{oriolesRecord.wins}-{oriolesRecord.losses}</div>
                                        <div className="small-text text-gray-600">O's Record ({oriolesRecord.winPct}%)</div>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">🏟️</span>
                                <div>
                                    <div className="text-2xl font-bold text-gray-900">{bucketList.stadiumsVisited}</div>
                                    <div className="small-text text-gray-600">of 30 Stadiums</div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">👥</span>
                                <div>
                                    <div className="text-2xl font-bold text-gray-900">{bucketList.teamsCompleted}</div>
                                    <div className="small-text text-gray-600">of 30 Teams</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* This Week in History */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">📅 This Week in History</h2>
                            <p className="body-text text-gray-500 mt-1">Games you attended during this week in previous years</p>
                        </div>
                        <div className="p-4">
                            {thisWeekGames.length > 0 ? (
                                <div className="space-y-3">
                                    {thisWeekGames.slice(0, 10).map((game, idx) => {
                                        const gameDate = new Date(game.date);
                                        const yearsAgo = today.getFullYear() - gameDate.getFullYear();
                                        return (
                                            <div key={idx} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                        <div className="text-center min-w-[60px]">
                                                            <span className="body-text font-bold text-blue-600 block">{game.date}</span>
                                                            <span className="small-text text-gray-500">{yearsAgo === 0 ? 'This year' : yearsAgo === 1 ? '1 year ago' : `${yearsAgo} years ago`}</span>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <span className="body-text font-semibold">{game.awayTeam}</span>
                                                            <span className="body-text text-gray-500">@</span>
                                                            <span className="body-text font-semibold">{game.homeTeam}</span>
                                                        </div>
                                                        <span className="font-mono body-text bg-white px-2 py-1 rounded">{game.score}</span>
                                                    </div>
                                                    <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                                                </div>
                                            </div>
                                        );
                                    })}
                                    {thisWeekGames.length > 10 && (
                                        <p className="small-text text-gray-500 text-center">+{thisWeekGames.length - 10} more games this week in history</p>
                                    )}
                                </div>
                            ) : (
                                <p className="body-text text-gray-500 text-center py-8">No games attended during this week in previous years</p>
                            )}
                        </div>
                    </div>
                    
                    {/* Attendance Streaks */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">🔥 Attendance Streaks</h2>
                        </div>
                        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                            <InsightCard 
                                icon="📅" 
                                title="Longest Gap" 
                                description={`${attendanceStreaks.longestGap} days between games`}
                                action={attendanceStreaks.longestGapGames ? 
                                    `${attendanceStreaks.longestGapGames.before.date} to ${attendanceStreaks.longestGapGames.after.date}` : ''}
                                color="orange"
                            />
                            <InsightCard 
                                icon="🚀" 
                                title="Hot Streak" 
                                description={`${attendanceStreaks.maxGamesInWindow} games in 30 days`}
                                action={attendanceStreaks.maxWindowStart ? 
                                    `${attendanceStreaks.maxWindowStart.date} to ${attendanceStreaks.maxWindowEnd.date}` : ''}
                                color="green"
                            />
                        </div>
                    </div>
                    
                    {/* Best Games */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">⭐ Most Exciting Games</h2>
                        </div>
                        <div className="p-4">
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <div>
                                    <h3 className="subsection-title font-bold mb-3">🔥 Highest Scoring</h3>
                                    <div className="space-y-2">
                                        {bestGames.highestScoring.map((game, idx) => (
                                            <div key={idx} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <span className="body-text font-bold text-gray-500">{idx + 1}.</span>
                                                    <span className="body-text">{game.awayTeam} @ {game.homeTeam}</span>
                                                    <span className="font-mono body-text bg-orange-100 px-2 py-1 rounded font-bold">{game.score}</span>
                                                </div>
                                                <span className="small-text text-gray-500">{game.date}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                
                                <div>
                                    <h3 className="subsection-title font-bold mb-3">😰 Nail-Biters (1-Run)</h3>
                                    <div className="space-y-2">
                                        {bestGames.closestGames.slice(0, 5).map((game, idx) => (
                                            <div key={idx} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <span className="body-text font-bold text-gray-500">{idx + 1}.</span>
                                                    <span className="body-text">{game.awayTeam} @ {game.homeTeam}</span>
                                                    <span className="font-mono body-text bg-blue-100 px-2 py-1 rounded font-bold">{game.score}</span>
                                                </div>
                                                <span className="small-text text-gray-500">{game.date}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                
                                <div>
                                    <h3 className="subsection-title font-bold mb-3">🎉 Walk-Off Wins</h3>
                                    <div className="space-y-2">
                                        {bestGames.walkoffGames.length > 0 ? (
                                            bestGames.walkoffGames.slice(0, 5).map((game, idx) => (
                                                <div key={idx} className="p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="body-text">{game.awayTeam} @ {game.homeTeam}</span>
                                                        <span className="font-mono body-text bg-green-600 text-white px-2 py-1 rounded font-bold">{game.score}</span>
                                                    </div>
                                                    <div className="flex items-center justify-between">
                                                        <span className="small-text text-gray-600">{game.date}</span>
                                                        <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                                                    </div>
                                                </div>
                                            ))
                                        ) : (
                                            <p className="body-text text-gray-500 text-center py-8">No walk-off games yet</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    {/* Top Rivalries */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">⚔️ Top Rivalries</h2>
                            <p className="body-text text-gray-500 mt-1">Most watched matchups with your attendance records</p>
                        </div>
                        <div className="p-4">
                            <div className="space-y-3">
                                {topRivalries.map((rivalry, idx) => (
                                    <div key={idx} className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <span className="text-2xl font-bold text-blue-600">{idx + 1}</span>
                                                <div>
                                                    <div className="body-text font-bold">{rivalry.name}</div>
                                                    <div className="small-text text-gray-600 mt-1">
                                                        When you attend: <span className="font-semibold text-blue-600">{rivalry.team1} {rivalry.team1Wins}-{rivalry.team2Wins} {rivalry.team2}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-2xl font-bold text-blue-600">{rivalry.count}</div>
                                                <div className="small-text text-gray-600">games</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    
                    {/* Your Baseball Journey - First & Last Games */}
                    {firstAndLastGame && (
                        <div className="bg-white rounded-lg shadow">
                            <div className="p-4 border-b">
                                <h2 className="section-title font-bold">🛤️ Your Baseball Journey</h2>
                                <p className="body-text text-gray-500 mt-1">
                                    {firstAndLastGame.spanYears > 0
                                        ? `${firstAndLastGame.spanYears} years of attending games`
                                        : 'Your first year of games!'
                                    }
                                </p>
                            </div>
                            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* First Game */}
                                <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                                    <div className="flex items-center gap-2 mb-3">
                                        <span className="text-xl">🎬</span>
                                        <span className="body-text font-bold text-green-700">First Game</span>
                                    </div>
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="body-text font-bold">{firstAndLastGame.first.awayTeam} @ {firstAndLastGame.first.homeTeam}</span>
                                        <span className="font-mono body-text bg-white px-2 py-1 rounded">{firstAndLastGame.first.score}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="small-text text-gray-600">{firstAndLastGame.first.date}</span>
                                        <GameLink gameId={firstAndLastGame.first.gameId} mlbGamePk={firstAndLastGame.first.mlbGamePk} source={firstAndLastGame.first.source} />
                                    </div>
                                </div>
                                {/* Most Recent Game */}
                                <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                                    <div className="flex items-center gap-2 mb-3">
                                        <span className="text-xl">⏱️</span>
                                        <span className="body-text font-bold text-blue-700">Most Recent</span>
                                        <span className="small-text text-gray-500 ml-auto">
                                            {timeSinceLastGame ? timeSinceLastGame.message : ''}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="body-text font-bold">{firstAndLastGame.last.awayTeam} @ {firstAndLastGame.last.homeTeam}</span>
                                        <span className="font-mono body-text bg-white px-2 py-1 rounded">{firstAndLastGame.last.score}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="small-text text-gray-600">{firstAndLastGame.last.date}</span>
                                        <GameLink gameId={firstAndLastGame.last.gameId} mlbGamePk={firstAndLastGame.last.mlbGamePk} source={firstAndLastGame.last.source} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
            
            {/* Trends View */}
            {insightsView === 'trends' && (
                <div className="space-y-6">
                    {/* Yearly Trends Chart */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">📈 Games Per Year</h2>
                            <p className="body-text text-gray-500 mt-1">Your baseball attendance over time</p>
                        </div>
                        <div className="p-6">
                            <div className="relative" style={{ height: '320px' }}>
                                <div className="absolute inset-0 flex items-end justify-between gap-2">
                                    {yearlyTrends.map((data, idx) => {
                                        const maxGames = Math.max(...yearlyTrends.map(y => y.games));
                                        const heightPercent = (data.games / maxGames) * 100;
                                        return (
                                            <div key={idx} className="flex-1 flex flex-col items-center justify-end h-full">
                                                <div 
                                                    className="w-full bg-blue-600 rounded-t transition-all hover:bg-blue-700 cursor-pointer relative group flex items-start justify-center pt-2" 
                                                    style={{ height: `${heightPercent}%` }}
                                                    onClick={() => setSelectedYear(data.year)}
                                                >
                                                    <span className="body-text text-white font-bold">
                                                        {data.games}
                                                    </span>
                                                    <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-3 py-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap small-text pointer-events-none z-10">
                                                        {data.games} games in {data.year}<br/>
                                                        <span className="text-xs">Click to filter</span>
                                                    </div>
                                                </div>
                                                <span className="body-text text-gray-600 font-medium mt-2">{data.year}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                            <p className="text-center small-text text-gray-500 mt-4">💡 Click any bar to filter to that year</p>
                        </div>
                    </div>
                    
                    {/* Year over year comparison */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">📊 Year-Over-Year Comparison</h2>
                        </div>
                        <div className="p-4">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {yearlyTrends.length >= 2 && (
                                    <>
                                        <InsightCard 
                                            icon="🏆" 
                                            title="Best Year" 
                                            description={`${Math.max(...yearlyTrends.map(y => y.games))} games attended`}
                                            action={yearlyTrends.find(y => y.games === Math.max(...yearlyTrends.map(y => y.games)))?.year}
                                            color="green"
                                        />
                                        <InsightCard 
                                            icon="📈" 
                                            title="Average Per Year" 
                                            description={`${(yearlyTrends.reduce((sum, y) => sum + y.games, 0) / yearlyTrends.length).toFixed(1)} games`}
                                            action={`Across ${yearlyTrends.length} years`}
                                            color="blue"
                                        />
                                        <InsightCard 
                                            icon="📅" 
                                            title="Most Recent Year" 
                                            description={`${yearlyTrends[yearlyTrends.length - 1].games} games in ${yearlyTrends[yearlyTrends.length - 1].year}`}
                                            action={yearlyTrends.length >= 2 ? 
                                                `${yearlyTrends[yearlyTrends.length - 1].games > yearlyTrends[yearlyTrends.length - 2].games ? '↑' : '↓'} from previous year` : ''}
                                            color="purple"
                                        />
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Records View - Categorized Statistics */}
            {insightsView === 'records' && (
                <div className="space-y-6">
                    {/* Categorized Summary Stats */}
                    {(() => {
                        // Build a lookup map for game details
                        const gameMap = {};
                        (data.games || []).forEach(game => {
                            if (game.gameId) {
                                gameMap[game.gameId] = game;
                            }
                        });

                        // Category definitions with colors and icons
                        const categoryConfig = {
                            'Game Format': { icon: '🎮', color: 'emerald', gradient: 'from-emerald-500 to-green-600' },
                            'Hitting': { icon: '🏏', color: 'orange', gradient: 'from-orange-500 to-amber-600' },
                            'Pitching': { icon: '⚾', color: 'indigo', gradient: 'from-indigo-500 to-purple-600' },
                            'Home Runs': { icon: '💣', color: 'red', gradient: 'from-red-500 to-rose-600' },
                            'Runs Scored': { icon: '🏃', color: 'blue', gradient: 'from-blue-500 to-cyan-600' },
                            'Defense': { icon: '🛡️', color: 'slate', gradient: 'from-slate-500 to-gray-600' },
                            'Baserunning': { icon: '👟', color: 'yellow', gradient: 'from-yellow-500 to-amber-500' },
                            'Other': { icon: '📊', color: 'gray', gradient: 'from-gray-500 to-slate-600' }
                        };

                        // Group summary records by category
                        const categories = {
                            'Game Format': [],
                            'Hitting': [],
                            'Pitching': [],
                            'Home Runs': [],
                            'Runs Scored': [],
                            'Defense': [],
                            'Baserunning': [],
                            'Other': []
                        };

                        (data.summary || []).forEach(row => {
                            const record = row.record.toLowerCase();

                            if (record.includes('extra inning') || record.includes('doubleheader') ||
                                record.includes('game length') || record.includes('attendance') ||
                                record.includes('longest') || record.includes('shortest')) {
                                categories['Game Format'].push(row);
                            }
                            else if (record.includes('hr') || record.includes('home run') ||
                                     record.includes('grand slam') || record.includes('multi-hr')) {
                                categories['Home Runs'].push(row);
                            }
                            else if (record.includes('hit') && !record.includes('pitcher') && !record.includes('shutout') ||
                                     record.includes('batting') || record.includes('cycle') || record.includes('double') ||
                                     record.includes('triple') || record.includes('single')) {
                                categories['Hitting'].push(row);
                            }
                            else if (record.includes('pitch') || record.includes('strikeout') ||
                                     record.includes(' k ') || record.includes('shutout') ||
                                     record.includes('complete game') || record.includes('quality start') ||
                                     record.includes('earned run') || record.includes('no-hit') ||
                                     record.includes('walks allowed') || record.includes('era')) {
                                categories['Pitching'].push(row);
                            }
                            else if (record.includes('run') && (record.includes('score') || record.includes('inning')) ||
                                     record.includes('rbi') || record.includes('runs in')) {
                                categories['Runs Scored'].push(row);
                            }
                            else if (record.includes('runs allowed') || record.includes('fewest hit') ||
                                     record.includes('error') || record.includes('defense')) {
                                categories['Defense'].push(row);
                            }
                            else if (record.includes('steal') || record.includes(' sb') || record.includes('caught')) {
                                categories['Baserunning'].push(row);
                            }
                            else {
                                categories['Other'].push(row);
                            }
                        });

                        // Render category cards
                        return (
                            <div className="space-y-6">
                                {/* Header with controls */}
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h2 className="section-title font-bold">📋 Personal Records</h2>
                                        <p className="body-text text-gray-500 mt-1">Records from games you've attended</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => {
                                                document.querySelectorAll('.category-card details').forEach(d => d.open = true);
                                            }}
                                            className="px-4 py-2 body-text bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg font-semibold transition-colors"
                                        >
                                            Expand All
                                        </button>
                                        <button
                                            onClick={() => {
                                                document.querySelectorAll('.category-card details').forEach(d => d.open = false);
                                            }}
                                            className="px-4 py-2 body-text bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-semibold transition-colors"
                                        >
                                            Collapse All
                                        </button>
                                    </div>
                                </div>

                                {Object.entries(categories).map(([categoryName, records]) => {
                                    if (records.length === 0) return null;
                                    const config = categoryConfig[categoryName];

                                    return (
                                        <div key={categoryName} className="bg-white rounded-xl shadow-lg category-card overflow-hidden">
                                            <details open>
                                                <summary className={`cursor-pointer p-5 bg-gradient-to-r ${config.gradient} text-white hover:opacity-95 transition-opacity`}>
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <span className="text-2xl">{config.icon}</span>
                                                            <h3 className="text-xl font-bold">{categoryName}</h3>
                                                        </div>
                                                        <span className="bg-white/20 backdrop-blur px-4 py-1.5 rounded-full text-sm font-bold">
                                                            {records.length} record{records.length !== 1 ? 's' : ''}
                                                        </span>
                                                    </div>
                                                </summary>
                                                <div className="p-5 bg-gray-50">
                                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                                        {records.map((record, idx) => {
                                                            // Extract game data
                                                            const gameIds = record.gameIds ? record.gameIds.split(', ').map(g => g.trim()) : [];
                                                            const scores = record.score ? record.score.split('; ').map(s => s.trim()) : [];

                                                            // Get full game details for each gameId
                                                            const gameDetails = gameIds.map((gId, gIdx) => {
                                                                const game = gameMap[gId];
                                                                return {
                                                                    gameId: gId,
                                                                    score: scores[gIdx] || 'N/A',
                                                                    date: game?.date || 'Unknown',
                                                                    venue: game?.venue || 'Unknown venue',
                                                                    homeTeam: game?.homeTeam || '???',
                                                                    awayTeam: game?.awayTeam || '???'
                                                                };
                                                            });

                                                            // Try to parse players from detail
                                                            const playerPattern = /([A-Z][a-zÀ-ÿ]+(?:\\s+[A-Z][a-zÀ-ÿ'.]+)+)(?:\\s+\\(|\\s+—)/g;
                                                            const playerMatches = record.detail ? [...record.detail.matchAll(playerPattern)] : [];
                                                            const players = playerMatches.map(m => m[1].trim());

                                                            // Try to find player IDs from milestone data
                                                            const relatedMilestones = gameIds.length > 0
                                                                ? (data.milestones || []).filter(m => gameIds.includes(m.gameId))
                                                                : [];

                                                            return (
                                                                <div key={idx} className={`bg-white rounded-xl p-5 border-2 border-${config.color}-200 hover:border-${config.color}-400 hover:shadow-xl transition-all`}>
                                                                    {/* Header with title and value */}
                                                                    <div className="flex items-start justify-between gap-4 mb-4">
                                                                        <h4 className="text-lg font-bold text-gray-900 leading-tight flex-1">
                                                                            {record.record}
                                                                        </h4>
                                                                        <div className={`bg-gradient-to-br ${config.gradient} text-white rounded-xl px-4 py-2 min-w-[70px] text-center shadow-lg`}>
                                                                            <span className="text-3xl font-black leading-none block">{record.value}</span>
                                                                        </div>
                                                                    </div>

                                                                    {/* Parse details for integration into game rows */}
                                                                    {(() => {
                                                                        if (!record.detail) return null;
                                                                        const detail = record.detail.trim();

                                                                        // Pattern 1: "TEAM (X), TEAM (Y)" - paired stats per game
                                                                        const simpleTeamPattern = /^[A-Z]{2,3}\\s*\\(\\d+\\)(?:[,;]\\s*[A-Z]{2,3}\\s*\\(\\d+\\))*$/;
                                                                        if (simpleTeamPattern.test(detail)) {
                                                                            const teamStatPattern = /([A-Z]{2,3})\\s*\\((\\d+)\\)/g;
                                                                            const parsedTeamStats = [];
                                                                            let tsMatch;
                                                                            while ((tsMatch = teamStatPattern.exec(detail)) !== null) {
                                                                                parsedTeamStats.push({ team: tsMatch[1], stat: tsMatch[2] });
                                                                            }
                                                                            if (parsedTeamStats.length > 0) {
                                                                                record._parsedTeamStats = parsedTeamStats;
                                                                            }
                                                                            return null;
                                                                        }

                                                                        // Pattern 2: "TEAM (X unit)" format like "NYM (2 H)"
                                                                        const teamUnitPattern = /([A-Z]{2,3})\\s*\\((\\d+)\\s*([A-Za-z]+)\\)/g;
                                                                        const unitMatches = [...detail.matchAll(teamUnitPattern)];
                                                                        if (unitMatches.length > 0 && unitMatches.length === gameDetails.length) {
                                                                            record._teamUnitStats = unitMatches.map(m => ({
                                                                                team: m[1],
                                                                                value: m[2],
                                                                                unit: m[3]
                                                                            }));
                                                                            return null;
                                                                        }

                                                                        // Pattern 3: "TEAM (X): Player1, Player2" - extract team counts for game rows
                                                                        const teamPlayersPattern = /([A-Z]{2,3})\\s*\\((\\d+)\\):/g;
                                                                        const tpMatches = [...detail.matchAll(teamPlayersPattern)];
                                                                        if (tpMatches.length > 0) {
                                                                            // Group by pairs for each game
                                                                            const teamCounts = tpMatches.map(m => ({ team: m[1], count: m[2] }));
                                                                            record._teamCounts = teamCounts;
                                                                            return null;
                                                                        }

                                                                        // Pattern 4: Leaderboard "Name (stat)" - show as compact list only if no games
                                                                        const leaderPattern = /^([\\w\\s.'-]+)\\s*\\((\\d+)\\)(?:;\\s*([\\w\\s.'-]+)\\s*\\((\\d+)\\))*$/;
                                                                        if (leaderPattern.test(detail) && gameDetails.length === 0) {
                                                                            const playerStatsPattern = /([\\w\\s.'-]+)\\s*\\((\\d+)\\)/g;
                                                                            const playerStats = [];
                                                                            let match;
                                                                            while ((match = playerStatsPattern.exec(detail)) !== null) {
                                                                                playerStats.push({ name: match[1].trim(), stat: match[2] });
                                                                            }
                                                                            if (playerStats.length > 0) {
                                                                                return (
                                                                                    <div className="space-y-0.5">
                                                                                        {playerStats.slice(0, 5).map((p, pIdx) => (
                                                                                            <div key={pIdx} className="flex items-center justify-between text-sm py-0.5">
                                                                                                <span className="text-gray-800">{pIdx + 1}. {p.name}</span>
                                                                                                <span className="font-bold text-gray-600">{p.stat}</span>
                                                                                            </div>
                                                                                        ))}
                                                                                        {playerStats.length > 5 && (
                                                                                            <div className="text-xs text-gray-400">+{playerStats.length - 5} more</div>
                                                                                        )}
                                                                                    </div>
                                                                                );
                                                                            }
                                                                        }

                                                                        // Pattern 5: Player names/details for milestone records (HR events, cycles, etc.)
                                                                        // Show these as they contain important "who did it" info
                                                                        const recordTitle = record.record?.toLowerCase() || '';
                                                                        const isPlayerRecord = recordTitle.includes('hr') || recordTitle.includes('home run') ||
                                                                            recordTitle.includes('cycle') || recordTitle.includes('hit') ||
                                                                            recordTitle.includes('grand slam') || recordTitle.includes('walk-off') ||
                                                                            recordTitle.includes('strikeout') || recordTitle.includes('no-hit') ||
                                                                            recordTitle.includes('back-to-back');

                                                                        if (isPlayerRecord && detail.length > 0) {
                                                                            // Store for per-game display
                                                                            record._playerDetails = detail;
                                                                            return null;
                                                                        }

                                                                        // All other patterns - don't show separately, games are enough
                                                                        return null;
                                                                    })()}

                                                                    {/* Game display - clean and integrated */}
                                                                    {gameDetails.length > 0 && (
                                                                        <div>
                                                                            {gameDetails.length <= 5 ? (
                                                                                // Show games inline
                                                                                <div className="space-y-1.5">
                                                                                    {gameDetails.map((game, gIdx) => {
                                                                                        const teamCode = game.gameId.substring(0, 3);
                                                                                        const url = game.gameId && game.gameId !== 'UNKNOWN'
                                                                                            ? `https://www.baseball-reference.com/boxes/${teamCode}/${game.gameId}.shtml`
                                                                                            : null;
                                                                                        const displayScore = game.score !== 'N/A' ? game.score : (gameMap[game.gameId]?.score || '');

                                                                                        // Get stat info from various parsed patterns
                                                                                        // For "by One Team" records, 1 stat per game; for "Combined" records, 2 stats per game
                                                                                        const isSingleTeamRecord = (record.record || '').toLowerCase().includes('by one team') ||
                                                                                            (record.record || '').toLowerCase().includes('by one player');
                                                                                        const statsPerGame = isSingleTeamRecord ? 1 : 2;
                                                                                        const gameStats = record._parsedTeamStats
                                                                                            ? record._parsedTeamStats.slice(gIdx * statsPerGame, gIdx * statsPerGame + statsPerGame)
                                                                                            : null;
                                                                                        const unitStat = record._teamUnitStats?.[gIdx];
                                                                                        const teamCounts = record._teamCounts
                                                                                            ? record._teamCounts.slice(gIdx * statsPerGame, gIdx * statsPerGame + statsPerGame)
                                                                                            : null;
                                                                                        // Get player details - either from parsed detail or from milestones
                                                                                        const playerDetailParts = record._playerDetails?.split(';').map(s => s.trim()) || [];
                                                                                        let playerDetail = playerDetailParts[gIdx] || (gameDetails.length === 1 ? record._playerDetails : null);

                                                                                        // If no player detail or it's a generic description, look up from milestones
                                                                                        const recordLower = (record.record || '').toLowerCase();
                                                                                        const isGenericDetail = !playerDetail ||
                                                                                            playerDetail.toLowerCase().includes('streak') ||
                                                                                            playerDetail.toLowerCase().includes('consecutive') ||
                                                                                            playerDetail.toLowerCase().includes('exactly');

                                                                                        if (isGenericDetail) {
                                                                                            // Find related milestones for this game
                                                                                            const gameMilestones = (data.milestones || []).filter(m => {
                                                                                                if (m.gameId !== game.gameId) return false;
                                                                                                const mType = (m.type || '').toLowerCase();
                                                                                                const mDetail = (m.detail || '').toLowerCase();

                                                                                                // For back-to-back HR events, match consecutive HR milestones
                                                                                                if (recordLower.includes('back-to-back') && mType.includes('consecutive')) {
                                                                                                    return true;
                                                                                                }
                                                                                                if (recordLower.includes('grand slam') && mType.includes('grand')) return true;
                                                                                                if (recordLower.includes('walk-off') && mType.includes('walk-off')) return true;
                                                                                                if (recordLower.includes('cycle') && mType.includes('cycle')) return true;
                                                                                                if (recordLower.includes('no-hit') && mType.includes('no-hit')) return true;
                                                                                                if (recordLower.includes('multi-hr') && mType.includes('multi-hr')) return true;
                                                                                                if (recordLower.includes('hit game') && mType.includes('hit')) return true;
                                                                                                if (recordLower.includes('rbi') && mType.includes('rbi')) return true;
                                                                                                if (recordLower.includes('strikeout') && (mType.includes('strikeout') || mType.includes('k game'))) return true;
                                                                                                return false;
                                                                                            });
                                                                                            if (gameMilestones.length > 0) {
                                                                                                playerDetail = gameMilestones.map(m => m.player || m.detail).filter(Boolean).join(', ');
                                                                                            }
                                                                                        }

                                                                                        return (
                                                                                            <a
                                                                                                key={gIdx}
                                                                                                href={url}
                                                                                                target="_blank"
                                                                                                rel="noopener noreferrer"
                                                                                                className="block py-2 px-3 rounded-lg hover:bg-gray-100 transition-colors group"
                                                                                            >
                                                                                                <div className="flex items-center justify-between">
                                                                                                    <div className="flex items-center gap-3 text-sm">
                                                                                                        <span className="font-bold text-gray-800">{game.awayTeam} @ {game.homeTeam}</span>
                                                                                                        {displayScore && (
                                                                                                            <span className="font-mono text-xs bg-gray-100 group-hover:bg-white px-2 py-0.5 rounded text-gray-600">
                                                                                                                {displayScore}
                                                                                                            </span>
                                                                                                        )}
                                                                                                        {gameStats && gameStats.length === 2 && (
                                                                                                            <span className="text-xs text-gray-500">
                                                                                                                ({gameStats.map(ts => `${ts.team}: ${ts.stat}`).join(', ')})
                                                                                                            </span>
                                                                                                        )}
                                                                                                        {unitStat && !gameStats && (
                                                                                                            <span className="text-xs font-semibold text-orange-600">
                                                                                                                {unitStat.team}: {unitStat.value} {unitStat.unit}
                                                                                                            </span>
                                                                                                        )}
                                                                                                        {teamCounts && teamCounts.length === 2 && !gameStats && !unitStat && (
                                                                                                            <span className="text-xs text-gray-500">
                                                                                                                ({teamCounts.map(tc => `${tc.team}: ${tc.count}`).join(', ')})
                                                                                                            </span>
                                                                                                        )}
                                                                                                        <span className="text-xs text-gray-400">{game.date}</span>
                                                                                                    </div>
                                                                                                    <span className="text-blue-500 group-hover:text-blue-700 opacity-50 group-hover:opacity-100">→</span>
                                                                                                </div>
                                                                                                {playerDetail && (
                                                                                                    <div className="text-xs text-gray-600 mt-1 ml-0 italic">
                                                                                                        {playerDetail}
                                                                                                    </div>
                                                                                                )}
                                                                                            </a>
                                                                                        );
                                                                                    })}
                                                                                </div>
                                                                            ) : (
                                                                                // For 6+ games, show compact expandable list
                                                                                <details>
                                                                                    <summary className="cursor-pointer text-sm text-gray-500 hover:text-blue-600">
                                                                                        {gameDetails.length} games
                                                                                    </summary>
                                                                                    <div className="mt-2 max-h-48 overflow-y-auto space-y-1">
                                                                                        {gameDetails.map((game, gIdx) => {
                                                                                            const teamCode = game.gameId.substring(0, 3);
                                                                                            const url = game.gameId && game.gameId !== 'UNKNOWN'
                                                                                                ? `https://www.baseball-reference.com/boxes/${teamCode}/${game.gameId}.shtml`
                                                                                                : null;
                                                                                            const displayScore = game.score !== 'N/A' ? game.score : (gameMap[game.gameId]?.score || '');
                                                                                            const unitStat = record._teamUnitStats?.[gIdx];
                                                                                            // For "by One Team" records, 1 stat per game; for "Combined" records, 2 stats per game
                                                                                            const isSingleTeamRecord = (record.record || '').toLowerCase().includes('by one team') ||
                                                                                                (record.record || '').toLowerCase().includes('by one player');
                                                                                            const statsPerGame = isSingleTeamRecord ? 1 : 2;
                                                                                            const gameStats = record._parsedTeamStats
                                                                                                ? record._parsedTeamStats.slice(gIdx * statsPerGame, gIdx * statsPerGame + statsPerGame)
                                                                                                : null;
                                                                                            const teamCounts = record._teamCounts
                                                                                                ? record._teamCounts.slice(gIdx * statsPerGame, gIdx * statsPerGame + statsPerGame)
                                                                                                : null;
                                                                                            const playerDetailParts = record._playerDetails?.split(';').map(s => s.trim()) || [];
                                                                                            let playerDetail = playerDetailParts[gIdx] || null;

                                                                                            // Look up from milestones if needed
                                                                                            const recordLower = (record.record || '').toLowerCase();
                                                                                            const isGenericDetail = !playerDetail ||
                                                                                                playerDetail.toLowerCase().includes('streak') ||
                                                                                                playerDetail.toLowerCase().includes('consecutive') ||
                                                                                                playerDetail.toLowerCase().includes('exactly');

                                                                                            if (isGenericDetail) {
                                                                                                const gameMilestones = (data.milestones || []).filter(m => {
                                                                                                    if (m.gameId !== game.gameId) return false;
                                                                                                    const mType = (m.type || '').toLowerCase();
                                                                                                    const mDetail = (m.detail || '').toLowerCase();

                                                                                                    // For back-to-back HR events, match consecutive HR milestones
                                                                                                    if (recordLower.includes('back-to-back') && mType.includes('consecutive')) {
                                                                                                        return true;
                                                                                                    }
                                                                                                    if (recordLower.includes('grand slam') && mType.includes('grand')) return true;
                                                                                                    if (recordLower.includes('walk-off') && mType.includes('walk-off')) return true;
                                                                                                    if (recordLower.includes('cycle') && mType.includes('cycle')) return true;
                                                                                                    if (recordLower.includes('no-hit') && mType.includes('no-hit')) return true;
                                                                                                    if (recordLower.includes('multi-hr') && mType.includes('multi-hr')) return true;
                                                                                                    if (recordLower.includes('hit game') && mType.includes('hit')) return true;
                                                                                                    if (recordLower.includes('rbi') && mType.includes('rbi')) return true;
                                                                                                    if (recordLower.includes('strikeout') && (mType.includes('strikeout') || mType.includes('k game'))) return true;
                                                                                                    return false;
                                                                                                });
                                                                                                if (gameMilestones.length > 0) {
                                                                                                    playerDetail = gameMilestones.map(m => m.player || m.detail).filter(Boolean).join(', ');
                                                                                                }
                                                                                            }

                                                                                            return (
                                                                                                <a
                                                                                                    key={gIdx}
                                                                                                    href={url}
                                                                                                    target="_blank"
                                                                                                    rel="noopener noreferrer"
                                                                                                    className="block text-xs py-1.5 px-2 rounded hover:bg-gray-100 transition-colors group"
                                                                                                >
                                                                                                    <div className="flex items-center justify-between">
                                                                                                        <span>
                                                                                                            <span className="font-semibold text-gray-700">{game.awayTeam} @ {game.homeTeam}</span>
                                                                                                            {displayScore && <span className="text-gray-500 ml-2">{displayScore}</span>}
                                                                                                            {gameStats && gameStats.length === 2 && (
                                                                                                                <span className="text-gray-500 ml-2">
                                                                                                                    ({gameStats.map(ts => `${ts.team}: ${ts.stat}`).join(', ')})
                                                                                                                </span>
                                                                                                            )}
                                                                                                            {unitStat && !gameStats && (
                                                                                                                <span className="text-orange-600 font-semibold ml-2">
                                                                                                                    {unitStat.team}: {unitStat.value} {unitStat.unit}
                                                                                                                </span>
                                                                                                            )}
                                                                                                            {teamCounts && teamCounts.length === 2 && !gameStats && !unitStat && (
                                                                                                                <span className="text-gray-500 ml-2">
                                                                                                                    ({teamCounts.map(tc => `${tc.team}: ${tc.count}`).join(', ')})
                                                                                                                </span>
                                                                                                            )}
                                                                                                            <span className="text-gray-400 ml-2">{game.date}</span>
                                                                                                        </span>
                                                                                                        <span className="text-blue-500 opacity-0 group-hover:opacity-100">→</span>
                                                                                                    </div>
                                                                                                    {playerDetail && (
                                                                                                        <div className="text-gray-500 italic mt-0.5 ml-0">{playerDetail}</div>
                                                                                                    )}
                                                                                                </a>
                                                                                            );
                                                                                        })}
                                                                                    </div>
                                                                                </details>
                                                                            )}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            </details>
                                        </div>
                                    );
                                })}
                            </div>
                        );
                    })()}
                </div>
            )}

            {/* Patterns View */}
            {insightsView === 'patterns' && (
                <div className="space-y-6">
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">📊 Your Attendance Patterns</h2>
                        </div>
                        <div className="p-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                                <StatCard title="Favorite Month" value={attendancePatterns.favoriteMonth} subtitle={`${attendancePatterns.favoriteMonthCount} games`} color="blue" />
                                <StatCard title="Favorite Day" value={attendancePatterns.favoriteDay} subtitle={`${attendancePatterns.favoriteDayCount} games`} color="green" />
                                <StatCard title="Most Seen Team" value={attendancePatterns.favoriteTeam} subtitle={`${attendancePatterns.favoriteTeamCount} games`} color="purple" />
                                <StatCard title="Favorite Venue" value={attendancePatterns.favoriteVenue.substring(0, 20)} subtitle={`${attendancePatterns.favoriteVenueCount} visits`} color="orange" />
                            </div>
                            
                            {/* Day of Week Chart */}
                            <div className="bg-gray-50 rounded-lg p-4 mb-6">
                                <h3 className="subsection-title font-bold mb-4">Games by Day of Week</h3>
                                <div className="relative" style={{ height: '192px' }}>
                                    <div className="absolute inset-0 flex items-end justify-between gap-2">
                                        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, idx) => {
                                            const count = attendancePatterns.byDayOfWeek[idx];
                                            const maxCount = Math.max(...attendancePatterns.byDayOfWeek);
                                            const heightPercent = maxCount > 0 ? (count / maxCount) * 100 : 0;
                                            return (
                                                <div key={day} className="flex-1 flex flex-col items-center justify-end h-full">
                                                    <div 
                                                        className="w-full bg-blue-600 rounded-t transition-all hover:bg-blue-700 flex items-start justify-center pt-2" 
                                                        style={{ height: `${heightPercent}%`, minHeight: count > 0 ? '30px' : '0' }}
                                                    >
                                                        {count > 0 && (
                                                            <span className="small-text text-white font-bold">{count}</span>
                                                        )}
                                                    </div>
                                                    <span className="small-text text-gray-600 font-medium mt-2">{day}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                            
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <h3 className="subsection-title font-bold mb-4">Top 10 Teams (Click to Filter)</h3>
                                    <div className="space-y-2">
                                        {Object.entries(attendancePatterns.byTeam).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([team, count], idx) => (
                                            <div key={idx} 
                                                 onClick={() => setSelectedTeam(team)}
                                                 className="flex items-center justify-between p-2 bg-white rounded border cursor-pointer hover:bg-blue-50 hover:border-blue-300 transition-colors">
                                                <div className="flex items-center gap-2">
                                                    <span className="small-text text-gray-500 w-6">{idx + 1}.</span>
                                                    <span className="body-text font-semibold text-gray-700">{team}</span>
                                                </div>
                                                <span className="small-text font-bold text-blue-600">{count}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <p className="text-center small-text text-gray-500 mt-3">💡 Click any team to filter</p>
                                </div>
                                
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <h3 className="subsection-title font-bold mb-4">Top 10 Venues</h3>
                                    <div className="space-y-2">
                                        {Object.entries(attendancePatterns.byVenue).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([venue, count], idx) => (
                                            <div key={idx} className="flex items-center justify-between p-2 bg-white rounded border">
                                                <div className="flex items-center gap-2">
                                                    <span className="small-text text-gray-500 w-6">{idx + 1}.</span>
                                                    <span className="body-text text-gray-700" title={venue}>{venue.length > 30 ? venue.substring(0, 30) + '...' : venue}</span>
                                                </div>
                                                <span className="small-text font-bold text-blue-600">{count}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Progress View */}
            {insightsView === 'progress' && (
                <div className="space-y-6">
                    {/* Teams Progress */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">🎯 Bucket List: All 30 MLB Teams</h2>
                        </div>
                        <div className="p-4">
                            <div className="mb-4">
                                <div className="flex justify-between body-text text-gray-600 mb-2">
                                    <span className="font-semibold">Progress: {bucketList.teamsCompleted} of {bucketList.totalMLBTeams} teams</span>
                                    <span className="font-bold text-blue-600">{Math.round((bucketList.teamsCompleted / bucketList.totalMLBTeams) * 100)}%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                                    <div 
                                        className="bg-gradient-to-r from-green-500 to-green-600 h-4 rounded-full transition-all duration-500 flex items-center justify-end px-2" 
                                        style={{ width: `${(bucketList.teamsCompleted / bucketList.totalMLBTeams) * 100}%` }}
                                    >
                                        {bucketList.teamsCompleted > 0 && (
                                            <span className="text-white text-xs font-bold">{bucketList.teamsCompleted}/{bucketList.totalMLBTeams}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            {bucketList.unseenTeams.length > 0 ? (
                                <div>
                                    <p className="body-text text-gray-700 font-medium mb-2">Still to see:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {bucketList.unseenTeams.map(team => (
                                            <span key={team} className="px-3 py-1 bg-red-100 text-red-700 body-text rounded-full font-semibold">{team}</span>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-4">
                                    <p className="text-4xl mb-2">🎉</p>
                                    <p className="body-text text-green-600 font-bold text-lg">You've seen all 30 MLB teams!</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* MLB Stadiums Progress */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">🏟️ Bucket List: All 30 Current MLB Stadiums</h2>
                        </div>
                        <div className="p-4">
                            <div className="mb-4">
                                <div className="flex justify-between body-text text-gray-600 mb-2">
                                    <span className="font-semibold">Progress: {bucketList.stadiumsVisited} of {bucketList.totalMLBStadiums} stadiums</span>
                                    <span className="font-bold text-blue-600">{Math.round((bucketList.stadiumsVisited / bucketList.totalMLBStadiums) * 100)}%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                                    <div 
                                        className="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-500 flex items-center justify-end px-2" 
                                        style={{ width: `${(bucketList.stadiumsVisited / bucketList.totalMLBStadiums) * 100}%` }}
                                    >
                                        {bucketList.stadiumsVisited > 0 && (
                                            <span className="text-white text-xs font-bold">{bucketList.stadiumsVisited}/{bucketList.totalMLBStadiums}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            
                            {bucketList.unseenStadiums.length > 0 ? (
                                <div>
                                    <p className="body-text text-gray-700 font-medium mb-3">
                                        <span className="text-red-600 font-bold">{bucketList.unseenStadiums.length}</span> stadiums remaining:
                                    </p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                        {bucketList.unseenStadiums.map(stadium => (
                                            <div key={stadium} className="px-3 py-2 bg-red-50 text-red-700 body-text rounded-lg border border-red-200">
                                                ❌ {stadium}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-4">
                                    <p className="text-4xl mb-2">🎊</p>
                                    <p className="body-text text-blue-600 font-bold text-lg">You've visited all 30 current MLB stadiums!</p>
                                </div>
                            )}
                            
                            {bucketList.visitedStadiumsList.length > 0 && (
                                <div className="mt-6">
                                    <details className="cursor-pointer">
                                        <summary className="body-text font-semibold text-gray-700 hover:text-blue-600">
                                            ✓ View visited stadiums ({bucketList.visitedStadiumsList.length})
                                        </summary>
                                        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
                                            {bucketList.visitedStadiumsList.map(stadium => (
                                                <div key={stadium} className="px-3 py-2 bg-green-50 text-green-700 body-text rounded-lg border border-green-200">
                                                    ✓ {stadium}
                                                </div>
                                            ))}
                                        </div>
                                    </details>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Orioles Stadium Quest */}
                    <div className="bg-white rounded-lg shadow border-2 border-orange-300">
                        <div className="p-4 border-b bg-gradient-to-r from-orange-50 to-orange-100">
                            <h2 className="section-title font-bold text-orange-900">🧡 Special Quest: See Orioles at All 30 MLB Stadiums</h2>
                            <p className="body-text text-orange-700 mt-1">Track your journey watching the O's across every MLB park</p>
                        </div>
                        <div className="p-4">
                            <div className="mb-4">
                                <div className="flex justify-between body-text text-gray-600 mb-2">
                                    <span className="font-semibold">Progress: {bucketList.oriolesStadiumsVisited} of {bucketList.totalMLBStadiums} stadiums</span>
                                    <span className="font-bold text-orange-600">{Math.round((bucketList.oriolesStadiumsVisited / bucketList.totalMLBStadiums) * 100)}%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                                    <div 
                                        className="bg-gradient-to-r from-orange-500 to-orange-600 h-4 rounded-full transition-all duration-500 flex items-center justify-end px-2" 
                                        style={{ width: `${(bucketList.oriolesStadiumsVisited / bucketList.totalMLBStadiums) * 100}%` }}
                                    >
                                        {bucketList.oriolesStadiumsVisited > 0 && (
                                            <span className="text-white text-xs font-bold">{bucketList.oriolesStadiumsVisited}/{bucketList.totalMLBStadiums}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            
                            {bucketList.oriolesUnseenStadiums.length > 0 ? (
                                <div>
                                    <p className="body-text text-gray-700 font-medium mb-3">
                                        <span className="text-orange-600 font-bold">{bucketList.oriolesUnseenStadiums.length}</span> stadiums where you haven't seen the Orioles:
                                    </p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                        {bucketList.oriolesUnseenStadiums.map(stadium => (
                                            <div key={stadium} className="px-3 py-2 bg-orange-50 text-orange-700 body-text rounded-lg border border-orange-200">
                                                🧡 {stadium}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-4">
                                    <p className="text-4xl mb-2">🏆</p>
                                    <p className="body-text text-orange-600 font-bold text-lg">Legendary! You've seen the Orioles at all 30 MLB stadiums!</p>
                                </div>
                            )}
                            
                            {bucketList.oriolesStadiumsList.length > 0 && (
                                <div className="mt-6">
                                    <details className="cursor-pointer">
                                        <summary className="body-text font-semibold text-gray-700 hover:text-orange-600">
                                            🧡 View stadiums with Orioles games ({bucketList.oriolesStadiumsList.length})
                                        </summary>
                                        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
                                            {bucketList.oriolesStadiumsList.map(stadium => (
                                                <div key={stadium} className="px-3 py-2 bg-orange-50 text-orange-700 body-text rounded-lg border border-orange-200 font-medium">
                                                    ✓ {stadium}
                                                </div>
                                            ))}
                                        </div>
                                    </details>
                                </div>
                            )}
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

    const displayData = useMemo(() => {
        if (!useFiltered || (!startDate && !endDate)) return allPlayers;
        const filteredGames = playerGames.filter(game => {
            if (startDate && game.dateSort < startDate) return false;
            if (endDate && game.dateSort > endDate) return false;
            return true;
        });
        return aggregateHitterStats(filteredGames);
    }, [allPlayers, playerGames, startDate, endDate, useFiltered]);

    // Transform data based on game type filter
    const gameTypeData = useMemo(() => {
        if (gameTypeFilter === 'all') return displayData;
        return displayData.map(player => {
            const g = player[getStatKey('games', gameTypeFilter)] || 0;
            if (g === 0) return null; // Filter out players with no games in this type
            const ab = player[getStatKey('ab', gameTypeFilter)] || 0;
            const pa = player[getStatKey('pa', gameTypeFilter)] || 0;
            const h = player[getStatKey('h', gameTypeFilter)] || 0;
            const bb = player[getStatKey('bb', gameTypeFilter)] || 0;
            const doubles = player[getStatKey('doubles', gameTypeFilter)] || 0;
            const triples = player[getStatKey('triples', gameTypeFilter)] || 0;
            const hr = player[getStatKey('hr', gameTypeFilter)] || 0;
            const singles = h - doubles - triples - hr;
            const tb = singles + 2*doubles + 3*triples + 4*hr;
            const obp = pa > 0 ? ((h + bb) / pa).toFixed(3) : '.000';
            const slg = ab > 0 ? (tb / ab).toFixed(3) : '.000';
            const ops = (parseFloat(obp) + parseFloat(slg)).toFixed(3);
            const gtTeam = player[getStatKey('team', gameTypeFilter)] || player.team;
            return {
                ...player,
                games: g,
                ab: ab,
                pa: pa,
                h: h,
                avg: player[getStatKey('avg', gameTypeFilter)] || '.000',
                r: player[getStatKey('r', gameTypeFilter)] || 0,
                rbi: player[getStatKey('rbi', gameTypeFilter)] || 0,
                hr: hr,
                doubles: doubles,
                triples: triples,
                sb: player[getStatKey('sb', gameTypeFilter)] || 0,
                bb: bb,
                so: player[getStatKey('so', gameTypeFilter)] || 0,
                obp: obp,
                slg: slg,
                ops: ops,
                team: gtTeam,
            };
        }).filter(p => p !== null);
    }, [displayData, gameTypeFilter]);

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
                    <PlayerLink playerId={r.playerId} name={v} />
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
                        {sorted.map((row, idx) => (
                            <tr key={idx} className="hover:bg-blue-50">
                                {columns.map(col => <td key={col.key} className="px-4 py-3 body-text">{col.render ? col.render(row[col.key], row) : row[col.key]}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            {selectedPlayer && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPlayer(null)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-purple-700 text-white">
                            <h3 className="section-title font-bold">Career Timeline</h3>
                            <button onClick={() => setSelectedPlayer(null)} className="text-white hover:text-gray-200 text-2xl leading-none">&times;</button>
                        </div>
                        <div className="overflow-y-auto p-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>
                            <PlayerTimeline 
                                playerId={selectedPlayer.id}
                                playerName={selectedPlayer.name}
                                playerGames={playerGames}
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

    const displayData = useMemo(() => {
        if (!useFiltered || (!startDate && !endDate)) return allPitchers;
        const filteredGames = pitcherGames.filter(game => {
            if (startDate && game.dateSort < startDate) return false;
            if (endDate && game.dateSort > endDate) return false;
            return true;
        });
        return aggregatePitcherStats(filteredGames);
    }, [allPitchers, pitcherGames, startDate, endDate, useFiltered]);

    // Transform data based on game type filter
    const gameTypeData = useMemo(() => {
        if (gameTypeFilter === 'all') return displayData;
        return displayData.map(pitcher => {
            const g = pitcher[getStatKey('games', gameTypeFilter)] || 0;
            if (g === 0) return null; // Filter out pitchers with no games in this type
            const ip = pitcher[getStatKey('ip', gameTypeFilter)] || '0.0';
            const h = pitcher[getStatKey('h', gameTypeFilter)] || 0;
            const bb = pitcher[getStatKey('bb', gameTypeFilter)] || 0;
            // Calculate WHIP for filtered stats
            const ipNum = parseFloat(ip);
            const whip = ipNum > 0 ? ((h + bb) / ipNum).toFixed(3) : 'N/A';
            const gtTeam = pitcher[getStatKey('team', gameTypeFilter)] || pitcher.team;
            return {
                ...pitcher,
                games: g,
                gameStarts: pitcher[getStatKey('gameStarts', gameTypeFilter)] || 0,
                wins: pitcher[getStatKey('wins', gameTypeFilter)] || 0,
                losses: pitcher[getStatKey('losses', gameTypeFilter)] || 0,
                saves: pitcher[getStatKey('saves', gameTypeFilter)] || 0,
                ip: ip,
                era: pitcher[getStatKey('era', gameTypeFilter)] || 'N/A',
                whip: whip,
                h: h,
                er: pitcher[getStatKey('er', gameTypeFilter)] || 0,
                bb: bb,
                so: pitcher[getStatKey('so', gameTypeFilter)] || 0,
                team: gtTeam,
            };
        }).filter(p => p !== null);
    }, [displayData, gameTypeFilter]);

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
                    <PlayerLink playerId={r.playerId} name={v} />
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
                        {sorted.map((row, idx) => (
                            <tr key={idx} className="hover:bg-blue-50">
                                {columns.map(col => <td key={col.key} className="px-4 py-3 body-text">{col.render ? col.render(row[col.key], row) : row[col.key]}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            {selectedPitcher && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedPitcher(null)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-purple-700 text-white">
                            <h3 className="section-title font-bold">Career Timeline</h3>
                            <button onClick={() => setSelectedPitcher(null)} className="text-white hover:text-gray-200 text-2xl leading-none">&times;</button>
                        </div>
                        <div className="overflow-y-auto p-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>
                            <PitcherTimeline 
                                playerId={selectedPitcher.id}
                                playerName={selectedPitcher.name}
                                pitcherGames={pitcherGames}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const DataTable = ({ data, columns, title, defaultSortKey = null, filterOptions = null, enableDateFilter = false, enableExport = true }) => {
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
                        {enableExport && <button onClick={() => exportToCSV(sorted, columns, `${title.replace(/[^a-z0-9]/gi, '_')}.csv`)} className="px-3 py-1 bg-green-600 text-white body-text rounded hover:bg-green-700">📥 Export</button>}
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
            <div className="overflow-x-auto" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="w-full">
                    <thead className="bg-gray-50 sticky top-0">
                        <tr>{columns.map(col => <th key={col.key} onClick={() => handleSort(col.key)} className="px-4 py-3 text-left small-text font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100">{col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y">
                        {sorted.map((row, idx) => (
                            <tr key={idx} className="hover:bg-blue-50">
                                {columns.map(col => <td key={col.key} className="px-4 py-3 body-text">{col.render ? col.render(row[col.key], row) : row[col.key]}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
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
            avg: [...qualified].sort((a, b) => parseFloat(b.avg) - parseFloat(a.avg)).slice(0, 10),
            obp: [...qualified].sort((a, b) => parseFloat(b.obp) - parseFloat(a.obp)).slice(0, 10),
            slg: [...qualified].sort((a, b) => parseFloat(b.slg) - parseFloat(a.slg)).slice(0, 10),
            ops: [...qualified].sort((a, b) => parseFloat(b.ops) - parseFloat(a.ops)).slice(0, 10),
            hr: [...all].sort((a, b) => b.hr - a.hr).slice(0, 10),
            rbi: [...all].sort((a, b) => b.rbi - a.rbi).slice(0, 10),
            hits: [...all].sort((a, b) => b.h - a.h).slice(0, 10),
            runs: [...all].sort((a, b) => b.r - a.r).slice(0, 10),
            sb: [...all].sort((a, b) => b.sb - a.sb).slice(0, 10),
            doubles: [...all].sort((a, b) => b.doubles - a.doubles).slice(0, 10),
        };
    }, [playersData, minAB]);
    
    const pitchingLeaders = useMemo(() => {
        const all = pitchersData;
        const qualified = all.filter(p => parseFloat(p.ip) >= minIP);
        return {
            era: [...qualified].filter(p => p.era !== 'N/A').sort((a, b) => parseFloat(a.era) - parseFloat(b.era)).slice(0, 10),
            whip: [...qualified].filter(p => p.whip !== 'N/A').sort((a, b) => parseFloat(a.whip) - parseFloat(b.whip)).slice(0, 10),
            wins: [...all].sort((a, b) => b.wins - a.wins).slice(0, 10),
            so: [...all].sort((a, b) => b.so - a.so).slice(0, 10),
            saves: [...all].sort((a, b) => b.saves - a.saves).slice(0, 10),
            ip: [...all].sort((a, b) => parseFloat(b.ip) - parseFloat(a.ip)).slice(0, 10),
        };
    }, [pitchersData, minIP]);
    
    const LeaderCard = ({ title, leaders, stat, isRateStat = false }) => (
        <div className="bg-white rounded-lg shadow p-4">
            <h3 className="subsection-title font-bold text-gray-900 mb-1">{title}</h3>
            {isRateStat && <p className="small-text text-blue-600 italic mb-2">Qualified</p>}
            <div className="space-y-2">
                {leaders.map((player, idx) => (
                    <div key={idx} className="flex items-center justify-between py-1 border-b last:border-0">
                        <div className="flex items-center gap-2">
                            <span className="text-gray-500 body-text w-6">{idx + 1}.</span>
                            <PlayerLink playerId={player.playerId} name={player.name} />
                            <span className="small-text text-gray-500">({player.team})</span>
                        </div>
                        <span className="font-bold text-blue-600 body-text">{player[stat]}</span>
                    </div>
                ))}
            </div>
        </div>
    );
    
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

const MilestonesView = ({ milestones, games, careerFirsts, allTimePassings }) => {
    const [activeCategory, setActiveCategory] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [showCareerFirsts, setShowCareerFirsts] = useState(true);
    const [careerMilestoneSort, setCareerMilestoneSort] = useState('event'); // 'event' or 'date'

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
                        { id: 'all', label: 'All', count: totalCount + careerFirstsCount + allTimePassingsCount },
                        { id: 'firsts', label: '⭐ Career Milestones', count: careerFirstsCount },
                        { id: 'passings', label: '📈 All-Time List', count: allTimePassingsCount },
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
                                const shortenMilestone = (m) => (m || '').replace('First Career ', '1st ').replace('Career ', '').replace('Home Run', 'HR').replace('Stolen Base', 'SB').replace('Run Scored', 'Run').replace('Strikeout', 'K').replace('Inning Pitched', 'IP').replace('Double', '2B').replace('Triple', '3B');

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
            {allTimePassings && allTimePassings.length > 0 && (activeCategory === 'all' || activeCategory === 'passings') && (
                <div className="bg-white rounded-xl shadow overflow-hidden">
                    <details open={true}>
                        <summary className="cursor-pointer p-4 bg-gradient-to-r from-purple-600 to-violet-700 text-white hover:opacity-95 transition-opacity">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">📈</span>
                                    <h3 className="text-lg font-bold">All-Time List Movements</h3>
                                </div>
                                <span className="bg-white/20 backdrop-blur px-3 py-1 rounded-full text-sm font-bold">
                                    {allTimePassings.length} passing{allTimePassings.length !== 1 ? 's' : ''}
                                </span>
                            </div>
                        </summary>
                        <div className="p-4 bg-gradient-to-b from-purple-50 to-white">
                            <p className="text-sm text-purple-700 mb-4">
                                Players who moved up the all-time leaderboards at games you attended
                            </p>
                            <div className="space-y-3">
                                {allTimePassings
                                    .filter(p => !searchTerm ||
                                        p.player_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                        p.stat_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                        (p.passed_players || []).some(pp => pp.name?.toLowerCase().includes(searchTerm.toLowerCase()))
                                    )
                                    .sort((a, b) => a.new_rank - b.new_rank)  // Sort by rank (most notable first)
                                    .map((passing, idx) => {
                                        const playerUrl = passing.player_id
                                            ? `https://www.baseball-reference.com/players/${passing.player_id.charAt(0).toLowerCase()}/${passing.player_id}.shtml`
                                            : null;
                                        const gameUrl = passing.game_id
                                            ? `https://www.baseball-reference.com/boxes/${passing.game_id.substring(0, 3)}/${passing.game_id}.shtml`
                                            : null;

                                        // Check if this is a tie or a pass for each player
                                        // Only show "tied" distinction for top 100
                                        const passedPlayers = passing.passed_players || [];
                                        const isTied = passedPlayers.length > 0 && passedPlayers[0].value === passing.new_value;
                                        const showTiedLabel = isTied && passing.new_rank <= 100;

                                        // Build passed/tied names with their values
                                        // Format IP in baseball notation (X.1 = X and 1/3, X.2 = X and 2/3)
                                        const formatIP = (val) => {
                                            let whole = Math.floor(val);
                                            const frac = val - whole;
                                            // Convert decimal fraction to baseball thirds
                                            let thirds;
                                            if (frac < 0.17) thirds = 0;
                                            else if (frac < 0.5) thirds = 1;
                                            else if (frac < 0.84) thirds = 2;
                                            else { thirds = 0; whole++; }  // Round up
                                            return `${whole.toLocaleString()}.${thirds}`;
                                        };

                                        // Format stat value (use IP notation for innings)
                                        const formatStatValue = (val, stat) => {
                                            if (stat === 'IP') return formatIP(val);
                                            return Number.isInteger(val) ? val.toLocaleString() : val.toFixed(1);
                                        };

                                        // Show each passed player with their individual value
                                        const passedNamesWithValues = passedPlayers.map(p => {
                                            const valueStr = formatStatValue(p.value, passing.stat);
                                            return `${p.name} (${valueStr})`;
                                        }).join(', ');

                                        return (
                                            <div key={idx} className="bg-white border border-purple-200 rounded-lg p-4 hover:border-purple-400 hover:shadow transition-all">
                                                <div className="flex items-start gap-4">
                                                    <div className={`flex-shrink-0 w-12 h-12 ${passing.new_rank <= 10 ? 'bg-gradient-to-br from-yellow-400 to-amber-500' : passing.new_rank <= 50 ? 'bg-gradient-to-br from-purple-500 to-violet-600' : 'bg-gradient-to-br from-purple-400 to-purple-500'} rounded-full flex items-center justify-center text-white font-bold text-lg`}>
                                                        #{passing.new_rank}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-2 flex-wrap">
                                                            {playerUrl ? (
                                                                <a href={playerUrl} target="_blank" rel="noopener noreferrer" className="font-bold text-purple-700 hover:text-purple-900 hover:underline text-lg">
                                                                    {passing.player_name}
                                                                </a>
                                                            ) : (
                                                                <span className="font-bold text-gray-900 text-lg">{passing.player_name}</span>
                                                            )}
                                                            <span className="text-purple-600 font-medium">
                                                                {showTiedLabel ? 'tied' : 'passed'} {passedNamesWithValues || 'others'} in {passing.stat_name}
                                                            </span>
                                                        </div>
                                                        <div className="mt-1 text-sm text-gray-600">
                                                            <span className="font-semibold">{formatStatValue(passing.new_value, passing.stat)}</span>
                                                            <span className="text-gray-500"> career {passing.stat_name.toLowerCase()}</span>
                                                        </div>
                                                        <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                                                            <span>{passing.date_display || passing.date}</span>
                                                            {passing.venue && <span>@ {passing.venue}</span>}
                                                            {gameUrl && (
                                                                <a href={gameUrl} target="_blank" rel="noopener noreferrer" className="text-purple-500 hover:text-purple-700 font-medium">
                                                                    View Game →
                                                                </a>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                            </div>
                        </div>
                    </details>
                </div>
            )}

            {/* Milestone groups - hide when only viewing career firsts or passings */}
            {activeCategory !== 'firsts' && activeCategory !== 'passings' && (
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
                                                                    <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200 hover:border-rose-300 hover:shadow transition-all">
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
                                                <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200 hover:border-blue-300 hover:shadow transition-all">
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

const Dashboard = ({ data }) => {
    const [filteredGames, setFilteredGames] = useState(data.games || []);

    return (
        <div className="space-y-6">
            {/* Advanced Filters */}
            <AdvancedFilters
                games={data.games || []}
                onFilterChange={setFilteredGames}
            />
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard title="Filtered Games" value={filteredGames.length} subtitle={filteredGames.length < data.games?.length ? `of ${data.games?.length} total` : ''} color="blue" />
            <StatCard title="Players" value={data.players?.length || 0} color="green" />
            <StatCard title="Milestones" value={data.milestones?.length || 0} color="purple" />
            <StatCard title="Teams" value={data.teams?.length || 0} color="orange" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6"><MilestoneChart milestones={data.milestones} /></div>
            <div className="bg-white rounded-lg shadow p-6"><TeamChart teams={data.teams} /></div>
        </div>
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
                    key={i}
                    className={`px-1.5 py-0.5 rounded text-xs whitespace-nowrap ${badgeColors[badge.type] || 'bg-gray-100 text-gray-700'}`}
                    title={badge.title}
                >
                    {badge.text}
                </span>
            ))}
            {badges.length > 3 && (
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="px-1.5 py-0.5 rounded text-xs bg-gray-200 text-gray-600 hover:bg-gray-300 cursor-pointer"
                >
                    {expanded ? '−' : `+${badges.length - 3}`}
                </button>
            )}
        </div>
    );
};

const GameLogWithDetails = ({ games, playerGames, pitcherGames, careerFirstsByGame }) => {
    const [selectedGame, setSelectedGame] = useState(null);

    // Compute milestones for badge display
    const milestoneData = useMemo(() => computeGameMilestones(games), [games]);
    const gameMilestones = milestoneData.milestones || {};

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
        'career-first': 'bg-amber-100 text-amber-800 font-bold'
    };

    return (
        <>
            <DataTable
                title="📋 Game Log"
                data={games}
                defaultSortKey="date"
                enableDateFilter={true}
                filterOptions={[
                    { key: 'gameType', label: 'Game Type', displayFn: (v) => v === 'spring' ? 'Spring Training' : v === 'postseason' ? 'Postseason' : v === 'regular' ? 'Regular Season' : v },
                    { key: 'homeTeam', label: 'Home Team' },
                    { key: 'venue', label: 'Venue' }
                ]}
                columns={[
                    { key: 'date', label: 'Date' },
                    { key: 'awayTeam', label: 'Away' },
                    { key: 'homeTeam', label: 'Home' },
                    { key: 'score', label: 'Score' },
                    { key: 'venue', label: 'Venue' },
                    {
                        key: 'badges',
                        label: 'Badges',
                        render: (_, row) => {
                            // Combine regular badges with career first badges
                            const regularBadges = gameMilestones[row.gameId]?.badges || [];
                            const gameCareerFirsts = careerFirstsByGame?.[row.gameId] || [];
                            const shortenMilestone = (m) => (m || '').replace('First Career ', '1st ').replace('Career ', '').replace('Home Run', 'HR').replace('Stolen Base', 'SB').replace('Run Scored', 'Run').replace('Strikeout', 'K').replace('Inning Pitched', 'IP').replace('Double', '2B').replace('Triple', '3B');
                            const getLastName = (name) => { const parts = (name || '').split(' '); return parts[parts.length - 1] || name || '?'; };
                            const careerFirstBadges = gameCareerFirsts.map(f => ({
                                type: 'career-first',
                                text: `⭐ ${getLastName(f.player_name)}: ${shortenMilestone(f.milestone)}`,
                                title: `${f.player_name || 'Unknown'}'s ${f.milestone || 'milestone'}`
                            }));
                            const allBadges = [...regularBadges, ...careerFirstBadges];
                            return (
                                <BadgeCell
                                    badges={allBadges}
                                    badgeColors={badgeColors}
                                />
                            );
                        }
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

const App = () => {
    const [tab, setTab] = useState('dashboard');
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('baseballDarkMode');
        if (saved !== null) return saved === 'true';
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });

    useEffect(() => {
        document.documentElement.classList.toggle('dark', darkMode);
        localStorage.setItem('baseballDarkMode', darkMode);
    }, [darkMode]);

    const data = BASEBALL_DATA;

    const tabs = [
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'gamelog', label: 'Games', icon: '📋' },
        { id: 'calendar', label: 'Calendar', icon: '📅' },
        { id: 'progress', label: 'Progress', icon: '🏁' },  // Combined: divisions + badges
        { id: 'milestones', label: 'Milestones', icon: '🏆' },
        { id: 'leaderboards', label: 'Leaders', icon: '🏅' },
        { id: 'players', label: 'Hitters', icon: '👤' },
        { id: 'pitchers', label: 'Pitchers', icon: '⚾' },
        { id: 'venues', label: 'Venues', icon: '🏟️' },  // Combined: teams + stadiums + map
        { id: 'matchups', label: 'Matchups', icon: '🎯' },
        { id: 'special', label: 'Special', icon: '🌟' },  // Combined: debuts + finals + signature
        { id: 'companions', label: 'With', icon: '👥' },
        { id: 'orioles', label: 'Orioles', icon: '🧡' },
    ];
    
    return (
        <div className={`min-h-screen transition-colors duration-200 ${darkMode ? 'bg-gray-900' : 'bg-gradient-to-br from-gray-50 to-gray-100'}`}>
            <header className={`shadow-2xl ${darkMode ? 'bg-gradient-to-r from-gray-800 via-gray-900 to-gray-800' : 'bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700'} text-white`}>
                <div className="max-w-7xl mx-auto px-4 py-8 flex justify-between items-start">
                    <div>
                        <h1 className="page-title font-bold">⚾ Baseball Statistics Portal</h1>
                        <p className={`body-text mt-2 ${darkMode ? 'text-gray-300' : 'text-blue-100'}`}>{data.games?.length || 0} games • {data.playerGames?.length || 0} player-games</p>
                    </div>
                    <button
                        onClick={() => setDarkMode(!darkMode)}
                        className={`px-4 py-2 rounded-lg transition-colors ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-white/20 hover:bg-white/30'}`}
                        title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                    >
                        {darkMode ? '☀️' : '🌙'}
                    </button>
                </div>
            </header>
            <nav className={`shadow-md sticky top-0 z-50 border-b-2 overflow-x-auto ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-blue-100'}`}>
                <div className="max-w-7xl mx-auto px-4">
                    <div className="flex space-x-1">
                        {tabs.map(t => (
                            <button key={t.id} onClick={() => setTab(t.id)} className={`px-4 py-3 font-medium body-text whitespace-nowrap transition-all ${
                                tab === t.id
                                    ? (darkMode ? 'bg-gray-700 text-blue-400 border-b-4 border-blue-400' : 'bg-blue-50 text-blue-600 border-b-4 border-blue-600')
                                    : (darkMode ? 'text-gray-300 hover:bg-gray-700 border-b-4 border-transparent' : 'text-gray-600 hover:bg-gray-50 border-b-4 border-transparent')
                            }`}>
                                <span className="mr-1">{t.icon}</span>{t.label}
                            </button>
                        ))}
                    </div>
                </div>
            </nav>
            <main className="max-w-7xl mx-auto px-4 py-8">
                {tab === 'dashboard' && <Dashboard data={data} />}
                {tab === 'gamelog' && <GameLogWithDetails games={data.games || []} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} careerFirstsByGame={data.careerFirstsByGame || {}} />}
                {tab === 'calendar' && <Calendar games={data.games || []} />}
                {tab === 'progress' && (
                    <div className="space-y-6">
                        <DivisionChecklist divisionChecklist={data.divisionChecklist} games={data.games || []} />
                        <BadgesDisplay games={data.games || []} />
                    </div>
                )}
                {tab === 'milestones' && <MilestonesView milestones={data.milestones || []} games={data.games || []} careerFirsts={data.careerFirsts || []} allTimePassings={data.allTimePassings || []} />}
                {tab === 'leaderboards' && <Leaderboards data={data} />}
                {tab === 'players' && <DynamicPlayerTable allPlayers={data.players || []} playerGames={data.playerGames || []} />}
                {tab === 'pitchers' && <DynamicPitcherTable allPitchers={data.pitchers || []} pitcherGames={data.pitcherGames || []} />}
                {tab === 'venues' && (
                    <div className="space-y-6">
                        <StadiumMap stadiums={data.stadiums || []} games={data.games || []} orioles={data.orioles || []} />
                        <DataTable title="🏟️ Teams" data={data.teams || []} defaultSortKey="games" columns={[
                            { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'record', label: 'Record' },
                            { key: 'runs', label: 'R' }, { key: 'runsAllowed', label: 'RA' }, { key: 'diff', label: 'Diff' },
                            { key: 'homeRecord', label: 'Home' }, { key: 'awayRecord', label: 'Away' },
                            { key: 'oneRunGames', label: '1-Run' }, { key: 'blowouts', label: 'Blowouts' }
                        ]} />
                        <DataTable title="🏟️ Stadiums" data={data.stadiums || []} defaultSortKey="games" columns={[
                            { key: 'stadium', label: 'Stadium' }, { key: 'games', label: 'G' }, { key: 'firstVisit', label: 'First' },
                            { key: 'lastVisit', label: 'Last' }, { key: 'span', label: 'Span' }, { key: 'avgAttendance', label: 'Avg Att.' },
                            { key: 'homeRunsSeen', label: 'HRs' }, { key: 'hitsSeen', label: 'Hits' }, { key: 'strikeoutsSeen', label: 'SOs' },
                            { key: 'teamsSeen', label: 'Teams' }, { key: 'homeTeamRecord', label: 'Home Record' }
                        ]} />
                    </div>
                )}
                {tab === 'matchups' && <MatchupMatrix matchupData={data.matchupMatrix} games={data.games || []} />}
                {tab === 'special' && (
                    <div className="space-y-6">
                        <DataTable title="🌟 MLB Debuts" data={data.debuts || []} defaultSortKey="date" enableDateFilter={true} columns={[
                            { key: 'date', label: 'Date' }, { key: 'player', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                            { key: 'team', label: 'Team' }, { key: 'opponent', label: 'vs' }, { key: 'position', label: 'Pos' },
                            { key: 'stats', label: 'Debut Performance', render: (v, r) => {
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
                            }},
                            { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                        ]} />
                        <DataTable title="👋 Final MLB Games" data={data.finalGames || []} defaultSortKey="date" enableDateFilter={true} columns={[
                            { key: 'date', label: 'Date' }, { key: 'player', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                            { key: 'team', label: 'Team' }, { key: 'position', label: 'Pos' },
                            { key: 'stats', label: 'Final Performance', render: (v, r) => {
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
                            }},
                            { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                        ]} />
                        <DataTable title="💦 Signature HRs" data={data.signatureHRs || []} defaultSortKey="date" enableDateFilter={true} columns={[
                            { key: 'date', label: 'Date' }, { key: 'player', label: 'Player' }, { key: 'team', label: 'Team' },
                            { key: 'opponent', label: 'Opponent' }, { key: 'pitcher', label: 'Pitcher' }, { key: 'signatureNumber', label: 'Type' },
                            { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                        ]} />
                    </div>
                )}
                {tab === 'companions' && <CompanionsView companionData={data.companionData} />}
                {tab === 'orioles' && <OriolesDashboard orioles={data.orioles || []} games={data.games || []} />}
            </main>
            <footer className="bg-white border-t mt-12">
                <div className="max-w-7xl mx-auto px-4 py-8 text-center">
                    <p className="body-text text-gray-600 font-medium">Baseball Statistics Portal</p>
                    <p className="small-text text-gray-400">Enhanced insights with interactive filtering</p>
                </div>
            </footer>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
"""