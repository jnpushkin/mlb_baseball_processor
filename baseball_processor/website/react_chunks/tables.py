"""React app chunk: tables."""

CODE = r'''const GamesPerYearChart = ({ games }) => {
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

    const latestGame = recentGames[0] || null;
    const latestGameId = latestGame?.gameId;
    const openGame = (game) => {
        if (!game?.gameId) return;
        window._pendingGameId = game.gameId;
        if (onTabChange) onTabChange('gamelog');
    };

    const latestGameHighlights = useMemo(() => {
        if (!latestGameId) return [];
        const firsts = data.careerFirstsByGame?.[latestGameId] || [];
        const passings = data.allTimePassingsByGame?.[latestGameId] || [];
        const keyPlays = latestGame?.keyPlays || [];
        const items = [];
        if (firsts.length) {
            items.push({
                label: 'Career milestones',
                value: firsts.length,
                detail: firsts.slice(0, 2).map(f => `${getLastName(f.player_name)} ${shortenMilestone(f.milestone)}`).join(', ')
            });
        }
        if (passings.length) {
            items.push({
                label: 'All-time movement',
                value: passings.length,
                detail: passings.slice(0, 2).map(p => `${getLastName(p.player_name)} #${p.new_rank} ${p.stat_name}`).join(', ')
            });
        }
        if (keyPlays.length) {
            items.push({
                label: 'Key plays',
                value: keyPlays.length,
                detail: keyPlays.slice(0, 2).map(p => `${p.batter} ${p.type === 'grand_slam' ? 'grand slam' : 'HR'}`).join(', ')
            });
        }
        if (latestGame?.weather) {
            items.push({ label: 'Conditions', value: latestGame.temperature ? `${latestGame.temperature}°F` : 'Weather', detail: latestGame.weather });
        }
        return items.slice(0, 4);
    }, [latestGameId, latestGame, data.careerFirstsByGame, data.allTimePassingsByGame]);

    const recentMomentCards = useMemo(() => {
        const moments = [];
        (data.careerFirsts || []).forEach(m => moments.push({
            kind: 'Milestone',
            tone: 'amber',
            title: m.milestone,
            person: m.player_name,
            date: m.date_display || m.date,
            sortDate: m.date,
            gameId: m.game_id
        }));
        (data.allTimePassings || []).forEach(p => moments.push({
            kind: 'History',
            tone: 'purple',
            title: `#${p.new_rank} all-time in ${p.stat_name}`,
            person: p.player_name,
            date: p.date_display || p.date,
            sortDate: p.date,
            gameId: p.game_id
        }));
        (data.debuts || []).forEach(d => moments.push({
            kind: 'Debut',
            tone: 'green',
            title: `MLB debut${d.team ? ` with ${d.team}` : ''}`,
            person: d.player,
            date: d.date,
            sortDate: d.date,
            gameId: d.gameId
        }));
        return moments
            .filter(m => m.person || m.title)
            .sort((a, b) => toSortDate(b.sortDate).localeCompare(toSortDate(a.sortDate)))
            .slice(0, 6);
    }, [data.careerFirsts, data.allTimePassings, data.debuts]);

    const momentAccent = {
        amber: 'border-l-amber-400',
        purple: 'border-l-purple-400',
        green: 'border-l-emerald-400'
    };
    const momentPill = {
        amber: 'bg-amber-100 text-amber-700',
        purple: 'bg-purple-100 text-purple-700',
        green: 'bg-green-100 text-green-700'
    };

    return (
        <div className="space-y-6">
            {latestGame && (
                <section className="bg-white rounded-lg border border-slate-200 p-5" style={{ boxShadow: 'var(--shadow)' }}>
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
                        <div className="min-w-0">
                            <div className="small-text uppercase tracking-wide text-slate-500 font-semibold mb-1">Latest game</div>
                            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                                <h2 className="flex flex-wrap items-center gap-2 text-xl font-bold tracking-tight text-slate-900">
                                    <TeamToken code={latestGame.awayTeam} logoSize={26} />
                                    <span className="text-slate-400">@</span>
                                    <TeamToken code={latestGame.homeTeam} logoSize={26} />
                                </h2>
                                <span className="small-text font-semibold text-slate-500">Final</span>
                                <SourceBadge game={latestGame} compact />
                            </div>
                            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 body-text text-slate-500">
                                <span>{latestGame.date}</span>
                                <span>{latestGame.venue}</span>
                                {latestGame.startTime && <span>{latestGame.startTime}</span>}
                                {latestGame.gameType === 'spring' && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-semibold">Spring Training</span>}
                                {latestGame.gameType === 'postseason' && <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs font-semibold">Postseason</span>}
                            </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 lg:justify-end">
                            <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-2">
                                <div className="text-2xl font-bold font-mono text-slate-900">{latestGame.score}</div>
                            </div>
                            <button onClick={() => openGame(latestGame)} className="px-4 py-2 bg-blue-600 text-white rounded-lg body-text font-bold hover:bg-blue-700">
                                Open recap
                            </button>
                        </div>
                    </div>
                    {latestGameHighlights.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-2">
                            {latestGameHighlights.map((item, i) => (
                                <button key={`latest-highlight-${i}`} onClick={() => openGame(latestGame)} className="text-left rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 hover:bg-slate-100 min-w-[12rem]">
                                    <div className="small-text text-slate-500 font-semibold uppercase tracking-wide">{item.label}</div>
                                    <div className="mt-1 flex items-baseline gap-2">
                                        <span className="text-lg font-bold text-slate-900">{item.value}</span>
                                        <span className="small-text text-slate-500 truncate">{item.detail}</span>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </section>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Games" value={data.games?.length || 0} color="blue" onClick={() => onTabChange && onTabChange('gamelog')} />
                <StatCard title="Players" value={data.players?.length || 0} color="green" onClick={() => onTabChange && onTabChange('players')} />
                <StatCard title="Milestones" value={data.milestones?.length || 0} color="purple" onClick={() => onTabChange && onTabChange('milestones')} />
                <StatCard title="Teams" value={data.teams?.length || 0} color="orange" onClick={() => onTabChange && onTabChange('venues')} />
            </div>

            {recentMomentCards.length > 0 && (
                <section className="bg-white rounded-lg border border-slate-200 p-5" style={{ boxShadow: 'var(--shadow)' }}>
                    <div className="flex items-center justify-between gap-3 mb-4">
                        <div>
                            <h3 className="subsection-title font-bold text-slate-900">Recent Notable Moments</h3>
                            <p className="small-text text-slate-500 mt-1">Milestones, debuts, and all-time list movement from the latest games.</p>
                        </div>
                        <button onClick={() => onTabChange && onTabChange('milestones')} className="small-text text-blue-600 hover:text-blue-800 font-medium shrink-0">View all →</button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2.5">
                        {recentMomentCards.map((m, i) => (
                            <button
                                key={`recent-moment-${m.gameId || i}-${i}`}
                                onClick={() => {
                                    if (m.gameId) {
                                        window._pendingGameId = m.gameId;
                                        if (onTabChange) onTabChange('gamelog');
                                    }
                                }}
                                className={`text-left rounded-lg border border-slate-200 border-l-4 bg-slate-50 p-3 hover:bg-slate-100 hover:shadow-sm ${momentAccent[m.tone] || momentAccent.amber}`}
                            >
                                <div className="flex items-center justify-between gap-3">
                                    <span className={`small-text font-bold uppercase tracking-wide rounded px-2 py-0.5 ${momentPill[m.tone] || momentPill.amber}`}>{m.kind}</span>
                                    <span className="small-text text-slate-400 shrink-0">{m.date}</span>
                                </div>
                                <div className="body-text font-bold text-slate-900 mt-2">{m.person}</div>
                                <div className="small-text text-slate-500 mt-1">{m.title}</div>
                            </button>
                        ))}
                    </div>
                </section>
            )}

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
                                        <span className="ml-2 inline-flex items-center gap-1.5 small-text text-slate-500">
                                            <TeamLogo code={g.awayTeam} size={16} />
                                            <span>{g.awayTeam}</span>
                                            <span>@</span>
                                            <TeamLogo code={g.homeTeam} size={16} />
                                            <span>{g.homeTeam}</span>
                                        </span>
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
// The full-list popup is portaled to document.body with fixed positioning so
// it isn't clipped by ancestor `overflow-*` containers (e.g. the DataTable's
// scrolling wrapper). Hover handlers cover both the anchor and the popup so
// moving the cursor from one to the other never drops the hover state.
'''
