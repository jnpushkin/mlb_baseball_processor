"""React app chunk: badges."""

CODE = r'''class ErrorBoundary extends React.Component {
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
            <div className={`bg-white rounded-lg border hover:shadow-sm transition-all overflow-hidden ${isExpanded ? 'border-blue-300 shadow-sm' : 'border-slate-200'} ${isExpanded && !compact ? 'md:col-span-2 lg:col-span-3' : ''}`}>
                <div className={`${compact ? 'p-2.5' : 'p-3'} ${hasDetail ? 'cursor-pointer' : ''}`}
                    onClick={() => hasDetail && setExpandedRecord(isExpanded ? null : key)}>
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                            <div className={`${compact ? 'text-xs' : 'text-sm'} font-semibold text-slate-900 leading-tight`}>{record.record}</div>
                            {!isExpanded && previewText && (
                                <div className="text-[11px] text-slate-500 mt-1 leading-snug"
                                    style={{ display: '-webkit-box', WebkitLineClamp: compact ? 1 : 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                    {previewText}
                                </div>
                            )}
                        </div>
                        <div className={`${compact ? 'text-base' : 'text-xl'} font-bold text-blue-600 flex-shrink-0 leading-none`}>{record.value}</div>
                    </div>
                </div>
                {isExpanded && hasDetail && (
                    <div className="px-3 pb-3 border-t pt-3">
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
                            return (
                                <div className={`grid grid-cols-1 ${grouped.length > 1 && !compact ? 'md:grid-cols-2' : ''} gap-2`}>
                                {grouped.map((group, gi) => (
                                <div key={gi} className="bg-slate-50 rounded-lg p-2.5 text-xs border border-slate-100">
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
                                            <div key={di} className="text-slate-700 leading-snug">{d}</div>
                                        ))}
                                    </div>
                                </div>
                                ))}
                                </div>
                            );
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
                        const RoleRateCell = ({ total, overturned, rate }) => {
                            if (!total) return <span className="text-slate-400">-</span>;
                            const resolvedRate = rate != null ? rate : Math.round(((overturned || 0) / total) * 100);
                            const rateClass = resolvedRate >= 75 ? 'text-green-600' : resolvedRate >= 50 ? 'text-slate-700' : 'text-red-600';
                            return (
                                <div className="leading-tight">
                                    <div className={`font-bold ${rateClass}`}>{resolvedRate}%</div>
                                    <div className="text-[11px] text-slate-400">({overturned || 0}/{total})</div>
                                </div>
                            );
                        };
                        return (
                        <div className="mt-3 bg-white border border-slate-200 rounded-lg p-4">
                            <div className="mb-3">
                                <div className="text-xs font-semibold text-slate-400 uppercase">Player Challenge Leaderboard</div>
                                <div className="text-[11px] text-slate-500 mt-1">Role columns show success rate; small counts are overturned/challenges.</div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-slate-50 border-b">
                                        <tr>
                                            <AbsHeader k="name" label="Player" />
                                            <AbsHeader k="challenges" label="Challenges" />
                                            <AbsHeader k="overturned" label="Overturned" />
                                            <AbsHeader k="upheld" label="Upheld" />
                                            <AbsHeader k="successRate" label="Success %" />
                                            <AbsHeader k="batterSuccessRate" label="Batter %" />
                                            <AbsHeader k="catcherSuccessRate" label="Catcher %" />
                                            <AbsHeader k="pitcherSuccessRate" label="Pitcher %" />
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
                                                <td className="px-2 py-2 text-center text-slate-600">
                                                    <RoleRateCell total={p.asBatter} overturned={p.batterOverturned} rate={p.batterSuccessRate} />
                                                </td>
                                                <td className="px-2 py-2 text-center text-slate-600">
                                                    <RoleRateCell total={p.asCatcher} overturned={p.catcherOverturned} rate={p.catcherSuccessRate} />
                                                </td>
                                                <td className="px-2 py-2 text-center text-slate-600">
                                                    <RoleRateCell total={p.asPitcher} overturned={p.pitcherOverturned} rate={p.pitcherSuccessRate} />
                                                </td>
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

'''
