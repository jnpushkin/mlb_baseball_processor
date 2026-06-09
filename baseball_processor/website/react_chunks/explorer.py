"""React app chunk: chasers and custom stats explorer."""

CODE = r'''const ExplorePill = ({ active, children, onClick }) => (
    <button
        onClick={onClick}
        className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors border ${
            active ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
        }`}
    >
        {children}
    </button>
);

const ExploreStat = ({ label, value, sub }) => (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="text-2xl font-bold text-slate-900">{value}</div>
        <div className="text-xs font-semibold uppercase text-slate-500 mt-1">{label}</div>
        {sub && <div className="small-text text-slate-500 mt-2">{sub}</div>}
    </div>
);

const useGameLookups = (games) => useMemo(() => {
    const byId = {};
    const years = new Set();
    const venues = new Set();
    const gameTypes = new Set();
    (games || []).forEach(g => {
        byId[g.gameId] = g;
        const year = toSortableDate(g.date).slice(0, 4);
        if (year) years.add(year);
        if (g.venue) venues.add(g.venue);
        gameTypes.add(explorerGameType(g));
    });
    return {
        byId,
        years: Array.from(years).sort((a, b) => b.localeCompare(a)),
        venues: Array.from(venues).sort(),
        gameTypes: Array.from(gameTypes).sort(),
    };
}, [games]);

const explorerGameType = (game) => game?.gameType || game?.game_type || 'regular';

const explorerNumber = (value) => {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
};

const explorerLineValue = (game, side, key) => {
    const value = explorerNumber(game?.linescore?.[side]?.[key]);
    return value === null ? 0 : value;
};

const explorerRuns = (game, side) => {
    const lineRuns = explorerNumber(game?.linescore?.[side]?.runs);
    if (lineRuns !== null) return lineRuns;
    const scores = String(game?.score || '').match(/\d+/g);
    if (!scores || scores.length < 2) return null;
    return explorerNumber(side === 'away' ? scores[0] : scores[1]);
};

const gameMatchesExplorerFilters = (game, filters) => {
    if (!game) return false;
    const year = toSortableDate(game.date).slice(0, 4);
    if (filters.year !== 'all' && year !== filters.year) return false;
    if (filters.gameType !== 'all' && explorerGameType(game) !== filters.gameType) return false;
    if (filters.venue !== 'all' && game.venue !== filters.venue) return false;
    if (filters.team !== 'all' && game.awayTeam !== filters.team && game.homeTeam !== filters.team) return false;
    return true;
};

const playerGameMatchesExplorerFilters = (row, game, filters) => {
    if (!gameMatchesExplorerFilters(game, filters)) return false;
    if (filters.gameType !== 'all' && (row.gameType || explorerGameType(game)) !== filters.gameType) return false;
    if (filters.team !== 'all' && row.team !== filters.team) return false;
    if (filters.opponent !== 'all' && row.opponent !== filters.opponent) return false;
    return true;
};

const enrichHitterGameRow = (row, game) => ({
    ...row,
    year: toSortableDate(row.date).slice(0, 4),
    venue: game?.venue || '',
    score: game?.score || '',
    matchup: game ? `${game.awayTeam} @ ${game.homeTeam}` : '',
    totalBases: (row.h || 0) - (row.doubles || 0) - (row.triples || 0) - (row.hr || 0) + (row.doubles || 0) * 2 + (row.triples || 0) * 3 + (row.hr || 0) * 4,
});

const enrichPitcherGameRow = (row, game) => {
    const outs = row.outs || 0;
    const ip = `${Math.floor(outs / 3)}.${outs % 3}`;
    const decision = row.wins ? 'W' : row.losses ? 'L' : row.saves ? 'SV' : '';
    return {
        ...row,
        ip,
        decision,
        year: toSortableDate(row.date).slice(0, 4),
        venue: game?.venue || '',
        score: game?.score || '',
        matchup: game ? `${game.awayTeam} @ ${game.homeTeam}` : '',
    };
};

const aggregateTeamRows = (games, playerGames, pitcherGames, filters) => {
    const teams = {};
    const ensure = (team) => {
        if (!teams[team]) {
            teams[team] = { team, games: 0, wins: 0, losses: 0, runs: 0, runsAllowed: 0, h: 0, hr: 0, so: 0, venues: new Set(), lastGame: '' };
        }
        return teams[team];
    };
    const filteredGameIds = new Set();
    games.forEach(g => {
        if (!gameMatchesExplorerFilters(g, filters)) return;
        filteredGameIds.add(g.gameId);
        const awayRuns = explorerRuns(g, 'away');
        const homeRuns = explorerRuns(g, 'home');
        [['away', g.awayTeam, awayRuns, homeRuns], ['home', g.homeTeam, homeRuns, awayRuns]].forEach(([side, team, runs, allowed]) => {
            if (!team) return;
            if (filters.team !== 'all' && team !== filters.team) return;
            const row = ensure(team);
            row.games += 1;
            if (runs != null) row.runs += runs;
            if (allowed != null) row.runsAllowed += allowed;
            if (runs != null && allowed != null) {
                if (runs > allowed) row.wins += 1;
                if (runs < allowed) row.losses += 1;
            }
            if (g.venue) row.venues.add(g.venue);
            if (!row.lastGame || toSortableDate(g.date) > toSortableDate(row.lastGame)) row.lastGame = g.date;
        });
    });
    playerGames.forEach(pg => {
        if (!filteredGameIds.has(pg.gameId)) return;
        if (filters.team !== 'all' && pg.team !== filters.team) return;
        const row = ensure(pg.team);
        row.h += pg.h || 0;
        row.hr += pg.hr || 0;
    });
    pitcherGames.forEach(pg => {
        if (!filteredGameIds.has(pg.gameId)) return;
        if (filters.team !== 'all' && pg.team !== filters.team) return;
        const row = ensure(pg.team);
        row.so += pg.so || 0;
    });
    return Object.values(teams).map(row => ({
        ...row,
        winPct: row.games > 0 ? (row.wins / row.games).toFixed(3) : '0.000',
        rpg: row.games > 0 ? (row.runs / row.games).toFixed(2) : '0.00',
        rapg: row.games > 0 ? (row.runsAllowed / row.games).toFixed(2) : '0.00',
        venues: Array.from(row.venues).join(', '),
    }));
};

const CustomStatsExplorer = ({ data }) => {
    const games = data.games || [];
    const playerGames = data.playerGames || [];
    const pitcherGames = data.pitcherGames || [];
    const lookups = useGameLookups(games);
    const teams = useMemo(() => Array.from(new Set([
        ...games.flatMap(g => [g.awayTeam, g.homeTeam]),
        ...playerGames.map(r => r.team),
        ...pitcherGames.map(r => r.team),
    ].filter(Boolean))).sort(), [games, playerGames, pitcherGames]);
    const opponents = useMemo(() => Array.from(new Set([
        ...playerGames.map(r => r.opponent),
        ...pitcherGames.map(r => r.opponent),
    ].filter(Boolean))).sort(), [playerGames, pitcherGames]);

    const [dataset, setDataset] = useState('hitters');
    const [filters, setFilters] = useState({ year: 'all', team: 'all', opponent: 'all', venue: 'all', gameType: 'all' });
    const [minPa, setMinPa] = useState(1);
    const [minIp, setMinIp] = useState(0);

    const setFilter = (key, value) => setFilters(prev => ({ ...prev, [key]: value }));
    const clearFilters = () => {
        setFilters({ year: 'all', team: 'all', opponent: 'all', venue: 'all', gameType: 'all' });
        setMinPa(1);
        setMinIp(0);
    };

    const tableRows = useMemo(() => {
        const filteredPlayerGames = playerGames.filter(pg => playerGameMatchesExplorerFilters(pg, lookups.byId[pg.gameId], filters));
        const filteredPitcherGames = pitcherGames.filter(pg => playerGameMatchesExplorerFilters(pg, lookups.byId[pg.gameId], filters));

        if (dataset === 'hitters') {
            return aggregateHitterStats(filteredPlayerGames).filter(row => (row.pa || 0) >= minPa);
        }
        if (dataset === 'pitchers') {
            return aggregatePitcherStats(filteredPitcherGames).filter(row => ((row.outs || 0) / 3) >= minIp);
        }
        if (dataset === 'hitter-games') {
            return filteredPlayerGames.map(pg => enrichHitterGameRow(pg, lookups.byId[pg.gameId]));
        }
        if (dataset === 'pitcher-games') {
            return filteredPitcherGames.map(pg => enrichPitcherGameRow(pg, lookups.byId[pg.gameId]));
        }
        if (dataset === 'teams') {
            return aggregateTeamRows(games, playerGames, pitcherGames, filters);
        }
        return games
            .filter(g => gameMatchesExplorerFilters(g, filters))
            .map(g => {
                const awayRuns = explorerRuns(g, 'away');
                const homeRuns = explorerRuns(g, 'home');
                const awayHits = explorerLineValue(g, 'away', 'hits');
                const homeHits = explorerLineValue(g, 'home', 'hits');
                return {
                    ...g,
                    year: toSortableDate(g.date).slice(0, 4),
                    matchup: `${g.awayTeam} @ ${g.homeTeam}`,
                    gameType: explorerGameType(g),
                    combinedRuns: (awayRuns || 0) + (homeRuns || 0),
                    combinedHits: awayHits + homeHits,
                    margin: awayRuns === null || homeRuns === null ? '' : Math.abs(awayRuns - homeRuns),
                    winner: awayRuns === null || homeRuns === null ? '' : awayRuns > homeRuns ? g.awayTeam : homeRuns > awayRuns ? g.homeTeam : 'Tie',
                };
            });
    }, [dataset, filters, games, playerGames, pitcherGames, lookups, minPa, minIp]);

    const datasetDefs = {
        hitters: {
            title: 'Hitter Explorer',
            sort: 'ops',
            columns: [
                { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'pa', label: 'PA' }, { key: 'ab', label: 'AB' },
                { key: 'h', label: 'H' }, { key: 'avg', label: 'AVG' }, { key: 'obp', label: 'OBP' }, { key: 'slg', label: 'SLG' },
                { key: 'ops', label: 'OPS' }, { key: 'hr', label: 'HR' }, { key: 'rbi', label: 'RBI' }, { key: 'r', label: 'R' },
                { key: 'tb', label: 'TB' }, { key: 'xbh', label: 'XBH' }, { key: 'sb', label: 'SB' },
            ]
        },
        pitchers: {
            title: 'Pitcher Explorer',
            sort: 'so',
            columns: [
                { key: 'name', label: 'Pitcher', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'gameStarts', label: 'GS' }, { key: 'ip', label: 'IP' },
                { key: 'era', label: 'ERA' }, { key: 'whip', label: 'WHIP' }, { key: 'wins', label: 'W' }, { key: 'losses', label: 'L' },
                { key: 'saves', label: 'SV' }, { key: 'so', label: 'K' }, { key: 'bb', label: 'BB' }, { key: 'hr', label: 'HR' },
            ]
        },
        'hitter-games': {
            title: 'Single-Game Hitting Lines',
            sort: 'totalBases',
            columns: [
                { key: 'date', label: 'Date' }, { key: 'name', label: 'Player', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'team', label: 'Team' }, { key: 'opponent', label: 'Opp' }, { key: 'venue', label: 'Venue' },
                { key: 'ab', label: 'AB' }, { key: 'h', label: 'H' }, { key: 'r', label: 'R' }, { key: 'rbi', label: 'RBI' },
                { key: 'hr', label: 'HR' }, { key: 'doubles', label: '2B' }, { key: 'triples', label: '3B' }, { key: 'totalBases', label: 'TB' },
                { key: 'bb', label: 'BB' }, { key: 'so', label: 'SO' }, { key: 'sb', label: 'SB' },
                { key: 'gameId', label: 'Game', render: v => <button className="text-blue-600 hover:underline font-mono small-text" onClick={() => requestGameDetails(v)}>{v}</button> },
            ]
        },
        'pitcher-games': {
            title: 'Single-Game Pitching Lines',
            sort: 'so',
            columns: [
                { key: 'date', label: 'Date' }, { key: 'name', label: 'Pitcher', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'team', label: 'Team' }, { key: 'opponent', label: 'Opp' }, { key: 'venue', label: 'Venue' },
                { key: 'ip', label: 'IP' }, { key: 'h', label: 'H' }, { key: 'r', label: 'R' }, { key: 'er', label: 'ER' },
                { key: 'bb', label: 'BB' }, { key: 'so', label: 'K' }, { key: 'hr', label: 'HR' }, { key: 'decision', label: 'Dec' },
                { key: 'gameId', label: 'Game', render: v => <button className="text-blue-600 hover:underline font-mono small-text" onClick={() => requestGameDetails(v)}>{v}</button> },
            ]
        },
        teams: {
            title: 'Team Explorer',
            sort: 'games',
            columns: [
                { key: 'team', label: 'Team', render: v => <span className="inline-flex items-center gap-2"><TeamLogo code={v} size={18} />{v}</span> },
                { key: 'games', label: 'G' }, { key: 'wins', label: 'W' }, { key: 'losses', label: 'L' }, { key: 'winPct', label: 'Win %' },
                { key: 'runs', label: 'R' }, { key: 'runsAllowed', label: 'RA' }, { key: 'rpg', label: 'R/G' }, { key: 'rapg', label: 'RA/G' },
                { key: 'h', label: 'H' }, { key: 'hr', label: 'HR' }, { key: 'so', label: 'K' }, { key: 'lastGame', label: 'Last' },
            ]
        },
        games: {
            title: 'Game Explorer',
            sort: 'date',
            columns: [
                { key: 'date', label: 'Date' }, { key: 'matchup', label: 'Matchup' }, { key: 'score', label: 'Score' },
                { key: 'venue', label: 'Venue' }, { key: 'gameType', label: 'Type' }, { key: 'combinedRuns', label: 'Runs' },
                { key: 'combinedHits', label: 'Hits' }, { key: 'margin', label: 'Margin' }, { key: 'winner', label: 'Winner' },
                { key: 'gameId', label: 'Game', render: v => <button className="text-blue-600 hover:underline font-mono small-text" onClick={() => requestGameDetails(v)}>{v}</button> },
            ]
        },
    };

    const active = datasetDefs[dataset] || datasetDefs.hitters;
    const preset = (nextDataset, patch = {}) => {
        setDataset(nextDataset);
        setFilters(prev => ({ ...prev, ...patch }));
    };

    return (
        <div className="space-y-5">
            <div className="bg-white border border-slate-200 rounded-lg p-4">
                <div className="flex flex-wrap items-center gap-2 mb-4">
                    <ExplorePill active={dataset === 'hitters'} onClick={() => setDataset('hitters')}>Hitters</ExplorePill>
                    <ExplorePill active={dataset === 'pitchers'} onClick={() => setDataset('pitchers')}>Pitchers</ExplorePill>
                    <ExplorePill active={dataset === 'hitter-games'} onClick={() => setDataset('hitter-games')}>Hitting Games</ExplorePill>
                    <ExplorePill active={dataset === 'pitcher-games'} onClick={() => setDataset('pitcher-games')}>Pitching Games</ExplorePill>
                    <ExplorePill active={dataset === 'teams'} onClick={() => setDataset('teams')}>Teams</ExplorePill>
                    <ExplorePill active={dataset === 'games'} onClick={() => setDataset('games')}>Games</ExplorePill>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
                    <select value={filters.year} onChange={e => setFilter('year', e.target.value)} className="px-3 py-2 rounded border border-slate-200 body-text">
                        <option value="all">All years</option>
                        {lookups.years.map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                    <select value={filters.team} onChange={e => setFilter('team', e.target.value)} className="px-3 py-2 rounded border border-slate-200 body-text">
                        <option value="all">All teams</option>
                        {teams.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                    <select value={filters.opponent} onChange={e => setFilter('opponent', e.target.value)} className="px-3 py-2 rounded border border-slate-200 body-text">
                        <option value="all">All opponents</option>
                        {opponents.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                    <select value={filters.venue} onChange={e => setFilter('venue', e.target.value)} className="px-3 py-2 rounded border border-slate-200 body-text">
                        <option value="all">All venues</option>
                        {lookups.venues.map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                    <select value={filters.gameType} onChange={e => setFilter('gameType', e.target.value)} className="px-3 py-2 rounded border border-slate-200 body-text">
                        <option value="all">All game types</option>
                        {lookups.gameTypes.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                    <button onClick={clearFilters} className="px-3 py-2 rounded border border-slate-200 bg-slate-50 hover:bg-slate-100 body-text text-slate-600">Clear</button>
                </div>
                <div className="flex flex-wrap items-center gap-2 mt-4">
                    <span className="small-text text-slate-500 font-semibold mr-1">Presets</span>
                    <button onClick={() => preset('hitter-games')} className="px-2.5 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold">Best hitting games</button>
                    <button onClick={() => preset('pitcher-games')} className="px-2.5 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold">Best pitching games</button>
                    <button onClick={() => preset('hitters', { team: 'SF' })} className="px-2.5 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold">SF hitters</button>
                    <button onClick={() => preset('games', { venue: 'Oracle Park' })} className="px-2.5 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold">Oracle games</button>
                    <button onClick={() => preset('teams')} className="px-2.5 py-1 rounded bg-blue-50 text-blue-700 text-xs font-semibold">Team results</button>
                    {dataset === 'hitters' && (
                        <label className="ml-auto inline-flex items-center gap-2 small-text text-slate-500">Min PA
                            <input type="number" min="0" value={minPa} onChange={e => setMinPa(Number(e.target.value || 0))} className="w-20 px-2 py-1 rounded border border-slate-200" />
                        </label>
                    )}
                    {dataset === 'pitchers' && (
                        <label className="ml-auto inline-flex items-center gap-2 small-text text-slate-500">Min IP
                            <input type="number" min="0" value={minIp} onChange={e => setMinIp(Number(e.target.value || 0))} className="w-20 px-2 py-1 rounded border border-slate-200" />
                        </label>
                    )}
                </div>
            </div>
            <DataTable
                key={`explorer-${dataset}`}
                title={active.title}
                data={tableRows.map((row, idx) => ({ ...row, id: row.id || `${dataset}-${row.gameId || row.playerId || row.team || 'row'}-${idx}` }))}
                columns={active.columns}
                defaultSortKey={active.sort}
                persistKey={`custom-explorer-${dataset}`}
            />
        </div>
    );
};

const buildChaserCandidates = (data) => {
    const byId = {};
    const seenIds = new Set([
        ...(data.players || []).map(p => p.playerId),
        ...(data.pitchers || []).map(p => p.playerId),
        ...(data.playersWithoutStats || []).map(p => p.playerId),
    ].filter(Boolean));
    const majorAwardKeys = new Set(['mvp', 'cya', 'roy', 'reliever', 'postmvp', 'asmvp', 'hank_aaron', 'edgar_martinez', 'triple_crowns', 'batting-titles', 'pitching-era-titles']);
    const nonTeamCodes = new Set(['AL', 'NL', 'MLB', '2TM', '3TM', '4TM', 'SV', 'SP', 'RP', 'DH']);
    const teamCode = (value) => {
        const text = String(value || '').trim().toUpperCase();
        return /^[A-Z]{2,4}$/.test(text) && !nonTeamCodes.has(text) ? text : '';
    };
    const currentYear = Math.max(0, ...[
        ...(data.awardChecklists?.groups || []).flatMap(g => g.items || []).map(i => Number(i.year || 0)),
        ...(data.allStarChecklists?.groups || []).flatMap(g => g.items || []).map(i => Number(i.year || 0)),
    ]);

    const ensure = (item) => {
        const id = item.playerId || item.name;
        if (!id) return null;
        if (!byId[id]) {
            byId[id] = {
                id,
                playerId: item.playerId || '',
                name: item.name || 'Unknown',
                seen: seenIds.has(item.playerId) || Boolean(item.checked),
                score: 0,
                awardEntries: 0,
                majorAwards: 0,
                allStarSelections: 0,
                latestYear: 0,
                teams: new Set(),
                leagues: new Set(),
                reasons: new Set(),
                firstSeen: item.firstSeen || '',
                gamesSeen: item.gamesSeen || 0,
            };
        }
        const c = byId[id];
        if (item.checked) c.seen = true;
        if (item.gamesSeen) c.gamesSeen = Math.max(c.gamesSeen, item.gamesSeen);
        if (item.firstSeen && (!c.firstSeen || toSortableDate(item.firstSeen) < toSortableDate(c.firstSeen))) c.firstSeen = item.firstSeen;
        const cleanTeam = teamCode(item.team || item.teamCode);
        if (cleanTeam) c.teams.add(cleanTeam);
        if (item.league) c.leagues.add(item.league);
        if (item.year) c.latestYear = Math.max(c.latestYear, Number(item.year) || 0);
        return c;
    };

    (data.awardChecklists?.groups || []).forEach(group => {
        (group.items || []).forEach(item => {
            const c = ensure(item);
            if (!c) return;
            c.awardEntries += 1;
            const awardKey = item.awardKey || group.awardKey || '';
            const awardName = item.award || group.award || item.awardDetail || 'Award';
            const isMajor = majorAwardKeys.has(awardKey);
            if (isMajor) c.majorAwards += 1;
            c.score += isMajor ? 90 : 18;
            c.reasons.add(awardName);
        });
    });

    (data.allStarChecklists?.groups || []).forEach(group => {
        (group.items || []).forEach(item => {
            const c = ensure(item);
            if (!c) return;
            c.allStarSelections += 1;
            c.score += 22;
            c.reasons.add(item.gameLabel || 'All-Star');
        });
    });

    return Object.values(byId).map(c => {
        const recency = c.latestYear && currentYear ? Math.max(0, 12 - Math.min(12, currentYear - c.latestYear)) : 0;
        const reasons = Array.from(c.reasons).slice(0, 4);
        const isActiveWindowTarget = c.latestYear && currentYear ? c.latestYear >= currentYear - 1 : false;
        const activeScore = isActiveWindowTarget ? Math.round((c.score * 0.35) + (recency * 10) + (c.majorAwards ? 40 : 0) + (c.allStarSelections ? 15 : 0)) : 0;
        return {
            ...c,
            teams: Array.from(c.teams).sort().join(', '),
            leagues: Array.from(c.leagues).sort().join(', '),
            reasons: reasons.join(', '),
            isActiveWindowTarget,
            activeScore,
            score: Math.round(c.score + recency),
        };
    }).sort((a, b) => b.activeScore - a.activeScore || b.latestYear - a.latestYear || b.score - a.score || a.name.localeCompare(b.name));
};

const ChasersView = ({ data }) => {
    const [view, setView] = useState('active');
    const [status, setStatus] = useState('unseen');
    const candidates = useMemo(() => buildChaserCandidates(data), [data]);
    const unseen = candidates.filter(c => !c.seen);
    const seen = candidates.filter(c => c.seen);
    const activeWindow = candidates.filter(c => c.isActiveWindowTarget);
    const filtered = (status === 'seen' ? seen : status === 'all' ? candidates : unseen);

    const teamRows = useMemo(() => {
        const rows = {};
        candidates.forEach(c => {
            String(c.teams || '').split(',').map(t => t.trim()).filter(Boolean).forEach(team => {
                if (!rows[team]) rows[team] = { team, targets: 0, seen: 0, unseen: 0, score: 0, topTarget: '', topScore: 0 };
                const row = rows[team];
                row.targets += 1;
                row.score += c.score;
                if (c.seen) row.seen += 1;
                else row.unseen += 1;
                if (!c.seen && c.score > row.topScore) {
                    row.topScore = c.score;
                    row.topTarget = c.name;
                }
            });
        });
        return Object.values(rows).map(row => ({ ...row, completion: row.targets ? `${Math.round(row.seen / row.targets * 100)}%` : '0%' }))
            .sort((a, b) => b.unseen - a.unseen || b.score - a.score);
    }, [candidates]);

    const rows = view === 'teams' ? teamRows : filtered;
    const targetColumns = [
        { key: 'name', label: 'Target', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
        { key: 'displayScore', label: 'Score' },
        { key: 'majorAwards', label: 'Major' },
        { key: 'allStarSelections', label: 'ASG' },
        { key: 'awardEntries', label: 'Awards' },
        { key: 'latestYear', label: 'Latest' },
        { key: 'teams', label: 'Teams' },
        { key: 'reasons', label: 'Why' },
        { key: 'seen', label: 'Status', render: v => v ? <span className="text-green-700 font-semibold">Seen</span> : <span className="text-orange-700 font-semibold">Need</span> },
    ];
    const teamColumns = [
        { key: 'team', label: 'Team', render: v => <span className="inline-flex items-center gap-2"><TeamLogo code={v} size={18} />{v}</span> },
        { key: 'targets', label: 'Targets' },
        { key: 'seen', label: 'Seen' },
        { key: 'unseen', label: 'Need' },
        { key: 'completion', label: 'Complete' },
        { key: 'score', label: 'Target Score' },
        { key: 'topTarget', label: 'Top Need' },
    ];

    return (
        <div className="space-y-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <ExploreStat label="Reference targets" value={candidates.length} sub="Awards and All-Star players with BREF IDs" />
                <ExploreStat label="Active-window targets" value={activeWindow.length} sub="Award or All-Star records from the latest two seasons" />
                <ExploreStat label="Still unseen" value={unseen.length} sub="All unmatched reference targets" />
                <ExploreStat label="Already seen" value={seen.length} sub="Recognized players in your archive" />
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4 flex flex-wrap items-center gap-2">
                <ExplorePill active={view === 'active'} onClick={() => setView('active')}>Active Targets</ExplorePill>
                <ExplorePill active={view === 'awards'} onClick={() => setView('awards')}>Award Targets</ExplorePill>
                <ExplorePill active={view === 'allstars'} onClick={() => setView('allstars')}>All-Star Targets</ExplorePill>
                <ExplorePill active={view === 'teams'} onClick={() => setView('teams')}>By Team</ExplorePill>
                <ExplorePill active={view === 'historical'} onClick={() => setView('historical')}>Historical Targets</ExplorePill>
                {view !== 'teams' && (
                    <select value={status} onChange={e => setStatus(e.target.value)} className="ml-auto px-3 py-2 rounded border border-slate-200 body-text">
                        <option value="unseen">Unseen only</option>
                        <option value="seen">Seen only</option>
                        <option value="all">All targets</option>
                    </select>
                )}
            </div>
            <DataTable
                key={`chasers-${view}-${status}`}
                title={view === 'teams' ? 'Target Buckets by Team' : view === 'allstars' ? 'Active-Window All-Star Chasers' : view === 'awards' ? 'Active-Window Award Chasers' : view === 'active' ? 'Active Chaser Targets' : 'Historical Chaser Targets'}
                data={view === 'teams' ? rows : rows.filter(row => {
                    if (view === 'active') return row.isActiveWindowTarget;
                    if (view === 'awards') return row.awardEntries > 0 && row.isActiveWindowTarget;
                    if (view === 'allstars') return row.allStarSelections > 0 && row.isActiveWindowTarget;
                    return true;
                }).map(row => ({ ...row, displayScore: view === 'historical' ? row.score : row.activeScore }))}
                columns={view === 'teams' ? teamColumns : targetColumns}
                defaultSortKey={view === 'teams' ? 'unseen' : 'displayScore'}
                persistKey={`chasers-${view}`}
            />
        </div>
    );
};

const ExploreTab = ({ data, initialSubtab, onSubtabChange }) => {
    const [view, setView] = useState(initialSubtab || 'chasers');
    useEffect(() => { if (initialSubtab) setView(initialSubtab); }, [initialSubtab]);
    const switchView = (next) => {
        setView(next);
        if (onSubtabChange) onSubtabChange(next);
    };

    return (
        <div className="space-y-5">
            <div className="flex flex-wrap gap-2">
                <ExplorePill active={view === 'chasers'} onClick={() => switchView('chasers')}>Chasers</ExplorePill>
                <ExplorePill active={view === 'stats'} onClick={() => switchView('stats')}>Stats Explorer</ExplorePill>
            </div>
            {view === 'chasers' && <ChasersView data={data} />}
            {view === 'stats' && <CustomStatsExplorer data={data} />}
        </div>
    );
};
'''
