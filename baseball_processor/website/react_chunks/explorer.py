"""React app chunk: custom stats explorer."""

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

const useGameLookups = (games) => useMemo(() => {
    const byId = {};
    const years = new Set();
    const venues = new Set();
    const gameTypes = new Set();
    (games || []).forEach(g => {
        byId[g.gameId] = g;
        const year = toSortableDate(g.date).slice(0, 4);
        if (year) years.add(year);
        if (g.venue) venues.add(g._venueKey || g.venue);
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
    if (filters.venue !== 'all' && (game._venueKey || game.venue) !== filters.venue) return false;
    if (filters.opponent !== 'all' && game.awayTeam !== filters.opponent && game.homeTeam !== filters.opponent) return false;
    if (filters.team !== 'all' && filters.opponent === filters.team) return false;
    if (filters.team !== 'all' && game.awayTeam !== filters.team && game.homeTeam !== filters.team) return false;
    return true;
};

const playerGameMatchesExplorerFilters = (row, game, filters) => {
    if (!gameMatchesExplorerFilters(game, filters)) return false;
    if (filters.gameType !== 'all' && (row.gameType || explorerGameType(game)) !== filters.gameType) return false;
    if (filters.team !== 'all' && row.team !== filters.team) return false;
    if (filters.opponent !== 'all' && row.opponent !== filters.opponent) return false;
    if (filters.role === 'starter' && !row.gameStarts) return false;
    if (filters.role === 'reliever' && row.gameStarts) return false;
    const firstSeen = (game.firstSeenPlayerIds || []).includes(row.playerId);
    if (filters.visit === 'first' && !firstSeen) return false;
    if (filters.visit === 'return' && firstSeen) return false;
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
    const ip = formatOutsAsIP(outs);
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
            if (filters.opponent !== 'all' && (side === 'away' ? g.homeTeam : g.awayTeam) !== filters.opponent) return;
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
        if (filters.opponent !== 'all' && pg.opponent !== filters.opponent) return;
        const row = ensure(pg.team);
        row.h += pg.h || 0;
        row.hr += pg.hr || 0;
    });
    pitcherGames.forEach(pg => {
        if (!filteredGameIds.has(pg.gameId)) return;
        if (filters.team !== 'all' && pg.team !== filters.team) return;
        if (filters.opponent !== 'all' && pg.opponent !== filters.opponent) return;
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

    const route = usePassportRoute();
    const readQuery = (value, fallback) => { try { const parsed = JSON.parse(value || ''); return parsed && typeof parsed === 'object' && Array.isArray(parsed) === Array.isArray(fallback) ? parsed : fallback; } catch { return fallback; } };
    const dataset = ['hitters','pitchers','hitter-games','pitcher-games','teams','games'].includes(route.dataset) ? route.dataset : 'hitters';
    const defaults = {year:'all',team:'all',opponent:'all',venue:'all',gameType:'all',role:'all',visit:'all'};
    const queryFilters = readQuery(route.filters,{});
    const filters = Object.fromEntries(Object.entries(defaults).map(([key,value])=>[key,typeof queryFilters[key] === 'string' ? queryFilters[key] : value]));
    const conditions = readQuery(route.conditions,[]).filter(c=>c && typeof c === 'object' && typeof c.field === 'string' && ['gte','lte','eq'].includes(c.op) && ['string','number'].includes(typeof c.value));
    const minPa = Number(route.minPa || 1), minIp = Number(route.minIp || 0);
    const setDataset = next => navigatePassport({dataset:next,conditions:null,columns:null,filters:JSON.stringify({...filters,role:'all',visit:'all'})});
    const setFilters = update => navigatePassport({filters:JSON.stringify(typeof update==='function' ? update(filters) : update)});
    const setFilter = (key,value) => setFilters({...filters,[key]:value});
    const setMinPa = value => navigatePassport({minPa:String(value)});
    const setMinIp = value => navigatePassport({minIp:String(value)});
    const clearFilters = () => navigatePassport({filters:null,conditions:null,columns:null,minPa:null,minIp:null,match:null});
    const [queryName,setQueryName] = useState(''), [queryMessage,setQueryMessage] = useState('');
    const [savedQueries,saveQueries,queryError] = usePersonal('views',[]);
    const tableRows = useMemo(() => {
        const filteredPlayerGames = playerGames.filter(pg => playerGameMatchesExplorerFilters(pg, lookups.byId[pg.gameId], filters));
        const filteredPitcherGames = pitcherGames.filter(pg => playerGameMatchesExplorerFilters(pg, lookups.byId[pg.gameId], filters));

        if (dataset === 'hitters') {
            return aggregateHitterStats(filteredPlayerGames).filter(row => (row.pa || 0) >= minPa);
        }
        if (dataset === 'pitchers') {
            return aggregatePitcherStats(filteredPitcherGames).filter(row => (row.outs || 0) >= minIp * 3);
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
                    combinedHr: g._totals?.hr ?? null,
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
                {key:'iso',label:'ISO'},{key:'babip',label:'BABIP'},{key:'kPct',label:'K%'},{key:'bbPct',label:'BB%'},{key:'cs',label:'CS'},{key:'sbPct',label:'SB%'},{key:'sf',label:'SF'},{key:'sh',label:'SH'},
            ]
        },
        pitchers: {
            title: 'Pitcher Explorer',
            sort: 'so',
            columns: [
                { key: 'name', label: 'Pitcher', render: (v, r) => <PlayerLink playerId={r.playerId} name={v} /> },
                { key: 'team', label: 'Team' }, { key: 'games', label: 'G' }, { key: 'gameStarts', label: 'GS' }, { key: 'ip', label: 'IP', sortValue: (v, r) => r.outs || 0 },
                { key: 'era', label: 'ERA' }, { key: 'whip', label: 'WHIP' }, { key: 'wins', label: 'W' }, { key: 'losses', label: 'L' },
                { key: 'saves', label: 'SV' }, { key: 'so', label: 'K' }, { key: 'bb', label: 'BB' }, { key: 'hr', label: 'HR' },
                {key:'k9',label:'K/9'},{key:'bb9',label:'BB/9'},
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
                { key: 'ip', label: 'IP', sortValue: (v, r) => r.outs || 0 }, { key: 'h', label: 'H' }, { key: 'r', label: 'R' }, { key: 'er', label: 'ER' },
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
                { key: 'combinedHits', label: 'Hits' }, { key: 'combinedHr', label: 'HR' }, { key: 'margin', label: 'Margin' }, { key: 'winner', label: 'Winner' },
                { key: 'gameId', label: 'Game', render: v => <button className="text-blue-600 hover:underline font-mono small-text" onClick={() => requestGameDetails(v)}>{v}</button> },
            ]
        },
    };

    const active = datasetDefs[dataset] || datasetDefs.hitters;
    const preset = (nextDataset, patch = {}, rules=[]) => {
        navigatePassport({dataset:nextDataset,filters:JSON.stringify({...defaults,...patch}),conditions:JSON.stringify(rules),columns:null,match:'all'});
    };
    const numericColumns = active.columns.filter(c=>tableRows.some(r=>r[c.key]!==null && r[c.key]!=='' && Number.isFinite(Number(r[c.key]))) && !['date','gameId','playerId','ip'].includes(c.key));
    const validConditions = Array.isArray(conditions) ? conditions.filter(c=>numericColumns.some(f=>f.key===c.field) && Number.isFinite(Number(c.value)) && c.value!=='') : [];
    const matches = row => {
        const results = validConditions.map(c=>{
            if(row[c.field]==null || row[c.field]==='') return false;
            const a=Number(row[c.field]),b=Number(c.value);
            return c.op==='gte' ? a>=b : c.op==='lte' ? a<=b : a===b;
        });
        return !results.length || (route.match==='any' ? results.some(Boolean) : results.every(Boolean));
    };
    const selectedColumns = (route.columns || '').split(',').filter(Boolean);
    const requestedColumns = active.columns.filter(c=>selectedColumns.includes(c.key));
    const visibleColumns = requestedColumns.length ? requestedColumns : active.columns;
    const updateCondition = (index,patch) => navigatePassport({conditions:JSON.stringify(conditions.map((c,i)=>i===index ? {...c,...patch} : c))});
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
            <section className="passport-panel space-y-3">
                <h3 className="font-bold">Build a query</h3>
                <p className="text-sm text-slate-500">Filters and conditions are included in this page’s URL. Rate statistics use summed counts; K% and BB% use PA, SB% uses attempts, and K/9 and BB/9 use outs. A blank rate has no denominator.</p>
                <div className="flex gap-2 flex-wrap">
                    <button className="passport-button" onClick={()=>preset('pitcher-games',{role:'starter'},[{field:'so',op:'gte',value:'8'},{field:'bb',op:'eq',value:'0'}])}>8+ K, no walks</button>
                    <button className="passport-button" onClick={()=>preset('hitter-games',{},[{field:'h',op:'gte',value:'3'},{field:'sb',op:'gte',value:'1'}])}>3+ hits and a steal</button>
                    <button className="passport-button" onClick={()=>preset('games',{},[{field:'margin',op:'eq',value:'1'},{field:'combinedHr',op:'gte',value:'4'}])}>One-run games, 4+ HR</button>
                    <select aria-label="Condition matching" className="passport-input" value={route.match || 'all'} onChange={e=>navigatePassport({match:e.target.value})}><option value="all">Match all conditions</option><option value="any">Match any condition</option></select>
                    {['pitchers','pitcher-games'].includes(dataset) && <select aria-label="Pitching role" className="passport-input" value={filters.role} onChange={e=>setFilter('role',e.target.value)}><option value="all">All pitching roles</option><option value="starter">Starts</option><option value="reliever">Relief appearances</option></select>}
                    {!['teams','games'].includes(dataset) && <select aria-label="Visit history" className="passport-input" value={filters.visit} onChange={e=>setFilter('visit',e.target.value)}><option value="all">All appearances</option><option value="first">First time seen</option><option value="return">Return appearances</option></select>}
                </div>
                {(Array.isArray(conditions) ? conditions : []).map((c,i)=><div className="flex flex-wrap gap-2" key={i}>
                    <select aria-label={`Condition ${i+1} statistic`} className="passport-input" value={c.field} onChange={e=>updateCondition(i,{field:e.target.value})}>{numericColumns.map(f=><option key={f.key} value={f.key}>{f.label}</option>)}</select>
                    <select aria-label={`Condition ${i+1} operator`} className="passport-input" value={c.op} onChange={e=>updateCondition(i,{op:e.target.value})}><option value="gte">at least</option><option value="lte">at most</option><option value="eq">equals</option></select>
                    <input aria-label={`Condition ${i+1} value`} className="passport-input w-24" type="number" step="any" value={c.value} onChange={e=>updateCondition(i,{value:e.target.value})}/>
                    <button className="passport-button" onClick={()=>navigatePassport({conditions:JSON.stringify(conditions.filter((_,n)=>n!==i))})}>Remove condition {i+1}</button>
                </div>)}
                <button className="passport-button" disabled={!numericColumns.length} onClick={()=>navigatePassport({conditions:JSON.stringify([...conditions,{field:numericColumns[0].key,op:'gte',value:'1'}])})}>Add condition</button>
                <details><summary>Choose columns</summary><div className="flex flex-wrap gap-3 mt-2">{active.columns.map(c=><label key={c.key} className="text-sm"><input type="checkbox" checked={visibleColumns.includes(c)} onChange={e=>{const keys=visibleColumns.map(x=>x.key).filter(k=>k!==c.key);if(e.target.checked)keys.push(c.key);if(keys.length)navigatePassport({columns:keys.join(',')});}}/> {c.label}</label>)}</div></details>
                <div className="flex flex-wrap gap-2"><input aria-label="Query name" placeholder="Name this query" className="passport-input" value={queryName} onChange={e=>setQueryName(e.target.value)}/><button className="passport-button" disabled={!queryName.trim()} onClick={()=>{if(saveQueries([...savedQueries.filter(v=>v.name!==queryName.trim()),{name:queryName.trim(),route:{...route,game:null,player:null},tables:{}}]))setQueryMessage('Saved in Dashboard → Saved views and included in your private backup.');}}>Save query</button><button className="passport-button" onClick={async()=>{try{await navigator.clipboard.writeText(location.href);setQueryMessage('Query link copied.');}catch{setQueryMessage('Copy the address in your browser to share this query.');}}}>Copy query link</button></div>
                {(queryMessage || queryError) && <p role="status">{queryError || queryMessage}</p>}
            </section>
            <DataTable
                key={`explorer-${dataset}`}
                title={active.title}
                data={tableRows.filter(matches).map((row, idx) => ({ ...row, id: row.id || `${dataset}-${row.gameId || row.playerId || row.team || 'row'}-${idx}` }))}
                columns={visibleColumns}
                defaultSortKey={active.sort}
                persistKey={`custom-explorer-${dataset}`}
            />
        </div>
    );
};

'''
