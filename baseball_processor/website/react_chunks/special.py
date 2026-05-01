"""React app chunk: special."""

CODE = r'''const WpaLeadersView = ({ wpaLeaders }) => {
    const rows = wpaLeaders || [];
    const formatWpa = (value) => {
        const num = parseFloat(value || 0);
        if (isNaN(num)) return value || '';
        return `${num > 0 ? '+' : ''}${num.toFixed(3)}`;
    };
    const WpaValue = ({ value }) => {
        const num = parseFloat(value || 0);
        const cls = num > 0 ? 'text-green-600' : num < 0 ? 'text-red-600' : 'text-slate-500';
        return <span className={`font-mono font-semibold ${cls}`}>{formatWpa(value)}</span>;
    };

    const bestTotal = rows[0];
    const bestGame = rows.reduce((best, row) => parseFloat(row.bestGameWpa || 0) > parseFloat(best?.bestGameWpa || 0) ? row : best, null);
    const worstGame = rows.reduce((worst, row) => parseFloat(row.worstGameWpa || 0) < parseFloat(worst?.worstGameWpa || 0) ? row : worst, null);

    if (!rows.length) {
        return <EmptyState title="No WPA Data" message="No WPA leaders are available in the processed games." />;
    }

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard title="Players" value={rows.length.toLocaleString()} color="blue" />
                <StatCard title="Top Total" value={bestTotal ? formatWpa(bestTotal.totalWpa) : '0.000'} subtitle={bestTotal?.name || ''} color="green" />
                <StatCard title="Best Game" value={bestGame ? formatWpa(bestGame.bestGameWpa) : '0.000'} subtitle={bestGame?.name || ''} color="purple" />
                <StatCard title="Lowest Game" value={worstGame ? formatWpa(worstGame.worstGameWpa) : '0.000'} subtitle={worstGame?.name || ''} color="orange" />
            </div>
            <DataTable
                title="WPA Leaders"
                data={rows}
                defaultSortKey="totalWpa"
                persistKey="wpa-leaders"
                columns={[
                    { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                    { key: 'games', label: 'Games' },
                    { key: 'totalWpa', label: 'Total WPA', render: v => <WpaValue value={v} /> },
                    { key: 'avgWpa', label: 'Avg WPA', render: v => <WpaValue value={v} /> },
                    { key: 'positiveWpa', label: 'Positive WPA', render: v => <WpaValue value={v} /> },
                    { key: 'negativeWpa', label: 'Negative WPA', render: v => <WpaValue value={v} /> },
                    { key: 'bestGameWpa', label: 'Best Game', render: v => <WpaValue value={v} /> },
                    { key: 'bestGameId', label: 'Best Game ID', render: v => v ? <GameLink gameId={v} /> : '' },
                    { key: 'worstGameWpa', label: 'Worst Game', render: v => <WpaValue value={v} /> },
                    { key: 'worstGameId', label: 'Worst Game ID', render: v => v ? <GameLink gameId={v} /> : '' },
                ]}
            />
        </div>
    );
};

const DefenseLineupView = ({ data }) => {
    const defensiveRows = data.defensiveLeaders || [];
    const lineupRows = data.lineupAnalysis || [];
    const matrixRows = data.lineupMatrix || [];
    const firstPopulated = defensiveRows.length ? 'defense' : lineupRows.length ? 'lineup' : 'matrix';
    const [view, setView] = useState(firstPopulated);
    const totalRows = defensiveRows.length + lineupRows.length + matrixRows.length;
    const mostDefensiveGames = defensiveRows.reduce((best, row) => (row.games || 0) > (best?.games || 0) ? row : best, null);

    useEffect(() => {
        const activeHasRows = view === 'defense' ? defensiveRows.length : view === 'lineup' ? lineupRows.length : matrixRows.length;
        if (!activeHasRows && firstPopulated !== view) setView(firstPopulated);
    }, [firstPopulated, totalRows]);

    if (!totalRows) {
        return <EmptyState title="No Defense or Lineup Data" message="No defensive or lineup analysis rows are available." />;
    }

    const playerCol = { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> };
    const tabs = [
        { id: 'defense', label: 'Defense' },
        { id: 'lineup', label: 'Lineup' },
        { id: 'matrix', label: 'Matrix' },
    ];

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard title="Defensive Rows" value={defensiveRows.length.toLocaleString()} color="blue" />
                <StatCard title="Lineup Rows" value={lineupRows.length.toLocaleString()} color="green" />
                <StatCard title="Matrix Rows" value={matrixRows.length.toLocaleString()} color="purple" />
                <StatCard title="Most Games" value={mostDefensiveGames?.games || 0} subtitle={mostDefensiveGames?.name || ''} color="orange" />
            </div>
            <SubNav tabs={tabs} active={view} onChange={setView} />
            {view === 'defense' && (
                <DataTable
                    title="Defensive Leaders"
                    data={defensiveRows}
                    defaultSortKey="games"
                    persistKey="defensive-leaders"
                    columns={[
                        playerCol,
                        { key: 'games', label: 'Games' },
                        { key: 'putouts', label: 'PO' },
                        { key: 'assists', label: 'A' },
                        { key: 'errors', label: 'E' },
                        { key: 'totalChances', label: 'TC' },
                        { key: 'fieldingPct', label: 'Fielding %', render: v => <span className="font-mono">{v}</span> },
                        { key: 'positions', label: 'Positions' },
                    ]}
                />
            )}
            {view === 'lineup' && (
                <DataTable
                    title="Lineup Analysis"
                    data={lineupRows}
                    defaultSortKey="games"
                    persistKey="lineup-analysis"
                    columns={[
                        playerCol,
                        { key: 'games', label: 'Games' },
                        { key: 'mostCommonSpot', label: 'Common Spot' },
                        { key: 'timesInSpot', label: 'Times' },
                        { key: 'pinchHits', label: 'Pinch Hits' },
                    ]}
                />
            )}
            {view === 'matrix' && (
                <DataTable
                    title="Lineup Matrix"
                    data={matrixRows}
                    defaultSortKey="total"
                    persistKey="lineup-matrix"
                    columns={[
                        playerCol,
                        { key: 'total', label: 'Total' },
                        { key: 'spot1', label: '#1' },
                        { key: 'spot2', label: '#2' },
                        { key: 'spot3', label: '#3' },
                        { key: 'spot4', label: '#4' },
                        { key: 'spot5', label: '#5' },
                        { key: 'spot6', label: '#6' },
                        { key: 'spot7', label: '#7' },
                        { key: 'spot8', label: '#8' },
                        { key: 'spot9', label: '#9' },
                    ]}
                />
            )}
        </div>
    );
};

const SituationalHittingView = ({ data }) => {
    const tables = [
        {
            id: 'risp',
            label: 'RISP',
            title: 'RISP Performance',
            data: data.rispPerformance || [],
            defaultSortKey: 'avg',
            columns: [
                { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'ab', label: 'AB' },
                { key: 'h', label: 'H' },
                { key: 'avg', label: 'AVG', render: v => <span className="font-mono">{v}</span> },
                { key: 'hr', label: 'HR' },
            ],
        },
        {
            id: 'twoout',
            label: '2 Outs',
            title: '2-Out Performance',
            data: data.twoOutPerformance || [],
            defaultSortKey: 'avg',
            columns: [
                { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'ab', label: 'AB' },
                { key: 'h', label: 'H' },
                { key: 'avg', label: 'AVG', render: v => <span className="font-mono">{v}</span> },
                { key: 'hr', label: 'HR' },
            ],
        },
        {
            id: 'risp2out',
            label: 'RISP + 2',
            title: 'RISP + 2 Outs',
            data: data.rispTwoOutPerformance || [],
            defaultSortKey: 'avg',
            columns: [
                { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'ab', label: 'AB' },
                { key: 'h', label: 'H' },
                { key: 'avg', label: 'AVG', render: v => <span className="font-mono">{v}</span> },
                { key: 'hr', label: 'HR' },
            ],
        },
        {
            id: 'bases',
            label: 'Bases Loaded',
            title: 'Bases Loaded',
            data: data.basesLoaded || [],
            defaultSortKey: 'grandSlams',
            columns: [
                { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'grandSlams', label: 'Grand Slams' },
            ],
        },
        {
            id: 'late',
            label: 'Late & Close',
            title: 'Late & Close',
            data: data.lateClose || [],
            defaultSortKey: 'avg',
            columns: [
                { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'ab', label: 'AB' },
                { key: 'h', label: 'H' },
                { key: 'avg', label: 'AVG', render: v => <span className="font-mono">{v}</span> },
                { key: 'hr', label: 'HR' },
            ],
        },
    ];

    const firstPopulated = tables.find(t => t.data.length)?.id || 'risp';
    const [view, setView] = useState(firstPopulated);
    const totalRows = tables.reduce((sum, table) => sum + table.data.length, 0);
    const activeTable = tables.find(t => t.id === view) || tables[0];

    useEffect(() => {
        if (!tables.some(t => t.id === view && t.data.length) && firstPopulated !== view) {
            setView(firstPopulated);
        }
    }, [firstPopulated, totalRows]);

    if (!totalRows) {
        return <EmptyState title="No Situational Hitting" message="No situational hitting rows met the current table minimums." />;
    }

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {tables.map(table => (
                    <StatCard
                        key={table.id}
                        title={table.label}
                        value={table.data.length.toLocaleString()}
                        color={table.id === 'risp' ? 'blue' : table.id === 'twoout' ? 'green' : table.id === 'risp2out' ? 'purple' : table.id === 'bases' ? 'orange' : 'blue'}
                        onClick={() => setView(table.id)}
                    />
                ))}
            </div>
            <SubNav
                tabs={tables.map(table => ({ id: table.id, label: table.label }))}
                active={view}
                onChange={setView}
            />
            <DataTable
                title={activeTable.title}
                data={activeTable.data}
                defaultSortKey={activeTable.defaultSortKey}
                persistKey={`situational-${activeTable.id}`}
                columns={activeTable.columns}
            />
        </div>
    );
};

const HallOfFamersView = ({ hallOfFamers }) => {
    const rows = hallOfFamers || [];
    const totals = useMemo(() => {
        const hittingLines = rows.filter(r => (r.ab || 0) > 0).length;
        const pitchingLines = rows.filter(r => r.ip && r.ip !== '0.0').length;
        const topSeen = rows.reduce((best, row) => ((row.gamesSeen || 0) > (best?.gamesSeen || 0) ? row : best), null);
        const uniqueGames = new Set();
        rows.forEach(row => String(row.gameIds || '').split(',').map(g => g.trim()).filter(Boolean).forEach(g => uniqueGames.add(g)));
        return { hittingLines, pitchingLines, topSeen, uniqueGames: uniqueGames.size };
    }, [rows]);

    if (!rows.length) {
        return <EmptyState title="No Hall of Famers" message="No Hall of Fame players have been matched in the processed games." />;
    }

    const columns = [
        { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
        { key: 'yearInducted', label: 'Inducted' },
        { key: 'positions', label: 'Pos' },
        { key: 'teams', label: 'Teams' },
        { key: 'gamesSeen', label: 'Games' },
        { key: 'firstGame', label: 'First', render: v => v ? <GameLink gameId={v} /> : '' },
        { key: 'lastGame', label: 'Last', render: v => v ? <GameLink gameId={v} /> : '' },
        { key: 'span', label: 'Span' },
        { key: 'h', label: 'H' },
        { key: 'hr', label: 'HR' },
        { key: 'rbi', label: 'RBI' },
        { key: 'avg', label: 'AVG', render: v => v || '' },
        { key: 'ip', label: 'IP' },
        { key: 'wins', label: 'W' },
        { key: 'era', label: 'ERA', render: v => v || '' },
        { key: 'milestones', label: 'Milestones', render: v => v ? <span className="text-slate-700">{v}</span> : <span className="text-slate-300">None</span> },
    ];

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard title="Hall of Famers" value={rows.length.toLocaleString()} color="blue" />
                <StatCard title="Unique Games" value={totals.uniqueGames.toLocaleString()} color="green" />
                <StatCard title="Most Seen" value={totals.topSeen?.gamesSeen || 0} subtitle={totals.topSeen?.name || ''} color="purple" />
                <StatCard title="Lines" value={`${totals.hittingLines} H / ${totals.pitchingLines} P`} color="orange" />
            </div>
            <DataTable
                title="Hall of Famers Seen"
                data={rows}
                defaultSortKey="gamesSeen"
                persistKey="hall-of-famers"
                columns={columns}
            />
        </div>
    );
};

// Players tab: absorbs Leaderboards
const PlayersTabV2 = ({ data, initialSubtab, onSubtabChange }) => {
    const hasCollegeData = Object.keys(data.ncaaCrossRef || {}).length > 0;
    const hasSituationalData = [
        'rispPerformance',
        'twoOutPerformance',
        'rispTwoOutPerformance',
        'basesLoaded',
        'lateClose',
    ].some(key => (data[key] || []).length > 0);
    const hasDefenseData = [
        'defensiveLeaders',
        'lineupAnalysis',
        'lineupMatrix',
    ].some(key => (data[key] || []).length > 0);
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
        ...((data.hallOfFamers || []).length > 0 ? [{ id: 'hof', label: 'Hall of Fame' }] : []),
        ...(hasSituationalData ? [{ id: 'situational', label: 'Situational' }] : []),
        ...((data.wpaLeaders || []).length > 0 ? [{ id: 'wpa', label: 'WPA' }] : []),
        ...(hasDefenseData ? [{ id: 'defense', label: 'Defense' }] : []),
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
            {view === 'hof' && <HallOfFamersView hallOfFamers={data.hallOfFamers || []} />}
            {view === 'situational' && <SituationalHittingView data={data} />}
            {view === 'wpa' && <WpaLeadersView wpaLeaders={data.wpaLeaders || []} />}
            {view === 'defense' && <DefenseLineupView data={data} />}
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

const WeatherTimingView = ({ weatherTiming }) => {
    const rows = weatherTiming || [];
    const getValue = (statistic) => rows.find(r => r.statistic === statistic)?.value || 'N/A';
    const dayNight = `${getValue('Day Games')} / ${getValue('Night Games')}`;
    const weekendWeekday = `${getValue('Weekend Games')} / ${getValue('Weekday Games')}`;

    if (!rows.length) {
        return <EmptyState title="No Weather & Timing Data" message="No weather or timing summary data is available." />;
    }

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard title="Highest Wind" value={getValue('Highest Wind Speed')} color="blue" />
                <StatCard title="Average Wind" value={getValue('Average Wind Speed')} color="green" />
                <StatCard title="Day / Night" value={dayNight} color="purple" />
                <StatCard title="Weekend / Weekday" value={weekendWeekday} color="orange" />
            </div>
            <DataTable
                title="Weather & Timing"
                data={rows}
                defaultSortKey="category"
                persistKey="weather-timing"
                columns={[
                    { key: 'category', label: 'Category' },
                    { key: 'statistic', label: 'Statistic' },
                    { key: 'value', label: 'Value', render: v => <span className="font-mono">{v}</span> },
                ]}
            />
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
                ...((data.weatherTiming || []).length > 0 ? [{ id: 'weather', label: 'Weather' }] : []),
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
            {view === 'weather' && <WeatherTimingView weatherTiming={data.weatherTiming || []} />}
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
            {view === 'badges' && <BadgesDisplay games={data.games || []} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} careerFirstsByGame={data.careerFirstsByGame || {}} />}
            {view === 'matchups' && (data.matchupMatrix ? <MatchupMatrix matchupData={data.matchupMatrix} games={data.games || []} /> : <EmptyState icon="🎯" title="No Matchup Data" message="No matchup data available." />)}
        </div>
    );
};

'''
