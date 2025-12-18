"""
HTML and React component templates for the baseball statistics website.
Version with enhanced interactive insights and merged summary view.
"""
import json

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
    </style>
</head>
<body>
    <div id="root"></div>
    <script>const BASEBALL_DATA = {json_str};</script>
    <script type="text/babel">{react_code}</script>
</body>
</html>"""


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

const GameLink = ({ gameId }) => {
    if (!gameId || gameId === 'UNKNOWN') return <span className="small-text">{gameId}</span>;
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

const GameDetailsModal = ({ game, playerGames, pitcherGames, onClose }) => {
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
                <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
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
                    <GameLink gameId={game.gameId} />
                    <button onClick={onClose} className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 body-text font-medium">
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

const PlayerTimeline = ({ playerId, playerName, playerGames }) => {
    const timelineData = useMemo(() => {
        const gamesForPlayer = playerGames.filter(g => g.playerId === playerId);
        
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
    }, [playerId, playerGames]);
    
    if (timelineData.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="subsection-title font-bold mb-4">📊 Career Timeline</h3>
                <p className="body-text text-gray-500 text-center py-8">No games found for this player</p>
            </div>
        );
    }
    
    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="subsection-title font-bold mb-4">📊 Career Timeline - {playerName}</h3>
            
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
    );
};

const PitcherTimeline = ({ playerId, playerName, pitcherGames }) => {
    const timelineData = useMemo(() => {
        const gamesForPitcher = pitcherGames.filter(g => g.playerId === playerId);
        
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
    }, [playerId, pitcherGames]);
    
    if (timelineData.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="subsection-title font-bold mb-4">📊 Career Timeline</h3>
                <p className="body-text text-gray-500 text-center py-8">No games found for this pitcher</p>
            </div>
        );
    }
    
    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="subsection-title font-bold mb-4">📊 Pitching Career Timeline - {playerName}</h3>
            
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
                const cleanScore = game.score.replace(/\s*\(\d+\)\s*$/, '');
                const scores = cleanScore.match(/\d+/g);
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
    const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());
    const [selectedDate, setSelectedDate] = useState(null);
    const [showModal, setShowModal] = useState(false);
    
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
        // Use most recent year with games, fallback to current year
        const currentYear = new Date().getFullYear();
        const yearsWithGames = new Set();
        games.forEach(game => {
            const date = new Date(game.date);
            if (!isNaN(date)) yearsWithGames.add(date.getFullYear());
        });
        if (yearsWithGames.size === 0) return currentYear;
        return Math.max(...yearsWithGames);
    }, [games]);

    const calendarDays = useMemo(() => {
        const firstDay = new Date(year, selectedMonth, 1);
        const lastDay = new Date(year, selectedMonth + 1, 0);
        const startingDayOfWeek = firstDay.getDay();
        const daysInMonth = lastDay.getDate();
        const days = [];
        for (let i = 0; i < startingDayOfWeek; i++) days.push(null);
        for (let day = 1; day <= daysInMonth; day++) {
            const key = `${selectedMonth}-${day}`;
            const gamesOnDate = gamesByMonthDay[key] || [];
            days.push({ day, games: gamesOnDate, key });
        }
        return days;
    }, [selectedMonth, gamesByMonthDay, year]);
    
    const monthNames = ['March', 'April', 'May', 'June', 'July', 'August', 'September', 'October'];
    const monthIndices = [2, 3, 4, 5, 6, 7, 8, 9];
    
    const handleDateClick = (day) => {
        if (day && day.games.length > 0) {
            setSelectedDate(day);
            setShowModal(true);
        }
    };
    
    const monthStats = useMemo(() => {
        const gamesThisMonth = games.filter(game => {
            const date = new Date(game.date);
            return !isNaN(date) && date.getMonth() === selectedMonth;
        });
        const uniqueDates = new Set(gamesThisMonth.map(g => new Date(g.date).getDate()));
        return {
            totalGames: gamesThisMonth.length,
            uniqueDates: uniqueDates.size,
            avgPerDate: uniqueDates.size > 0 ? (gamesThisMonth.length / uniqueDates.size).toFixed(1) : 0
        };
    }, [games, selectedMonth]);
    
    return (
        <>
            <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                    <div className="flex justify-between items-center mb-4">
                        <div>
                            <h2 className="section-title font-bold">📅 Game Calendar Heatmap</h2>
                            <p className="small-text text-gray-500 mt-1">
                                {monthStats.totalGames} games in {monthNames[monthIndices.indexOf(selectedMonth)]} 
                                {monthStats.uniqueDates > 0 && ` • ${monthStats.uniqueDates} unique dates • ${monthStats.avgPerDate} avg per date`}
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="small-text text-gray-600">Legend:</span>
                            <div className="flex items-center gap-1">
                                <div className="w-6 h-6 bg-gray-50 border border-gray-200 rounded"></div>
                                <span className="small-text text-gray-500">0</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-6 h-6 bg-blue-100 border border-blue-200 rounded"></div>
                                <span className="small-text text-gray-500">1</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-6 h-6 bg-blue-400 border border-blue-500 rounded"></div>
                                <span className="small-text text-gray-500">2-3</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-6 h-6 bg-blue-600 border border-blue-700 rounded"></div>
                                <span className="small-text text-gray-500">4+</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                        {monthIndices.map((idx) => (
                            <button key={idx} onClick={() => setSelectedMonth(idx)} className={`px-4 py-2 body-text rounded-lg font-medium transition-all ${selectedMonth === idx ? 'bg-blue-600 text-white shadow-md' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>
                                {monthNames[monthIndices.indexOf(idx)]}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="p-6">
                    <div className="grid grid-cols-7 gap-2">
                        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                            <div key={day} className="text-center small-text font-semibold text-gray-600 pb-2">{day}</div>
                        ))}
                        {calendarDays.map((day, idx) => {
                            if (!day) return <div key={idx} className="aspect-square" />;
                            const hasGames = day.games.length > 0;
                            const bgColor = getHeatmapColor(day.games.length);
                            const textColor = getTextColor(day.games.length);
                            return (
                                <div key={idx} onClick={() => handleDateClick(day)} className={`aspect-square border-2 rounded-lg p-2 transition-all ${bgColor} ${hasGames ? 'cursor-pointer hover:scale-105 hover:shadow-lg' : ''}`}>
                                    <div className="flex flex-col h-full justify-between">
                                        <span className={`body-text font-semibold ${textColor}`}>{day.day}</span>
                                        {hasGames && (
                                            <div className="text-center">
                                                <span className={`small-text font-bold ${textColor}`}>{day.games.length}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
            {showModal && selectedDate && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                            <h3 className="section-title font-bold">{monthNames[monthIndices.indexOf(selectedMonth)]} {selectedDate.day} • All Years</h3>
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
                                            <GameLink gameId={game.gameId} />
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
                    <h2 className="section-title font-bold">🎯 Team Matchup Matrix</h2>
                    <p className="body-text text-gray-500 mt-1">Click any cell to see games between those teams</p>
                </div>
                <div className="overflow-x-auto p-4">
                    <table className="w-full border-collapse">
                        <thead>
                            <tr>
                                <th className="border p-2 bg-gray-100 small-text font-bold sticky left-0 z-10">Team</th>
                                {teams.map(team => (
                                    <th key={team} className="border p-2 bg-gray-50 small-text font-medium">{team}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {matrix.map((row, idx) => (
                                <tr key={idx} className="hover:bg-blue-50">
                                    <td className="border p-2 body-text font-bold bg-gray-100 sticky left-0 z-10">{row.team}</td>
                                    {teams.map(opponent => {
                                        const value = row[opponent];
                                        const isX = value === 'X';
                                        const hasGames = !isX && value > 0;
                                        return (
                                            <td key={opponent} onClick={() => hasGames && handleCellClick(row.team, opponent, value)} className={`border p-2 text-center body-text ${isX ? 'bg-gray-200 text-gray-400' : hasGames ? 'bg-blue-50 font-semibold cursor-pointer hover:bg-blue-100 hover:shadow-md transition-all' : ''}`}>
                                                {value === 'X' ? '—' : value}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="p-4 border-t bg-gray-50">
                    <div className="flex items-center gap-6 justify-center small-text text-gray-600">
                        <div className="flex items-center gap-2"><div className="w-6 h-6 bg-gray-200 border rounded"></div><span>Same team</span></div>
                        <div className="flex items-center gap-2"><div className="w-6 h-6 bg-white border rounded"></div><span>No games</span></div>
                        <div className="flex items-center gap-2"><div className="w-6 h-6 bg-blue-50 border rounded"></div><span>Click to view games</span></div>
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
                                                    <GameLink gameId={game.gameId} />
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

const SmartInsights = ({ data }) => {
    const [insightsView, setInsightsView] = useState('overview');
    const [selectedYear, setSelectedYear] = useState('all');
    const [selectedMonth, setSelectedMonth] = useState('all');
    const [selectedTeam, setSelectedTeam] = useState('all');
    
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
        
        return games;
    }, [data.games, selectedYear, selectedMonth, selectedTeam]);
    
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
            const aScore = a.score.replace(/\s*\(\d+\)\s*$/, '');
            const bScore = b.score.replace(/\s*\(\d+\)\s*$/, '');
            
            const aTotal = (aScore.match(/\d+/g) || []).reduce((sum, n) => sum + parseInt(n), 0);
            const bTotal = (bScore.match(/\d+/g) || []).reduce((sum, n) => sum + parseInt(n), 0);
            return bTotal - aTotal;
        }).slice(0, 5);
        
        // Closest games (1-run games)
        const closestGames = games.filter(game => {
            const scores = game.score.match(/\d+/g);
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
            
            // Determine winner
            const scores = game.score.match(/\d+/g);
            if (scores && scores.length === 2) {
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
    
    // On This Day games
    const onThisDayGames = useMemo(() => {
        return filteredGames.filter(game => {
            const gameDate = new Date(game.date);
            return !isNaN(gameDate) && gameDate.getMonth() === todayMonth && gameDate.getDate() === todayDay;
        }).sort((a, b) => new Date(b.date) - new Date(a.date));
    }, [filteredGames, todayMonth, todayDay]);
    
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
                    
                    {(selectedYear !== 'all' || selectedMonth !== 'all' || selectedTeam !== 'all') && (
                        <button 
                            onClick={() => { setSelectedYear('all'); setSelectedMonth('all'); setSelectedTeam('all'); }}
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
                {['overview', 'trends', 'summary', 'patterns', 'progress'].map(view => (
                    <button
                        key={view}
                        onClick={() => setInsightsView(view)}
                        className={`px-5 py-2.5 body-text rounded-lg font-semibold transition-all ${
                            insightsView === view 
                                ? 'bg-blue-600 text-white shadow-md' 
                                : 'bg-white text-gray-700 hover:bg-gray-100 shadow'
                        }`}
                    >
                        {view.charAt(0).toUpperCase() + view.slice(1)}
                    </button>
                ))}
            </div>
            
            {/* Overview View */}
            {insightsView === 'overview' && (
                <div className="space-y-6">
                    {/* On This Day */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">📅 On This Day in Baseball</h2>
                            <p className="body-text text-gray-500 mt-1">Games you attended on {today.toLocaleString('default', { month: 'long' })} {today.getDate()}</p>
                        </div>
                        <div className="p-4">
                            {onThisDayGames.length > 0 ? (
                                <div className="space-y-3">
                                    {onThisDayGames.map((game, idx) => (
                                        <div key={idx} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <span className="body-text font-bold text-blue-600">{game.date}</span>
                                                    <div className="flex items-center gap-2">
                                                        <span className="body-text font-semibold">{game.awayTeam}</span>
                                                        <span className="body-text text-gray-500">@</span>
                                                        <span className="body-text font-semibold">{game.homeTeam}</span>
                                                    </div>
                                                    <span className="font-mono body-text bg-white px-2 py-1 rounded">{game.score}</span>
                                                </div>
                                                <GameLink gameId={game.gameId} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="body-text text-gray-500 text-center py-8">No games attended on this date in previous years</p>
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
                                                        <GameLink gameId={game.gameId} />
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
                    
                    {/* Last Game */}
                    {timeSinceLastGame && (
                        <div className="bg-white rounded-lg shadow">
                            <div className="p-4 border-b">
                                <h2 className="section-title font-bold">⏱️ Last Game Attended</h2>
                            </div>
                            <div className="p-4">
                                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
                                    <div>
                                        <p className="body-text text-gray-600 mb-2">{timeSinceLastGame.message}</p>
                                        <div className="flex items-center gap-3">
                                            <span className="body-text font-bold">{timeSinceLastGame.game.awayTeam} @ {timeSinceLastGame.game.homeTeam}</span>
                                            <span className="font-mono body-text bg-white px-2 py-1 rounded">{timeSinceLastGame.game.score}</span>
                                            <span className="small-text text-gray-500">{timeSinceLastGame.game.date}</span>
                                        </div>
                                    </div>
                                    <GameLink gameId={timeSinceLastGame.game.gameId} />
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
            
            {/* Summary View - Enhanced with Categories and Charts */}
            {insightsView === 'summary' && (
                <div className="space-y-6">
                    {/* Quick Highlights */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {[
                            { label: 'Total Games', value: filteredGames.length, icon: '⚾', color: 'blue' },
                            { 
                                label: 'Multi-HR Games', 
                                value: (data.summary || []).find(s => s.record.includes('Multi-HR'))?.value || '0', 
                                icon: '💥', 
                                color: 'purple' 
                            },
                            { 
                                label: 'Extra Innings', 
                                value: (data.summary || []).find(s => s.record.includes('Extra Inning'))?.value || '0', 
                                icon: '⏱️', 
                                color: 'orange' 
                            },
                            { 
                                label: 'Walk-Off Wins', 
                                value: (data.milestones || []).filter(m => m.type === 'Walk-Offs').length, 
                                icon: '🎉', 
                                color: 'green' 
                            },
                        ].map((stat, idx) => (
                            <div key={idx} className={`bg-white rounded-lg shadow border-l-4 border-${stat.color}-500 p-4`}>
                                <div className="flex items-center gap-3">
                                    <span className="text-3xl">{stat.icon}</span>
                                    <div>
                                        <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                                        <div className="small-text text-gray-600 uppercase">{stat.label}</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Categorized Summary Stats */}
                    {(() => {
                        // Group summary records by category based on keywords
                        const categories = {
                            '🟩 Game Format': [],
                            '🟠 Hitting': [],
                            '🟤 Pitching': [],
                            '🟣 Home Runs': [],
                            '🔵 Offensive': [],
                            '🔴 Defensive & Runs Allowed': [],
                            '📊 Team Records': [],
                            '🟡 Baserunning': [],
                            '⚫️ Other': []
                        };
                        
                        (data.summary || []).forEach(row => {
                            const record = row.record.toLowerCase();
                            
                            // Categorize based on keywords
                            if (record.includes('extra inning') || record.includes('doubleheader') || 
                                record.includes('game length') || record.includes('attendance')) {
                                categories['🟩 Game Format'].push(row);
                            }
                            else if (record.includes('hr') || record.includes('home run') || 
                                     record.includes('grand slam')) {
                                categories['🟣 Home Runs'].push(row);
                            }
                            else if (record.includes('hit') && !record.includes('pitcher') || 
                                     record.includes('batting') || record.includes('cycle')) {
                                categories['🟠 Hitting'].push(row);
                            }
                            else if (record.includes('pitch') || record.includes('strikeout') || 
                                     record.includes(' k ') || record.includes('shutout') || 
                                     record.includes('complete game') || record.includes('quality start') ||
                                     record.includes('earned run')) {
                                categories['🟤 Pitching'].push(row);
                            }
                            else if (record.includes('run') && (record.includes('score') || record.includes('inning'))) {
                                categories['🔵 Offensive'].push(row);
                            }
                            else if (record.includes('runs allowed') || record.includes('fewest hit')) {
                                categories['🔴 Defensive & Runs Allowed'].push(row);
                            }
                            else if (record.includes('steal') || record.includes(' sb')) {
                                categories['🟡 Baserunning'].push(row);
                            }
                            else if (record.includes('team') || record.includes('combined')) {
                                categories['📊 Team Records'].push(row);
                            }
                            else {
                                categories['⚫️ Other'].push(row);
                            }
                        });
                        
                        // Render category cards
                        return (
                            <div className="space-y-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h2 className="section-title font-bold">📋 Summary by Category</h2>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => {
                                                document.querySelectorAll('.category-card details').forEach(d => d.open = true);
                                            }}
                                            className="px-3 py-1.5 body-text bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg font-semibold"
                                        >
                                            Expand All
                                        </button>
                                        <button
                                            onClick={() => {
                                                document.querySelectorAll('.category-card details').forEach(d => d.open = false);
                                            }}
                                            className="px-3 py-1.5 body-text bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-semibold"
                                        >
                                            Collapse All
                                        </button>
                                    </div>
                                </div>
                                
                                {Object.entries(categories).map(([category, records]) => {
                                    if (records.length === 0) return null;
                                    
                                    return (
                                        <div key={category} className="bg-white rounded-lg shadow category-card">
                                            <details open>
                                                <summary className="cursor-pointer p-4 hover:bg-blue-50 transition-colors rounded-lg">
                                                    <div className="flex items-center justify-between">
                                                        <h3 className="subsection-title font-bold inline">{category}</h3>
                                                        <span className="small-text text-gray-500 bg-blue-100 px-3 py-1 rounded-full font-semibold">
                                                            {records.length} records
                                                        </span>
                                                    </div>
                                                </summary>
                                                <div className="p-4 pt-0">
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                                                        {records.map((record, idx) => {
                                                            // Extract game data
                                                            const gameIds = record.gameIds ? record.gameIds.split(', ').map(g => g.trim()) : [];
                                                            const scores = record.score ? record.score.split('; ').map(s => s.trim()) : [];
                                                            
                                                            // Try to parse players from detail
                                                            // Look for patterns like "Name (stat)" or "Name —"
                                                            const playerPattern = /([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ'.]+)+)(?:\s+\(|\s+—)/g;
                                                            const playerMatches = record.detail ? [...record.detail.matchAll(playerPattern)] : [];
                                                            const players = playerMatches.map(m => m[1].trim());
                                                            
                                                            // Try to find player IDs from milestone data if this is a milestone-related record
                                                            const relatedMilestones = gameIds.length > 0 
                                                                ? (data.milestones || []).filter(m => gameIds.includes(m.gameId))
                                                                : [];
                                                            
                                                            return (
                                                                <div key={idx} className="bg-white rounded-xl p-5 border-2 border-gray-200 hover:border-blue-500 hover:shadow-xl transition-all">
                                                                    {/* Header with title and value */}
                                                                    <div className="flex items-start justify-between gap-4 mb-4">
                                                                        <h4 className="text-base font-bold text-gray-900 leading-tight flex-1">
                                                                            {record.record}
                                                                        </h4>
                                                                        <div className="bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg px-4 py-2 min-w-[60px] text-center">
                                                                            <span className="text-3xl font-black leading-none block">{record.value}</span>
                                                                        </div>
                                                                    </div>
                                                                    
                                                                    {/* Players involved - clickable */}
                                                                    {players.length > 0 && (
                                                                        <div className="mb-3">
                                                                            <div className="flex flex-wrap gap-2">
                                                                                {players.map((playerName, pIdx) => {
                                                                                    // Try to find this player's ID from milestones
                                                                                    const milestone = relatedMilestones.find(m => 
                                                                                        m.player && m.player.includes(playerName)
                                                                                    );
                                                                                    const playerId = milestone ? milestone.playerId : null;
                                                                                    
                                                                                    if (playerId && playerId !== 'UNKNOWN') {
                                                                                        return (
                                                                                            <a 
                                                                                                key={pIdx}
                                                                                                href={`https://www.baseball-reference.com/players/${playerId.charAt(0).toLowerCase()}/${playerId}.shtml`}
                                                                                                target="_blank"
                                                                                                rel="noopener noreferrer"
                                                                                                className="px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-800 rounded-full text-xs font-bold inline-flex items-center gap-1 transition-colors"
                                                                                            >
                                                                                                👤 {playerName}
                                                                                            </a>
                                                                                        );
                                                                                    } else {
                                                                                        return (
                                                                                            <span key={pIdx} className="px-3 py-1.5 bg-purple-100 text-purple-800 rounded-full text-xs font-bold inline-flex items-center gap-1">
                                                                                                👤 {playerName}
                                                                                            </span>
                                                                                        );
                                                                                    }
                                                                                })}
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    
                                                                    {/* Team/stat details */}
                                                                    {record.detail && (
                                                                        <div className="mb-3 bg-gray-50 rounded-lg p-3">
                                                                            <div className="small-text text-gray-700 leading-relaxed">
                                                                                {record.detail}
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    
                                                                    {/* Clickable score chips that link to games */}
                                                                    {scores.length > 0 && gameIds.length > 0 && (
                                                                        <div>
                                                                            <details open={scores.length <= 4}>
                                                                                <summary className="cursor-pointer small-text font-bold text-gray-700 mb-2 hover:text-blue-600">
                                                                                    📊 {scores.length} Game{scores.length !== 1 ? 's' : ''} {scores.length > 4 ? '(click to expand)' : ''}
                                                                                </summary>
                                                                                <div className="flex flex-wrap gap-2 mt-2">
                                                                                    {scores.map((score, sIdx) => {
                                                                                        const gameId = gameIds[sIdx];
                                                                                        if (!gameId || gameId === 'UNKNOWN') {
                                                                                            return (
                                                                                                <span key={sIdx} className="px-3 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 text-blue-900 rounded-lg font-mono text-xs font-bold">
                                                                                                    {score}
                                                                                                </span>
                                                                                            );
                                                                                        }
                                                                                        
                                                                                        const teamCode = gameId.substring(0, 3);
                                                                                        const url = `https://www.baseball-reference.com/boxes/${teamCode}/${gameId}.shtml`;
                                                                                        
                                                                                        return (
                                                                                            <a 
                                                                                                key={sIdx}
                                                                                                href={url}
                                                                                                target="_blank"
                                                                                                rel="noopener noreferrer"
                                                                                                className="px-3 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border-2 border-blue-200 hover:border-blue-400 text-blue-900 rounded-lg font-mono text-xs font-bold transition-all hover:shadow-md inline-block"
                                                                                                title={`View game: ${gameId}`}
                                                                                            >
                                                                                                {score}
                                                                                            </a>
                                                                                        );
                                                                                    })}
                                                                                </div>
                                                                            </details>
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
                    {/* Quick Stats Grid - Key Numbers */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="section-title font-bold">⚡ Key Numbers</h2>
                        </div>
                        <div className="p-6">
                            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                                {(() => {
                                    const keyStats = [
                                        { label: 'Total Games', value: filteredGames.length, color: 'blue' },
                                        { label: 'Players Seen', value: (data.players || []).length, color: 'green' },
                                        { label: 'Pitchers Seen', value: (data.pitchers || []).length, color: 'purple' },
                                        { label: 'Teams Seen', value: (data.teams || []).length, color: 'orange' },
                                        { label: 'Stadiums', value: (data.stadiums || []).length, color: 'blue' },
                                        { label: 'Milestones', value: (data.milestones || []).length, color: 'purple' },
                                    ];
                                    
                                    return keyStats.map((stat, idx) => (
                                        <div key={idx} className={`bg-${stat.color}-50 rounded-lg p-4 text-center border-2 border-${stat.color}-200`}>
                                            <div className={`text-3xl font-bold text-${stat.color}-600 mb-1`}>{stat.value}</div>
                                            <div className="small-text text-gray-600 font-medium">{stat.label}</div>
                                        </div>
                                    ));
                                })()}
                            </div>
                        </div>
                    </div>
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
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [useFiltered, setUseFiltered] = useState(false);
    const [selectedPlayer, setSelectedPlayer] = useState(null);
    
    useEffect(() => { setUseFiltered(!!(startDate || endDate)); }, [startDate, endDate]);
    
    const displayData = useMemo(() => {
        if (!useFiltered || (!startDate && !endDate)) return allPlayers;
        const filteredGames = playerGames.filter(game => {
            if (startDate && game.dateSort < startDate) return false;
            if (endDate && game.dateSort > endDate) return false;
            return true;
        });
        return aggregateHitterStats(filteredGames);
    }, [allPlayers, playerGames, startDate, endDate, useFiltered]);
    
    const filtered = useMemo(() => {
        let result = displayData;
        if (activeFilter !== 'all') result = result.filter(row => row.team.includes(activeFilter));
        if (search) result = result.filter(row => Object.values(row).some(val => String(val).toLowerCase().includes(search.toLowerCase())));
        return result;
    }, [displayData, search, activeFilter]);
    
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
    
    return (
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="section-title font-bold">👤 Hitter Statistics {useFiltered && <span className="small-text text-blue-600">(Date Filtered)</span>}</h2>
                    <div className="flex items-center gap-2">
                        <span className="body-text text-gray-500">{sorted.length} players</span>
                        <button onClick={() => exportToCSV(sorted, columns, 'Hitter_Statistics.csv')} className="px-3 py-1 bg-green-600 text-white body-text rounded hover:bg-green-700">📥 Export</button>
                    </div>
                </div>
                <div className="flex flex-wrap gap-4">
                    <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1 min-w-[200px] px-4 py-2 body-text border rounded-lg" />
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
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [useFiltered, setUseFiltered] = useState(false);
    const [selectedPitcher, setSelectedPitcher] = useState(null);
    
    useEffect(() => { setUseFiltered(!!(startDate || endDate)); }, [startDate, endDate]);
    
    const displayData = useMemo(() => {
        if (!useFiltered || (!startDate && !endDate)) return allPitchers;
        const filteredGames = pitcherGames.filter(game => {
            if (startDate && game.dateSort < startDate) return false;
            if (endDate && game.dateSort > endDate) return false;
            return true;
        });
        return aggregatePitcherStats(filteredGames);
    }, [allPitchers, pitcherGames, startDate, endDate, useFiltered]);
    
    const filtered = useMemo(() => {
        let result = displayData;
        if (activeFilter !== 'all') result = result.filter(row => row.team.includes(activeFilter));
        if (search) result = result.filter(row => Object.values(row).some(val => String(val).toLowerCase().includes(search.toLowerCase())));
        return result;
    }, [displayData, search, activeFilter]);
    
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
    
    return (
        <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b space-y-4">
                <div className="flex justify-between items-center">
                    <h2 className="section-title font-bold">⚾ Pitcher Statistics {useFiltered && <span className="small-text text-blue-600">(Date Filtered)</span>}</h2>
                    <div className="flex items-center gap-2">
                        <span className="body-text text-gray-500">{sorted.length} pitchers</span>
                        <button onClick={() => exportToCSV(sorted, columns, 'Pitcher_Statistics.csv')} className="px-3 py-1 bg-green-600 text-white body-text rounded hover:bg-green-700">📥 Export</button>
                    </div>
                </div>
                <div className="flex flex-wrap gap-4">
                    <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1 min-w-[200px] px-4 py-2 body-text border rounded-lg" />
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
    const [activeFilter, setActiveFilter] = useState('all');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    
    const filtered = useMemo(() => {
        let result = data;
        if (filterOptions && activeFilter !== 'all') result = result.filter(row => row[filterOptions.key] === activeFilter);
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
    }, [data, search, activeFilter, startDate, endDate]);
    
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
    
    const filterValues = useMemo(() => {
        if (!filterOptions) return [];
        return [...new Set(data.map(row => row[filterOptions.key]))].sort();
    }, [data, filterOptions]);
    
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
                            {(startDate || endDate) && <button onClick={() => { setStartDate(''); setEndDate(''); }} className="px-3 py-2 body-text text-gray-600 hover:text-gray-900">Clear</button>}
                        </>
                    )}
                    {filterOptions && (
                        <select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)} className="px-4 py-2 body-text border rounded-lg">
                            <option value="all">All {filterOptions.label}</option>
                            {filterValues.map(val => <option key={val} value={val}>{val}</option>)}
                        </select>
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

const GameLogWithDetails = ({ games, playerGames, pitcherGames }) => {
    const [selectedGame, setSelectedGame] = useState(null);
    
    return (
        <>
            <DataTable 
                title="📋 Game Log" 
                data={games} 
                defaultSortKey="date" 
                enableDateFilter={true} 
                columns={[
                    { key: 'date', label: 'Date' }, 
                    { key: 'awayTeam', label: 'Away' }, 
                    { key: 'homeTeam', label: 'Home' }, 
                    { key: 'score', label: 'Score' }, 
                    { key: 'venue', label: 'Venue' }, 
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
                    onClose={() => setSelectedGame(null)}
                />
            )}
        </>
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
        { id: 'insights', label: 'Insights', icon: '💡' },
        { id: 'leaderboards', label: 'Leaderboards', icon: '🏅' },
        { id: 'calendar', label: 'Calendar', icon: '📅' },
        { id: 'matchups', label: 'Matchups', icon: '🎯' }, 
        { id: 'gamelog', label: 'Game Log', icon: '📋' },
        { id: 'milestones', label: 'Milestones', icon: '🏆' },
        { id: 'players', label: 'Hitters', icon: '👤' }, 
        { id: 'pitchers', label: 'Pitchers', icon: '⚾' },
        { id: 'teams', label: 'Teams', icon: '🏟️' }, 
        { id: 'stadiums', label: 'Stadiums', icon: '🏟️' },
        { id: 'orioles', label: 'Orioles', icon: '🧡' }, 
        { id: 'debuts', label: 'Debuts', icon: '🌟' },
        { id: 'finals', label: 'Final Games', icon: '👋' }, 
        { id: 'signature', label: 'Signature HRs', icon: '💦' },
        { id: 'nostats', label: 'No Stats', icon: '👥' },
        { id: 'comparison', label: 'Compare', icon: '⚖️' },
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
                {tab === 'insights' && <SmartInsights data={data} />}
                {tab === 'leaderboards' && <Leaderboards data={data} />}
                {tab === 'calendar' && <Calendar games={data.games || []} />}
                {tab === 'matchups' && <MatchupMatrix matchupData={data.matchupMatrix} games={data.games || []} />}
                {tab === 'gamelog' && <GameLogWithDetails games={data.games || []} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} />}
                {tab === 'milestones' && <DataTable title="🏆 Milestones" data={data.milestones || []} defaultSortKey="date" filterOptions={{ key: 'type', label: 'Types' }} enableDateFilter={true} columns={[
                    { key: 'date', label: 'Date' }, { key: 'player', label: 'Player', render: (v, r) => r.playerId ? <PlayerLink playerId={r.playerId} name={v} /> : v }, 
                    { key: 'team', label: 'Team' }, { key: 'type', label: 'Type' }, { key: 'detail', label: 'Details' }, { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                ]} />}
                {tab === 'players' && <DynamicPlayerTable allPlayers={data.players || []} playerGames={data.playerGames || []} />}
                {tab === 'pitchers' && <DynamicPitcherTable allPitchers={data.pitchers || []} pitcherGames={data.pitcherGames || []} />}
                {tab === 'teams' && <DataTable title="🏟️ Teams" data={data.teams || []} defaultSortKey="games" columns={[
                    { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'record', label: 'Record' }, 
                    { key: 'runs', label: 'R' }, { key: 'runsAllowed', label: 'RA' }, { key: 'diff', label: 'Diff' },
                    { key: 'homeRecord', label: 'Home' }, { key: 'awayRecord', label: 'Away' }, 
                    { key: 'oneRunGames', label: '1-Run' }, { key: 'blowouts', label: 'Blowouts' }
                ]} />}
                {tab === 'stadiums' && <DataTable title="🏟️ Stadiums" data={data.stadiums || []} defaultSortKey="games" columns={[
                    { key: 'stadium', label: 'Stadium' }, { key: 'games', label: 'G' }, { key: 'firstVisit', label: 'First' },
                    { key: 'lastVisit', label: 'Last' }, { key: 'span', label: 'Span' }, { key: 'avgAttendance', label: 'Avg Att.' },
                    { key: 'homeRunsSeen', label: 'HRs' }, { key: 'hitsSeen', label: 'Hits' }, { key: 'strikeoutsSeen', label: 'SOs' },
                    { key: 'teamsSeen', label: 'Teams' }, { key: 'homeTeamRecord', label: 'Home Record' }
                ]} />}
                {tab === 'orioles' && <DataTable title="🧡 Orioles by Stadium" data={data.orioles || []} defaultSortKey="games" columns={[
                    { key: 'stadium', label: 'Stadium' }, { key: 'games', label: 'G' }, { key: 'record', label: 'Record' },
                    { key: 'firstVisit', label: 'First' }, { key: 'lastVisit', label: 'Last' }, { key: 'runsScored', label: 'R' },
                    { key: 'runsAllowed', label: 'RA' }, { key: 'runDiff', label: 'Diff' }, { key: 'homeRunsHit', label: 'HR' }, { key: 'oneRunGames', label: '1-Run' }
                ]} />}
                {tab === 'debuts' && <DataTable title="🌟 MLB Debuts" data={data.debuts || []} defaultSortKey="date" enableDateFilter={true} columns={[
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
                ]} />}
                {tab === 'finals' && <DataTable title="👋 Final MLB Games" data={data.finalGames || []} defaultSortKey="date" enableDateFilter={true} columns={[
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
                ]} />}
                {tab === 'signature' && <DataTable title="💦 Signature HRs" data={data.signatureHRs || []} defaultSortKey="date" enableDateFilter={true} columns={[
                    { key: 'date', label: 'Date' }, { key: 'player', label: 'Player' }, { key: 'team', label: 'Team' },
                    { key: 'opponent', label: 'Opponent' }, { key: 'pitcher', label: 'Pitcher' }, { key: 'signatureNumber', label: 'Type' }, 
                    { key: 'gameId', label: 'Game', render: (v) => <GameLink gameId={v} /> }
                ]} />}
                {tab === 'nostats' && <DataTable title="👥 Players Without Stats" data={data.playersWithoutStats || []} columns={[
                    { key: 'name', label: 'Name', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> }, 
                    { key: 'teams', label: 'Teams' }, { key: 'games', label: 'G' }, { key: 'positions', label: 'Positions' }
                ]} />}
                {tab === 'comparison' && <PlayerComparison players={data.players || []} playerGames={data.playerGames || []} />}
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