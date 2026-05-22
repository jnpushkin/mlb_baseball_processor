"""React app chunk: journeys."""

CODE = r'''const DynamicPlayerTable = ({ allPlayers, playerGames, ncaaCrossRef, careerFirstsByPlayer, allTimePassings, milestones, debuts, finalGames }) => {
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
            const aMissing = isMissingValue(aVal);
            const bMissing = isMissingValue(bVal);
            if (aMissing && bMissing) return 0;
            if (aMissing) return 1;
            if (bMissing) return -1;
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
            const aMissing = isMissingValue(aVal);
            const bMissing = isMissingValue(bVal);
            if (aMissing && bMissing) return 0;
            if (aMissing) return 1;
            if (bMissing) return -1;
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
            const aMissing = isMissingValue(aVal);
            const bMissing = isMissingValue(bVal);
            if (aMissing && bMissing) return 0;
            if (aMissing) return 1;
            if (bMissing) return -1;
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
            <div className="overflow-x-auto relative" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                <table className="w-full min-w-full">
                    <thead className="bg-slate-50 sticky top-0 z-10 shadow-[0_1px_0_0_rgba(148,163,184,0.25)]">
                        <tr>{columns.map(col => <th key={col.key} onClick={() => handleSort(col.key)} aria-sort={sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'} className={`px-4 py-3 text-left small-text font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 ${col.headerClassName || ''}`} style={col.headerStyle}>{col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y">
                        {displayData.map((row, idx) => (
                            <tr key={row.gameId || row.id || `item-${idx}`} className={`hover:bg-blue-50 ${idx % 2 === 1 ? 'bg-slate-50/50' : ''} ${onRowClick ? 'cursor-pointer' : ''}`} onClick={() => onRowClick && onRowClick(row)}>
                                {columns.map(col => <td key={col.key} className={`px-4 py-3 body-text align-top ${col.className || ''}`} style={col.style}>{col.render ? col.render(row[col.key], row) : row[col.key]}</td>)}
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

const MilestonesView = ({ milestones, games, careerFirsts, careerLasts, allTimePassings, onTabChange }) => {
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
    const careerLastsCount = careerLasts?.length || 0;
    const careerEventsCount = careerFirstsCount + careerLastsCount;
    const allTimePassingsCount = allTimePassings?.length || 0;
    const isCareerCategory = activeCategory === 'firsts' || activeCategory === 'career-firsts' || activeCategory === 'career-lasts';
    const careerEvents = useMemo(() => [
        ...(careerFirsts || []).map(f => ({
            ...f,
            kind: 'milestone',
            icon: '⭐',
            eventLabel: 'Career Milestone',
            rowTone: 'amber',
        })),
        ...(careerLasts || []).map(l => ({
            ...l,
            kind: 'last',
            icon: '🏁',
            eventLabel: 'Career Last',
            rowTone: 'slate',
        })),
    ], [careerFirsts, careerLasts]);
    const firstCareerEventsCount = careerEvents.filter(e => isFirstCareerEvent(e.milestone)).length;
    const filteredCareerEvents = useMemo(() => {
        const q = searchTerm.toLowerCase();
        return careerEvents.filter(e =>
            (activeCategory !== 'career-firsts' || isFirstCareerEvent(e.milestone)) &&
            (activeCategory !== 'career-lasts' || e.kind === 'last') &&
            (!searchTerm ||
                (e.player_name || '').toLowerCase().includes(q) ||
                (e.milestone || '').toLowerCase().includes(q) ||
                (e.venue || '').toLowerCase().includes(q) ||
                (e.opponent || '').toLowerCase().includes(q)
            )
        );
    }, [careerEvents, searchTerm, activeCategory]);
    const careerSectionTitle = activeCategory === 'career-firsts'
        ? 'First Career Events'
        : activeCategory === 'career-lasts'
            ? 'Career Lasts'
            : 'Career Events Witnessed';
    const careerSectionDescription = activeCategory === 'career-firsts'
        ? 'True first-career stat events you witnessed.'
        : activeCategory === 'career-lasts'
            ? 'Final career stat events you witnessed for retired players.'
            : 'Career milestones and final career stat events you witnessed.';
    const openMilestoneGame = (gameId) => {
        if (!gameId || gameId === 'UNKNOWN') return;
        window._pendingGameId = gameId;
        if (window.__navigateTab) window.__navigateTab('gamelog');
        else if (onTabChange) onTabChange('gamelog');
    };

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
                        {!isCareerCategory && (
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
                        { id: 'all', label: 'All', count: totalCount + careerEventsCount },
                        { id: 'firsts', label: '⭐ Career Events', count: careerEventsCount },
                        { id: 'career-firsts', label: 'Firsts', count: firstCareerEventsCount },
                        { id: 'career-lasts', label: 'Lasts', count: careerLastsCount },
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

            {/* Career Events Section — hidden on All+By Date so career
                milestones and final career events interleave chronologically
                with batting/pitching. */}
            {careerEventsCount > 0 && ((activeCategory === 'all' && viewMode !== 'date') || isCareerCategory) && (
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                    <div className="p-4 bg-gradient-to-r from-amber-500 to-slate-700 text-white">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">⭐</span>
                                <h3 className="text-lg font-bold">{careerSectionTitle}</h3>
                            </div>
                            <span className="bg-white/20 backdrop-blur px-3 py-1 rounded-full text-sm font-bold">
                                {filteredCareerEvents.length} event{filteredCareerEvents.length === 1 ? '' : 's'}
                            </span>
                        </div>
                    </div>
                    <div className="p-4 bg-gradient-to-b from-amber-50 to-white">
                            <div className="flex items-center justify-between mb-4">
                                <p className="text-sm text-amber-700">
                                    {careerSectionDescription}
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
                                const filtered = filteredCareerEvents;

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
                                    if (m.toLowerCase().includes('final career')) return { num: 999999, label: 'Final' };
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
                                                        <span className="text-sm font-medium text-amber-600 min-w-[170px]">{formatLongDate(m.date || m.date_display)}</span>
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
                                                                                <span className="text-xs text-slate-500">({formatLongDate(m.date || m.date_display)})</span>
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
                                                                                <span className="text-xs text-slate-500">({formatLongDate(m.date || m.date_display)})</span>
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
                </div>
            )}

            {/* All-Time List Passings Section */}
            {/* Date view - flat chronological list */}
            {viewMode === 'date' && !isCareerCategory && (() => {
                const parseDate = toSortableDate;
                const battingPitchingItems = (milestones || []).filter(m => {
                    if (activeCategory === 'batting' && categoryConfig[m.type]?.category !== 'batting') return false;
                    if (activeCategory === 'pitching' && categoryConfig[m.type]?.category !== 'pitching') return false;
                    if (searchTerm) {
                        const q = searchTerm.toLowerCase();
                        return (m.player || '').toLowerCase().includes(q) || (m.type || '').toLowerCase().includes(q) || (m.detail || '').toLowerCase().includes(q);
                    }
                    return true;
                });

                // On the All tab, fold career events into the same chronological
                // stream so they aren't quarantined in a separate banner.
                const careerItems = (activeCategory === 'all')
                    ? filteredCareerEvents.map(f => ({
                            _isCareer: true,
                            _careerKind: f.kind,
                            _careerIcon: f.icon,
                            _careerLabel: f.eventLabel,
                            gameId: f.game_id,
                            player: f.player_name,
                            playerId: f.player_id,
                            type: f.eventLabel,
                            detail: f.milestone,
                            _careerDate: formatLongDate(f.date || f.date_display),
                            _careerSortDate: f.date,
                        }))
                    : [];

                const sortKey = (m) => {
                    if (m._isCareer) return m._careerSortDate || '';
                    const game = gameMap[m.gameId];
                    return game ? parseDate(game.date) : '';
                };

                const allFiltered = [...battingPitchingItems, ...careerItems].map((m, i) => {
                    const game = gameMap[m.gameId];
                    const config = categoryConfig[m.type] || {};
                    const sort = sortKey(m);
                    const isLast = m._careerKind === 'last';
                    const dateRaw = m._isCareer ? (m._careerSortDate || m._careerDate) : (game?.date || m.date || sort);
                    return {
                        ...m,
                        _idx: i,
                        game,
                        sort,
                        dateLabel: formatLongDate(dateRaw),
                        icon: m._isCareer ? m._careerIcon : (config.icon || '🏆'),
                        badgeLabel: m._isCareer ? m._careerLabel : m.type,
                        badgeClass: m._isCareer
                            ? (isLast ? 'bg-slate-200 text-slate-700' : 'bg-amber-100 text-amber-700')
                            : 'bg-slate-100 text-slate-700',
                        rowClass: m._isCareer
                            ? (isLast ? 'hover:bg-slate-50' : 'hover:bg-amber-50')
                            : 'hover:bg-blue-50',
                        detailClass: m._isCareer
                            ? (isLast ? 'text-slate-700' : 'text-amber-800')
                            : 'text-slate-600',
                    };
                }).sort((a, b) => b.sort.localeCompare(a.sort));

                const dateGroups = [];
                const dateLookup = {};
                allFiltered.forEach(item => {
                    const dateKey = item.sort || 'unknown-date';
                    if (!dateLookup[dateKey]) {
                        dateLookup[dateKey] = { key: dateKey, label: item.dateLabel || 'Unknown date', games: [], gameLookup: {} };
                        dateGroups.push(dateLookup[dateKey]);
                    }
                    const group = dateLookup[dateKey];
                    const gameKey = item.gameId || `unknown-${dateKey}`;
                    if (!group.gameLookup[gameKey]) {
                        const game = item.game;
                        group.gameLookup[gameKey] = {
                            key: gameKey,
                            gameId: item.gameId,
                            game,
                            label: game ? `${game.awayTeam} @ ${game.homeTeam}` : (item.gameId || 'Unknown game'),
                            items: [],
                        };
                        group.games.push(group.gameLookup[gameKey]);
                    }
                    group.gameLookup[gameKey].items.push(item);
                });

                return (
                    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                        <div className="p-4 border-b bg-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                            <span className="font-bold body-text">{allFiltered.length} events</span>
                            <span className="text-xs font-medium text-slate-500">Grouped by date and game</span>
                        </div>
                        <div className="bg-slate-50/70" style={{ maxHeight: '720px', overflowY: 'auto' }}>
                            {dateGroups.map(dateGroup => (
                                <section key={dateGroup.key} className="border-b border-slate-200 last:border-b-0">
                                    <div className="sticky top-0 z-10 px-4 py-3 bg-slate-100/95 backdrop-blur border-b border-slate-200 flex items-center justify-between gap-3">
                                        <h3 className="text-sm font-bold text-slate-900">{dateGroup.label}</h3>
                                        <span className="text-xs font-medium text-slate-500">{dateGroup.games.reduce((sum, g) => sum + g.items.length, 0)} event{dateGroup.games.reduce((sum, g) => sum + g.items.length, 0) === 1 ? '' : 's'}</span>
                                    </div>
                                    <div className="p-3 space-y-3">
                                        {dateGroup.games.map(gameGroup => {
                                            const game = gameGroup.game;
                                            const canOpen = gameGroup.gameId && gameGroup.gameId !== 'UNKNOWN';
                                            const score = game && game.awayScore !== undefined && game.homeScore !== undefined
                                                ? `${game.awayTeam} ${game.awayScore} - ${game.homeScore} ${game.homeTeam}`
                                                : '';
                                            return (
                                                <div key={gameGroup.key} className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                                                    <div className="px-3 py-2 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                                                        <div className="min-w-0">
                                                            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                                                                {game ? (
                                                                    <>
                                                                        <TeamToken code={game.awayTeam} logoSize={16} />
                                                                        <span className="text-slate-400">@</span>
                                                                        <TeamToken code={game.homeTeam} logoSize={16} />
                                                                    </>
                                                                ) : (
                                                                    <span>{gameGroup.label}</span>
                                                                )}
                                                            </div>
                                                            <div className="text-xs text-slate-500 truncate">
                                                                {[score, game?.venue].filter(Boolean).join(' • ')}
                                                            </div>
                                                        </div>
                                                        {canOpen && (
                                                            <button
                                                                type="button"
                                                                onClick={() => openMilestoneGame(gameGroup.gameId)}
                                                                className="self-start sm:self-center text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
                                                            >
                                                                Open game
                                                            </button>
                                                        )}
                                                    </div>
                                                    <div className="divide-y divide-slate-100">
                                                        {gameGroup.items.map(item => (
                                                            <button
                                                                key={`${item._isCareer ? item._careerKind : 'milestone'}-${item.gameId}-${item.playerId || item.player}-${item.type}-${item._idx}`}
                                                                type="button"
                                                                disabled={!canOpen}
                                                                onClick={() => openMilestoneGame(item.gameId)}
                                                                className={`w-full px-3 py-2.5 text-left flex items-start gap-3 transition-colors ${canOpen ? `cursor-pointer ${item.rowClass}` : 'cursor-default'}`}
                                                            >
                                                                <span className="text-lg leading-5 shrink-0">{item.icon}</span>
                                                                <div className="flex-1 min-w-0">
                                                                    <div className="flex items-center gap-2 flex-wrap">
                                                                        <span className="font-semibold text-sm text-slate-900">{item.player}</span>
                                                                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${item.badgeClass}`}>{item.badgeLabel}</span>
                                                                    </div>
                                                                    {item.detail && <div className={`text-xs font-medium mt-0.5 truncate ${item.detailClass}`}>{item.detail}</div>}
                                                                </div>
                                                                {canOpen && <span className="text-xs font-semibold text-blue-500 shrink-0 mt-0.5">Open</span>}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </section>
                            ))}
                            {allFiltered.length === 0 && (
                                <div className="p-8 text-center text-sm text-slate-500">No events match the current filters.</div>
                            )}
                        </div>
                    </div>
                );
            })()}

            {/* Milestone groups - category view */}
            {viewMode === 'category' && !isCareerCategory && (
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

'''
