"""React app chunk: home/away frivolities."""

CODE = r'''const HomeAwayFrivolities = ({ games, playerGames, pitcherGames }) => {
    const [lineMetric, setLineMetric] = useState('runs');
    const [gameTypeFilter, setGameTypeFilter] = useState('all');
    const [teamFilter, setTeamFilter] = useState('all');
    const [venueFilter, setVenueFilter] = useState('all');
    const [startYear, setStartYear] = useState('');
    const [endYear, setEndYear] = useState('');
    const [battingSort, setBattingSort] = useState({ key: 'pa', dir: 'desc' });
    const [repeatSort, setRepeatSort] = useState({ key: 'pa', dir: 'desc' });
    const [repeatSearch, setRepeatSearch] = useState('');
    const [showAllBatting, setShowAllBatting] = useState(false);
    const [showAllRepeat, setShowAllRepeat] = useState(false);
    const yearForGame = (game) => {
        const match = String(game?.date || '').match(/(\d{4})/);
        return match ? Number.parseInt(match[1], 10) : null;
    };
    const filterMeta = useMemo(() => {
        const teams = new Set();
        const venues = new Set();
        const years = new Set();
        (games || []).forEach(game => {
            if (game.awayTeam) teams.add(game.awayTeam);
            if (game.homeTeam) teams.add(game.homeTeam);
            if (game.venue) venues.add(game.venue);
            const year = yearForGame(game);
            if (year) years.add(year);
        });
        const sortedYears = [...years].sort((a, b) => a - b);
        return {
            teams: [...teams].sort(),
            venues: [...venues].sort(),
            minYear: sortedYears[0] || '',
            maxYear: sortedYears[sortedYears.length - 1] || '',
        };
    }, [games]);
    const filteredGames = useMemo(() => {
        const start = startYear ? Number.parseInt(startYear, 10) : null;
        const end = endYear ? Number.parseInt(endYear, 10) : null;
        return (games || []).filter(game => {
            if (!game || !game.gameId) return false;
            const gameType = game.gameType || 'regular';
            if (gameTypeFilter !== 'all' && gameType !== gameTypeFilter) return false;
            if (teamFilter !== 'all' && game.awayTeam !== teamFilter && game.homeTeam !== teamFilter) return false;
            if (venueFilter !== 'all' && game.venue !== venueFilter) return false;
            const year = yearForGame(game);
            if (start && (!year || year < start)) return false;
            if (end && (!year || year > end)) return false;
            return true;
        });
    }, [games, gameTypeFilter, teamFilter, venueFilter, startYear, endYear]);
    const data = useMemo(() => {
        const sideTemplate = (label) => ({
            label,
            games: 0,
            wins: 0,
            losses: 0,
            ties: 0,
            runs: 0,
            runsAllowed: 0,
            hits: 0,
            errors: 0,
            hr: 0,
            doubles: 0,
            triples: 0,
            bb: 0,
            so: 0,
            sb: 0,
            cs: 0,
            pitchingK: 0,
            pitchingBB: 0,
            pitchingHRAllowed: 0,
        });
        const sideStats = {
            away: sideTemplate('Away teams'),
            home: sideTemplate('Home teams'),
        };
        const inningRows = {};
        const paHalfInnings = {};
        const gameById = {};
        const normalize = (code) => ({
            SFN: 'SF', LAN: 'LAD', NYA: 'NYY', NYN: 'NYM', SDN: 'SD', SLN: 'STL',
            CHN: 'CHC', CHA: 'CWS', KCA: 'KC', TBA: 'TB', ANA: 'LAA', WAS: 'WSH',
            FLA: 'MIA', FLO: 'MIA',
        }[code] || code || '');
        const normalizePerson = (value) => String(value || '').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim();
        const num = (value) => {
            if (value === null || value === undefined || value === '' || String(value).toLowerCase() === 'x') return null;
            const parsed = Number.parseInt(value, 10);
            return Number.isFinite(parsed) ? parsed : null;
        };
        const isPlateAppearance = (play) => {
            const description = String(play.description || '').trim().toLowerCase();
            if (!description) return false;
            if (/^(wild pitch|passed ball|stolen base|caught stealing|pickoff|balk|defensive indifference|mound visit)/i.test(description)) {
                return false;
            }
            return /(single|double|triple|home run|homer|walk|hit by pitch|strikeout|strikes out|called out on strikes|ground|line|fly|flies|pop|pops|force out|fielder's choice|reaches on|sacrifice|catcher interference|interference|double play|triple play)/i.test(description);
        };
        const getRuns = (game, side) => {
            const lineRuns = num(game.linescore?.[side]?.runs);
            if (lineRuns !== null) return lineRuns;
            const scores = String(game.score || '').match(/\d+/g);
            if (!scores || scores.length < 2) return null;
            return num(side === 'away' ? scores[0] : scores[1]);
        };
        const sideForTeam = (game, team) => {
            const normalized = normalize(team);
            if (normalized && normalized === normalize(game.awayTeam)) return 'away';
            if (normalized && normalized === normalize(game.homeTeam)) return 'home';
            return null;
        };
        const addHalf = (side, inningIndex, runs, game) => {
            if (runs === null) return;
            const inning = inningIndex + 1;
            const half = side === 'away' ? 'Top' : 'Bot';
            const key = `${half} ${inning}`;
            if (!inningRows[key]) {
                inningRows[key] = {
                    key,
                    inning,
                    half,
                    side,
                    opportunities: 0,
                    runs: 0,
                    scoringHalves: 0,
                    maxRuns: 0,
                    maxGame: null,
                };
            }
            const row = inningRows[key];
            row.opportunities += 1;
            row.runs += runs;
            if (runs > 0) row.scoringHalves += 1;
            if (runs > row.maxRuns) {
                row.maxRuns = runs;
                row.maxGame = {
                    gameId: game.gameId,
                    date: game.date,
                    matchup: `${game.awayTeam} @ ${game.homeTeam}`,
                    score: game.score,
                };
            }
        };

        (filteredGames || []).forEach(game => {
            if (!game || !game.gameId) return;
            gameById[game.gameId] = game;
            const awayRuns = getRuns(game, 'away');
            const homeRuns = getRuns(game, 'home');
            const away = sideStats.away;
            const home = sideStats.home;

            away.games += 1;
            home.games += 1;
            away.runs += awayRuns || 0;
            home.runs += homeRuns || 0;
            away.runsAllowed += homeRuns || 0;
            home.runsAllowed += awayRuns || 0;
            away.hits += num(game.linescore?.away?.hits) || 0;
            home.hits += num(game.linescore?.home?.hits) || 0;
            away.errors += num(game.linescore?.away?.errors) || 0;
            home.errors += num(game.linescore?.home?.errors) || 0;

            if (awayRuns !== null && homeRuns !== null) {
                if (awayRuns > homeRuns) { away.wins += 1; home.losses += 1; }
                else if (homeRuns > awayRuns) { home.wins += 1; away.losses += 1; }
                else { away.ties += 1; home.ties += 1; }
            }

            (game.linescore?.away?.innings || []).forEach((value, idx) => addHalf('away', idx, num(value), game));
            (game.linescore?.home?.innings || []).forEach((value, idx) => addHalf('home', idx, num(value), game));

            (game.playByPlay || []).forEach((play, playIndex) => {
                const inning = Number.parseInt(play.inning, 10);
                const half = String(play.half || '').toLowerCase();
                const batterName = normalizePerson(play.batter);
                const batterKey = play.batterId || batterName.toLowerCase();
                if (!inning || !half || !batterName || !batterKey) return;
                if (!isPlateAppearance(play)) return;
                const side = half === 'top' ? 'away' : half === 'bottom' ? 'home' : null;
                if (!side) return;
                const key = `${game.gameId}-${half}-${inning}`;
                if (!paHalfInnings[key]) {
                    const lineRow = inningRows[`${side === 'away' ? 'Top' : 'Bot'} ${inning}`];
                    const inningRuns = num(game.linescore?.[side]?.innings?.[inning - 1]);
                    paHalfInnings[key] = {
                        key,
                        gameId: game.gameId,
                        date: game.date,
                        matchup: `${game.awayTeam} @ ${game.homeTeam}`,
                        score: game.score,
                        inning,
                        half,
                        side,
                        battingTeam: play.battingTeam || (side === 'away' ? game.awayTeam : game.homeTeam),
                        runs: inningRuns !== null ? inningRuns : (lineRow?.maxGame?.gameId === game.gameId ? lineRow.maxRuns : null),
                        plateAppearances: 0,
                        batters: {},
                    };
                }
                const group = paHalfInnings[key];
                group.plateAppearances += 1;
                if (!group.batters[batterKey]) {
                    group.batters[batterKey] = {
                        playerId: play.batterId || '',
                        name: batterName,
                        appearances: 0,
                        results: [],
                        playIndexes: [],
                    };
                }
                const batter = group.batters[batterKey];
                batter.appearances += 1;
                batter.results.push(play.description || '');
                batter.playIndexes.push(playIndex);
            });
        });

        (playerGames || []).forEach(row => {
            const game = gameById[row.gameId];
            const side = game ? sideForTeam(game, row.team) : null;
            if (!side) return;
            const stats = sideStats[side];
            stats.hr += row.hr || 0;
            stats.doubles += row.doubles || 0;
            stats.triples += row.triples || 0;
            stats.bb += row.bb || 0;
            stats.so += row.so || 0;
            stats.sb += row.sb || 0;
            stats.cs += row.cs || 0;
        });

        (pitcherGames || []).forEach(row => {
            const game = gameById[row.gameId];
            const side = game ? sideForTeam(game, row.team) : null;
            if (!side) return;
            const stats = sideStats[side];
            stats.pitchingK += row.so || 0;
            stats.pitchingBB += row.bb || 0;
            stats.pitchingHRAllowed += row.hr || 0;
        });

        const halfRows = Object.values(inningRows).sort((a, b) => a.inning - b.inning || (a.side === 'away' ? -1 : 1));
        const maxInning = Math.max(9, ...halfRows.map(row => row.inning));
        const lineInnings = Array.from({ length: maxInning }, (_, idx) => idx + 1);
        const lineRows = [
            { side: 'away', label: 'Top', teamLabel: 'Away' },
            { side: 'home', label: 'Bot', teamLabel: 'Home' },
        ].map(row => ({
            ...row,
            innings: lineInnings.map(inning => halfRows.find(item => item.side === row.side && item.inning === inning) || null),
        }));
        const biggestHalves = [...halfRows]
            .filter(row => row.maxRuns > 0)
            .sort((a, b) => b.maxRuns - a.maxRuns || a.inning - b.inning)
            .slice(0, 8);
        const longHalfInnings = Object.values(paHalfInnings)
            .map(group => ({
                ...group,
                repeatBatters: Object.values(group.batters)
                    .filter(batter => batter.appearances > 1)
                    .sort((a, b) => b.appearances - a.appearances || a.name.localeCompare(b.name)),
            }))
            .filter(group => group.plateAppearances >= 9 && group.repeatBatters.length > 0)
            .sort((a, b) => b.plateAppearances - a.plateAppearances || (b.runs || 0) - (a.runs || 0) || toSortableDate(b.date).localeCompare(toSortableDate(a.date)));
        const repeatBatterEvents = longHalfInnings
            .flatMap(group => group.repeatBatters.map(batter => ({
                ...batter,
                group,
            })))
            .sort((a, b) => b.appearances - a.appearances || b.group.plateAppearances - a.group.plateAppearances || toSortableDate(b.group.date).localeCompare(toSortableDate(a.group.date)));
        return { sideStats, halfRows, lineInnings, lineRows, biggestHalves, longHalfInnings, repeatBatterEvents };
    }, [filteredGames, playerGames, pitcherGames]);

    const fmtAvg = (value, denom, places = 2) => denom ? (value / denom).toFixed(places) : '-';
    const fmtPct = (value, denom) => denom ? `${Math.round((value / denom) * 100)}%` : '-';
    const record = (s) => `${s.wins}-${s.losses}${s.ties ? `-${s.ties}` : ''}`;
    const runDiff = (s) => s.runs - s.runsAllowed;
    const lineMetricOptions = {
        runs: {
            label: 'Runs',
            totalLabel: 'R',
            value: (row) => row ? row.runs : '-',
            total: (rows) => rows.reduce((sum, row) => sum + (row?.runs || 0), 0),
        },
        avg: {
            label: 'Avg',
            totalLabel: 'AVG',
            value: (row) => row ? fmtAvg(row.runs, row.opportunities) : '-',
            total: (rows) => {
                const runs = rows.reduce((sum, row) => sum + (row?.runs || 0), 0);
                const opportunities = rows.reduce((sum, row) => sum + (row?.opportunities || 0), 0);
                return fmtAvg(runs, opportunities);
            },
        },
        scored: {
            label: 'Scored %',
            totalLabel: 'SCR',
            value: (row) => row ? fmtPct(row.scoringHalves, row.opportunities) : '-',
            total: (rows) => {
                const scored = rows.reduce((sum, row) => sum + (row?.scoringHalves || 0), 0);
                const opportunities = rows.reduce((sum, row) => sum + (row?.opportunities || 0), 0);
                return fmtPct(scored, opportunities);
            },
        },
        high: {
            label: 'High',
            totalLabel: 'HI',
            value: (row) => row ? row.maxRuns : '-',
            total: (rows) => rows.reduce((high, row) => Math.max(high, row?.maxRuns || 0), 0),
        },
    };
    const activeLineMetric = lineMetricOptions[lineMetric] || lineMetricOptions.runs;
    const halfLabel = (group) => `${group.half === 'top' ? 'Top' : 'Bot'} ${group.inning}`;
    const summarizeResult = (description, playerName) => {
        const playerPattern = playerName ? new RegExp(String(playerName).replace(/\u00a0/g, ' ').replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i') : null;
        let text = String(description || '').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim();
        if (playerPattern) text = text.replace(playerPattern, '').trim();
        if (!text) return 'PA';
        const lowered = text.toLowerCase().replace(/^[.:;,\-\s]+/, '');
        if (/^(home run|hr\b|homers?\b)/.test(lowered)) return 'HR';
        if (/^(triple|triples?\b|3b\b)/.test(lowered)) return '3B';
        if (/^(double|doubles?\b|2b\b)/.test(lowered)) return '2B';
        if (/^(single|singles?\b|1b\b)/.test(lowered)) return '1B';
        if (/^(intentional walk|walks?\b|bb\b|ibb\b)/.test(lowered)) return 'BB';
        if (/^(hit by pitch|hbp\b)/.test(lowered)) return 'HBP';
        if (/^(strikeout|strikes out|called out on strikes|strikeout swinging|strikeout looking|k\b)/.test(lowered)) return 'K';
        if (/^(out on a sacrifice fly|sacrifice fly|sac fly)|\bsacrifice fly\b/.test(lowered)) return 'SF';
        if (/^(sacrifice bunt|sac bunt)|\bsacrifice bunt\b/.test(lowered)) return 'SH';
        if (/^(grounded into double play|grounds into a double play|double play)/.test(lowered)) return 'GIDP';
        if (/^(fielder's choice|fielders choice)/.test(lowered)) return 'FC';
        if (/^(reaches on|field error|error)/.test(lowered)) return 'ROE';
        if (/^(lineout|line out|lines out|line-drive out)/.test(lowered)) return 'LO';
        if (/^(flyout|fly out|flies out|flyball|fly ball)/.test(lowered)) return 'FO';
        if (/^(popout|pop out|pops out|popfly|pop fly|foul popfly)/.test(lowered)) return 'PO';
        if (/^(groundout|ground out|grounds out)/.test(lowered)) return 'GO';
        if (/^(forceout|force out)/.test(lowered)) return 'Force';
        return 'PA';
    };
    const openGame = (gameId, focus) => {
        if (!gameId) return;
        requestGameDetails(gameId, focus ? { focus: { ...focus, gameId }, tab: 'playbyplay' } : {});
    };
    const focusForGroup = (group) => ({ inning: group.inning, half: group.half });
    const focusForHalfRow = (row) => ({
        inning: row.inning,
        half: row.side === 'away' ? 'top' : 'bottom',
    });
    const sortValue = (item, key, kind) => {
        const group = kind === 'repeat' ? item.group : item;
        if (key === 'date') return toSortableDate(group.date || '');
        if (key === 'game') return group.matchup || '';
        if (key === 'team') return group.battingTeam || '';
        if (key === 'inning') return (group.inning || 0) + (group.half === 'bottom' ? 0.5 : 0);
        if (key === 'pa') return kind === 'repeat' ? item.appearances : group.plateAppearances;
        if (key === 'runs') return group.runs ?? -1;
        if (key === 'repeat') return group.repeatBatters?.length || 0;
        if (key === 'player') return item.name || '';
        return '';
    };
    const compareBySort = (a, b, sort, kind) => {
        const av = sortValue(a, sort.key, kind);
        const bv = sortValue(b, sort.key, kind);
        const base = typeof av === 'number' && typeof bv === 'number'
            ? av - bv
            : String(av).localeCompare(String(bv));
        return sort.dir === 'asc' ? base : -base;
    };
    const toggleSort = (current, setSort, key) => {
        setSort(current.key === key
            ? { key, dir: current.dir === 'asc' ? 'desc' : 'asc' }
            : { key, dir: ['player', 'game', 'team', 'inning', 'date'].includes(key) ? 'asc' : 'desc' });
    };
    const SortHeader = ({ label, sortKey, sort, setSort, align = 'left' }) => (
        <button
            onClick={() => toggleSort(sort, setSort, sortKey)}
            className={`w-full flex items-center gap-1 ${align === 'right' ? 'justify-end text-right' : 'justify-start text-left'} font-semibold text-slate-600 hover:text-blue-700`}
        >
            <span>{label}</span>
            {sort.key === sortKey && <span className="text-blue-600">{sort.dir === 'asc' ? '↑' : '↓'}</span>}
        </button>
    );
    const repeatQuery = repeatSearch.trim().toLowerCase();
    const filteredRepeatEvents = data.repeatBatterEvents.filter(event => {
        if (!repeatQuery) return true;
        const haystack = [
            event.name,
            event.group?.battingTeam,
            event.group?.matchup,
            event.group?.date,
            event.group?.score,
            ...(event.results || []).map(result => summarizeResult(result, event.name)),
        ].join(' ').toLowerCase();
        return haystack.includes(repeatQuery);
    });
    const sortedBattingAround = [...data.longHalfInnings].sort((a, b) => compareBySort(a, b, battingSort, 'batting'));
    const sortedRepeatEvents = [...filteredRepeatEvents].sort((a, b) => compareBySort(a, b, repeatSort, 'repeat'));
    const visibleBattingAround = showAllBatting ? sortedBattingAround : sortedBattingAround.slice(0, 12);
    const visibleRepeatEvents = showAllRepeat ? sortedRepeatEvents : sortedRepeatEvents.slice(0, 30);
    const activeFilters = gameTypeFilter !== 'all' || teamFilter !== 'all' || venueFilter !== 'all' || startYear || endYear;
    const clearFilters = () => {
        setGameTypeFilter('all');
        setTeamFilter('all');
        setVenueFilter('all');
        setStartYear('');
        setEndYear('');
        setRepeatSearch('');
    };

    const StatBlock = ({ label, value, tone = 'blue' }) => {
        const tones = {
            blue: 'bg-blue-50 border-blue-200 text-blue-800',
            green: 'bg-emerald-50 border-emerald-200 text-emerald-800',
            amber: 'bg-amber-50 border-amber-200 text-amber-800',
            slate: 'bg-slate-50 border-slate-200 text-slate-800',
        };
        return (
            <div className={`rounded-lg border p-4 ${tones[tone] || tones.slate}`}>
                <div className="text-xs font-semibold uppercase text-slate-500">{label}</div>
                <div className="text-2xl font-bold mt-1">{value}</div>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <section className="bg-white rounded-lg border border-slate-200 p-4" style={{ boxShadow: 'var(--shadow)' }}>
                <div className="flex flex-col lg:flex-row lg:items-end gap-3">
                    <div className="min-w-0 flex-1">
                        <h2 className="section-title font-bold">Home/Away Filters</h2>
                        <p className="body-text text-slate-500 mt-1">
                            {filteredGames.length} of {(games || []).length} games included in these splits.
                        </p>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 w-full lg:w-auto">
                        <label className="text-xs font-semibold text-slate-500">
                            Type
                            <select value={gameTypeFilter} onChange={(e) => setGameTypeFilter(e.target.value)} className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-2 text-sm text-slate-800">
                                <option value="all">All types</option>
                                <option value="regular">Regular</option>
                                <option value="postseason">Postseason</option>
                                <option value="spring">Spring</option>
                            </select>
                        </label>
                        <label className="text-xs font-semibold text-slate-500">
                            Team
                            <select value={teamFilter} onChange={(e) => setTeamFilter(e.target.value)} className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-2 text-sm text-slate-800">
                                <option value="all">All teams</option>
                                {filterMeta.teams.map(team => <option key={team} value={team}>{team}</option>)}
                            </select>
                        </label>
                        <label className="text-xs font-semibold text-slate-500 md:col-span-2">
                            Venue
                            <select value={venueFilter} onChange={(e) => setVenueFilter(e.target.value)} className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-2 text-sm text-slate-800">
                                <option value="all">All venues</option>
                                {filterMeta.venues.map(venue => <option key={venue} value={venue}>{venue}</option>)}
                            </select>
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            <label className="text-xs font-semibold text-slate-500">
                                From
                                <input type="number" inputMode="numeric" min={filterMeta.minYear || undefined} max={filterMeta.maxYear || undefined} placeholder={filterMeta.minYear || 'Year'} value={startYear} onChange={(e) => setStartYear(e.target.value)} className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-2 text-sm text-slate-800" />
                            </label>
                            <label className="text-xs font-semibold text-slate-500">
                                To
                                <input type="number" inputMode="numeric" min={filterMeta.minYear || undefined} max={filterMeta.maxYear || undefined} placeholder={filterMeta.maxYear || 'Year'} value={endYear} onChange={(e) => setEndYear(e.target.value)} className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-2 text-sm text-slate-800" />
                            </label>
                        </div>
                    </div>
                    {activeFilters && (
                        <button onClick={clearFilters} className="self-start lg:self-end rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50">
                            Clear
                        </button>
                    )}
                </div>
            </section>

            <section className="bg-white rounded-lg border border-slate-200 p-5" style={{ boxShadow: 'var(--shadow)' }}>
                <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2 mb-4">
                    <div>
                        <h2 className="section-title font-bold">Away/Home Split</h2>
                        <p className="body-text text-slate-500 mt-1">Combined totals for every away team vs every home team in your games.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
                    <StatBlock label="Away record" value={record(data.sideStats.away)} tone="blue" />
                    <StatBlock label="Home record" value={record(data.sideStats.home)} tone="green" />
                    <StatBlock label="Away runs" value={`${data.sideStats.away.runs} (${fmtAvg(data.sideStats.away.runs, data.sideStats.away.games, 1)}/G)`} tone="amber" />
                    <StatBlock label="Home runs" value={`${data.sideStats.home.runs} (${fmtAvg(data.sideStats.home.runs, data.sideStats.home.games, 1)}/G)`} tone="slate" />
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-slate-50">
                            <tr>
                                <th className="px-3 py-2 text-left">Side</th>
                                <th className="px-3 py-2 text-right">W-L</th>
                                <th className="px-3 py-2 text-right">Win %</th>
                                <th className="px-3 py-2 text-right">Runs</th>
                                <th className="px-3 py-2 text-right">Diff</th>
                                <th className="px-3 py-2 text-right">Hits</th>
                                <th className="px-3 py-2 text-right">HR</th>
                                <th className="px-3 py-2 text-right">BB</th>
                                <th className="px-3 py-2 text-right">Bat K</th>
                                <th className="px-3 py-2 text-right">SB</th>
                                <th className="px-3 py-2 text-right">Pitch K</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {['away', 'home'].map(side => {
                                const s = data.sideStats[side];
                                const pct = s.wins + s.losses > 0 ? (s.wins / (s.wins + s.losses)).toFixed(3).replace(/^0/, '') : '-';
                                const diff = runDiff(s);
                                return (
                                    <tr key={side}>
                                        <td className="px-3 py-3 font-semibold">{s.label}</td>
                                        <td className="px-3 py-3 text-right font-mono">{record(s)}</td>
                                        <td className="px-3 py-3 text-right font-mono">{pct}</td>
                                        <td className="px-3 py-3 text-right font-mono">{s.runs}</td>
                                        <td className={`px-3 py-3 text-right font-mono ${diff >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{diff > 0 ? '+' : ''}{diff}</td>
                                        <td className="px-3 py-3 text-right font-mono">{s.hits}</td>
                                        <td className="px-3 py-3 text-right font-mono">{s.hr}</td>
                                        <td className="px-3 py-3 text-right font-mono">{s.bb}</td>
                                        <td className="px-3 py-3 text-right font-mono">{s.so}</td>
                                        <td className="px-3 py-3 text-right font-mono">{s.sb}</td>
                                        <td className="px-3 py-3 text-right font-mono">{s.pitchingK}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </section>

            <section className="bg-white rounded-lg border border-slate-200 p-5" style={{ boxShadow: 'var(--shadow)' }}>
                <div className="flex flex-col lg:flex-row gap-6">
                    <div className="min-w-0 flex-1">
                        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
                            <div>
                                <h2 className="section-title font-bold">Runs By Half Inning</h2>
                                <p className="body-text text-slate-500 mt-1">A personal linescore for every half-inning you've seen.</p>
                            </div>
                            <div className="inline-flex rounded-lg bg-slate-100 p-1 self-start sm:self-auto">
                                {Object.entries(lineMetricOptions).map(([key, option]) => (
                                    <button
                                        key={key}
                                        onClick={() => setLineMetric(key)}
                                        className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                                            lineMetric === key
                                                ? 'bg-white text-slate-900 shadow-sm'
                                                : 'text-slate-500 hover:text-slate-800'
                                        }`}>
                                        {option.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm" style={{ minWidth: data.lineInnings.length > 10 ? '760px' : '640px' }}>
                                <thead className="bg-slate-50">
                                    <tr>
                                        <th className="px-3 py-2 text-left sticky left-0 bg-slate-50 z-10">Half</th>
                                        {data.lineInnings.map(inning => (
                                            <th key={inning} className="px-3 py-2 text-center">{inning}</th>
                                        ))}
                                        <th className="px-3 py-2 text-center border-l border-slate-200">{activeLineMetric.totalLabel}</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {data.lineRows.map(row => (
                                        <tr key={row.side}>
                                            <td className="px-3 py-3 font-semibold sticky left-0 bg-white z-10">
                                                <span className="block">{row.label}</span>
                                                <span className="block text-xs font-medium text-slate-400">{row.teamLabel}</span>
                                            </td>
                                            {row.innings.map((inningRow, idx) => (
                                                <td key={`${row.side}-${idx}`} className={`px-3 py-3 text-center font-mono ${inningRow?.runs ? 'font-bold text-slate-900' : 'text-slate-400'}`}>
                                                    {activeLineMetric.value(inningRow)}
                                                </td>
                                            ))}
                                            <td className="px-3 py-3 text-center font-mono font-bold border-l border-slate-200">
                                                {activeLineMetric.total(row.innings)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                            <span>Runs: total runs in that half-inning slot.</span>
                            <span>Avg: runs per chance.</span>
                            <span>Scored %: share of halves with at least one run.</span>
                        </div>
                    </div>

                    <aside className="lg:w-80">
                        <h3 className="subsection-title font-bold mb-3">Biggest Half-Inning Bursts</h3>
                        <div className="space-y-2">
                            {data.biggestHalves.map(row => (
                                <button key={`${row.key}-${row.maxGame?.gameId || ''}`} onClick={() => openGame(row.maxGame?.gameId, focusForHalfRow(row))}
                                    className="w-full text-left rounded-lg border border-slate-200 bg-slate-50 p-3 hover:bg-blue-50 transition-colors">
                                    <div className="flex items-center justify-between gap-3">
                                        <span className="font-semibold">{row.key}</span>
                                        <span className="font-mono font-bold text-blue-700">{row.maxRuns} R</span>
                                    </div>
                                    <div className="text-xs text-slate-500 mt-1">{row.maxGame?.date} - {row.maxGame?.matchup}</div>
                                    <div className="text-xs text-slate-400">{row.maxGame?.score}</div>
                                </button>
                            ))}
                        </div>
                    </aside>
                </div>
            </section>

            <section className="bg-white rounded-lg border border-slate-200 p-5" style={{ boxShadow: 'var(--shadow)' }}>
                <div className="flex flex-col lg:flex-row gap-6">
                    <div className="min-w-0 flex-1">
                        <div className="mb-4">
                            <h2 className="section-title font-bold">Batting Around</h2>
                            <p className="body-text text-slate-500 mt-1">
                                Half-innings with 9+ plate appearances and at least one batter who came up more than once.
                            </p>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50">
                                    <tr>
                                        <th className="px-3 py-2 text-left"><SortHeader label="Inning" sortKey="inning" sort={battingSort} setSort={setBattingSort} /></th>
                                        <th className="px-3 py-2 text-left"><SortHeader label="Game" sortKey="date" sort={battingSort} setSort={setBattingSort} /></th>
                                        <th className="px-3 py-2 text-right"><SortHeader label="PA" sortKey="pa" sort={battingSort} setSort={setBattingSort} align="right" /></th>
                                        <th className="px-3 py-2 text-right"><SortHeader label="Runs" sortKey="runs" sort={battingSort} setSort={setBattingSort} align="right" /></th>
                                        <th className="px-3 py-2 text-left"><SortHeader label="Repeat Batters" sortKey="repeat" sort={battingSort} setSort={setBattingSort} /></th>
                                        <th className="px-3 py-2 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {visibleBattingAround.map(group => (
                                        <tr key={group.key} className="hover:bg-blue-50/50 cursor-pointer" onClick={() => openGame(group.gameId, focusForGroup(group))}>
                                            <td className="px-3 py-3">
                                                <div className="font-semibold">{halfLabel(group)}</div>
                                                <div className="text-xs text-slate-500">{group.battingTeam}</div>
                                            </td>
                                            <td className="px-3 py-3">
                                                <div className="font-medium">{group.date} - {group.matchup}</div>
                                                <div className="text-xs text-slate-500">{group.score}</div>
                                            </td>
                                            <td className="px-3 py-3 text-right font-mono font-bold">{group.plateAppearances}</td>
                                            <td className="px-3 py-3 text-right font-mono">{group.runs ?? '-'}</td>
                                            <td className="px-3 py-3">
                                                {group.repeatBatters.length ? (
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {group.repeatBatters.map(batter => (
                                                            <span key={`${group.key}-${batter.playerId || batter.name}`} className="rounded-md bg-amber-50 border border-amber-200 px-2 py-1 text-xs font-semibold text-amber-800">
                                                                {batter.name} ({batter.appearances} PA)
                                                            </span>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <span className="text-slate-400">None</span>
                                                )}
                                            </td>
                                            <td className="px-3 py-3 text-right">
                                                <button onClick={(e) => { e.stopPropagation(); openGame(group.gameId, focusForGroup(group)); }} className="rounded-md bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-blue-700">
                                                    Open inning
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {!visibleBattingAround.length && (
                            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                                No batting-around innings match these filters.
                            </div>
                        )}
                        {sortedBattingAround.length > 12 && (
                            <button onClick={() => setShowAllBatting(!showAllBatting)} className="mt-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50">
                                {showAllBatting ? 'Show top 12' : `Show all ${sortedBattingAround.length}`}
                            </button>
                        )}
                    </div>

                    <aside className="lg:w-96">
                        <div className="mb-3">
                            <h3 className="subsection-title font-bold">Repeat PA In One Inning</h3>
                            <p className="text-xs text-slate-500 mt-1">
                                Batters who made more than one plate appearance in the same half-inning. This is not capped at two.
                            </p>
                        </div>
                        <div className="space-y-3">
                            <input
                                type="search"
                                value={repeatSearch}
                                onChange={(e) => setRepeatSearch(e.target.value)}
                                placeholder="Search player, team, result..."
                                className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
                            />
                            <div className="grid grid-cols-4 gap-1 rounded-lg bg-slate-100 p-1">
                                {[
                                    ['pa', 'PA'],
                                    ['date', 'Date'],
                                    ['player', 'Player'],
                                    ['inning', 'Inning'],
                                ].map(([key, label]) => (
                                    <button
                                        key={key}
                                        onClick={() => toggleSort(repeatSort, setRepeatSort, key)}
                                        className={`rounded-md px-2 py-1.5 text-xs font-semibold transition-colors ${
                                            repeatSort.key === key
                                                ? 'bg-white text-blue-700 shadow-sm'
                                                : 'text-slate-500 hover:text-slate-800'
                                        }`}
                                    >
                                        {label}{repeatSort.key === key ? (repeatSort.dir === 'asc' ? ' ↑' : ' ↓') : ''}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="mt-3 space-y-2 max-h-[560px] overflow-y-auto pr-1">
                            {visibleRepeatEvents.map(event => (
                                <button key={`${event.group.key}-${event.playerId || event.name}`} onClick={() => openGame(event.group.gameId, focusForGroup(event.group))}
                                    className="w-full text-left rounded-lg border border-slate-200 bg-slate-50 p-3 hover:bg-blue-50 transition-colors">
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="min-w-0">
                                            <div className="font-semibold truncate">{event.name}</div>
                                            <div className="text-xs text-slate-500">{halfLabel(event.group)} - {event.group.battingTeam} - {event.group.date}</div>
                                        </div>
                                        <span className="font-mono font-bold text-blue-700 whitespace-nowrap">{event.appearances} PA</span>
                                    </div>
                                    <div className="mt-2 flex flex-wrap gap-1">
                                        {event.results.map((result, idx) => (
                                            <span key={`${event.group.key}-${event.playerId || event.name}-${idx}`} className="rounded bg-white border border-slate-200 px-2 py-0.5 text-xs text-slate-700">
                                                {summarizeResult(result, event.name)}
                                            </span>
                                        ))}
                                    </div>
                                    <div className="mt-2 flex items-center justify-between gap-2">
                                        <div className="text-xs text-slate-400 truncate">{event.group.matchup}</div>
                                        <span className="text-xs font-semibold text-blue-700 whitespace-nowrap">Open inning</span>
                                    </div>
                                </button>
                            ))}
                            {!visibleRepeatEvents.length && (
                                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                                    No repeat plate appearances match these filters.
                                </div>
                            )}
                        </div>
                        {sortedRepeatEvents.length > 30 && (
                            <button onClick={() => setShowAllRepeat(!showAllRepeat)} className="mt-3 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50">
                                {showAllRepeat ? 'Show top 30' : `Show all ${sortedRepeatEvents.length}`}
                            </button>
                        )}
                    </aside>
                </div>
            </section>
        </div>
    );
};

'''
