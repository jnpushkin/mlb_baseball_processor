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

const AwardProgressBar = ({ seen, total }) => {
    const pct = total ? Math.round((seen / total) * 100) : 0;
    return (
        <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
            <div className="h-full bg-emerald-600 rounded-full" style={{ width: `${Math.min(100, pct)}%` }} />
        </div>
    );
};

const AwardSetStatusBadge = ({ awardSet }) => {
    if (!awardSet) return null;
    if (awardSet.isComplete) {
        return <span className="small-text font-bold px-2 py-1 rounded-full bg-emerald-100 text-emerald-700">Badge earned</span>;
    }
    if ((awardSet.seen || 0) > 0) {
        return <span className="small-text font-bold px-2 py-1 rounded-full bg-amber-100 text-amber-700">{awardSet.missing} away</span>;
    }
    return <span className="small-text font-bold px-2 py-1 rounded-full bg-slate-100 text-slate-600">Not started</span>;
};

const cleanAwardToken = (value) => String(value || '').replace(/\s+/g, ' ').trim();
const normalizeAwardToken = (value) => cleanAwardToken(value).toLowerCase();
const isRedundantAwardDetail = (detail, award, league) => {
    const d = normalizeAwardToken(detail);
    const a = normalizeAwardToken(award);
    const l = normalizeAwardToken(league);
    if (!d) return true;
    if (d === a || d === l) return true;
    if (a && l && d === `${l} ${a}`) return true;
    if (a && l && d.startsWith(`${l} `) && d.endsWith(a)) return true;
    return false;
};
const appendAwardToken = (parts, token) => {
    const clean = cleanAwardToken(token);
    if (!clean) return;
    const normalized = normalizeAwardToken(clean);
    if (parts.some(part => normalizeAwardToken(part) === normalized)) return;
    parts.push(clean);
};
const formatAwardEntryShortLabel = (row) => {
    const award = cleanAwardToken(row.award || row.awardDetail || 'Award');
    const detail = cleanAwardToken(row.awardDetail);
    const parts = [];
    appendAwardToken(parts, award);
    if (!isRedundantAwardDetail(detail, award, row.league)) appendAwardToken(parts, detail);
    if (row.selection && !normalizeAwardToken(detail).includes(normalizeAwardToken(row.selection))) appendAwardToken(parts, row.selection);
    appendAwardToken(parts, row.position);
    appendAwardToken(parts, row.month);
    if (row.weekEnding) appendAwardToken(parts, `Week ending ${row.weekEnding}`);
    return parts.join(', ');
};
const formatAwardEntryFullLabel = (row) => {
    const context = [row.year, row.league].map(cleanAwardToken).filter(Boolean);
    const summary = formatAwardEntryShortLabel(row);
    return [...context, summary].filter(Boolean).join(' ');
};
const formatAwardSetMemberSummary = (rows) => {
    if (!rows.length) return '';
    const firstLabel = rows.length === 1
        ? formatAwardEntryShortLabel(rows[0])
        : formatAwardEntryFullLabel(rows[0]);
    return rows.length === 1 ? firstLabel : `${rows.length} entries, latest ${firstLabel}`;
};
const awardSelectionRank = (selection) => {
    const clean = cleanAwardToken(selection);
    if (clean === 'Starter') return 0;
    if (clean === 'Starting Pitcher') return 1;
    if (clean === 'Reserve') return 2;
    return 9;
};

const buildAwardSetMembers = (awardSet, groups) => {
    const criteria = awardSet?.criteria || {};
    const awardKeys = new Set(criteria.awardKeys || []);
    const valueList = (value) => Array.isArray(value) ? value : value ? [value] : [];
    const leagues = new Set(valueList(criteria.leagues || criteria.league).map(v => String(v)));
    const selections = new Set(valueList(criteria.selections || criteria.selection).map(v => String(v)));
    const positions = new Set(valueList(criteria.positions || criteria.position).map(v => String(v)));
    const excludedPositions = new Set(valueList(criteria.excludePositions).map(v => String(v)));
    const rows = [];
    const seenIds = new Set();
    (groups || []).forEach(group => {
        if (awardKeys.size && !awardKeys.has(group.awardKey)) return;
        (group.items || []).forEach(item => {
            if (criteria.year && Number(item.year || 0) !== Number(criteria.year)) return;
            if (criteria.gameKey && String(item.gameKey || '') !== String(criteria.gameKey)) return;
            if (leagues.size && !leagues.has(String(item.league || ''))) return;
            if (selections.size && !selections.has(String(item.selection || item.awardDetail || ''))) return;
            if (positions.size && !positions.has(String(item.position || ''))) return;
            if (excludedPositions.size && excludedPositions.has(String(item.position || ''))) return;
            if (!item.playerId || seenIds.has(item.id)) return;
            seenIds.add(item.id);
            const normalizedItem = {
                ...item,
                awardKey: item.awardKey || group.awardKey || '',
                award: item.award || group.award || '',
            };
            if (!normalizedItem.awardDetail) normalizedItem.awardDetail = normalizedItem.award;
            rows.push(normalizedItem);
        });
    });

    return rows.map((item, index) => {
        const itemId = item.id || `${item.playerId}:${item.awardKey}:${item.year}:${item.league}:${item.awardDetail}:${index}`;
        const checked = !!item.checked;
        return {
            id: `${awardSet.id}:${itemId}`,
            itemId,
            playerId: item.playerId,
            name: item.name,
            checked,
            gamesSeen: checked ? Number(item.gamesSeen || 0) : 0,
            firstSeen: checked ? item.firstSeen || '' : '',
            lastSeen: checked ? item.lastSeen || '' : '',
            awardCount: 1,
            awardSummary: formatAwardSetMemberSummary([item]),
            year: item.year,
            league: item.league || '',
            awardKey: item.awardKey || '',
            award: item.award || '',
            awardDetail: item.awardDetail || '',
            team: item.team || '',
            position: item.position || '',
            selection: item.selection || '',
            month: item.month || '',
            weekEnding: item.weekEnding || '',
            gameKey: item.gameKey || '',
            gameLabel: item.gameLabel || '',
            gameNumber: Number(item.gameNumber || 1),
            rosterOrder: Number(item.rosterOrder || 0),
            sourceUrl: item.sourceUrl || '',
        };
    }).sort((a, b) => {
        const yearDiff = Number(b.year || 0) - Number(a.year || 0);
        if (yearDiff) return yearDiff;
        if (a.awardKey === 'all_star' || b.awardKey === 'all_star') {
            const gameDiff = String(b.gameKey || '').localeCompare(String(a.gameKey || ''));
            if (gameDiff) return gameDiff;
            const leagueDiff = (a.league || '').localeCompare(b.league || '');
            if (leagueDiff) return leagueDiff;
            const selectionDiff = awardSelectionRank(a.selection || a.awardDetail) - awardSelectionRank(b.selection || b.awardDetail);
            if (selectionDiff) return selectionDiff;
            const rosterDiff = Number(a.rosterOrder || 0) - Number(b.rosterOrder || 0);
            if (rosterDiff) return rosterDiff;
        }
        const metaDiff = `${a.league || ''}${a.awardDetail || ''}${a.selection || ''}${a.position || ''}`.localeCompare(`${b.league || ''}${b.awardDetail || ''}${b.selection || ''}${b.position || ''}`);
        if (metaDiff) return metaDiff;
        return (a.name || '').localeCompare(b.name || '');
    });
};

const AwardSetCard = ({ awardSet, selected, onSelect, onOpen }) => (
    <div
        className={`bg-white rounded-lg border p-4 space-y-3 transition-all ${selected ? 'border-blue-300 ring-1 ring-blue-100' : awardSet.isComplete ? 'border-emerald-200' : 'border-slate-200 hover:border-slate-300'}`}
        style={{ boxShadow: 'var(--shadow)' }}
        onClick={() => onSelect(awardSet)}
    >
        <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
                <h3 className="subsection-title font-bold text-slate-900 truncate">{awardSet.title}</h3>
                <p className="small-text text-slate-500 mt-1 leading-snug">{awardSet.subtitle}</p>
            </div>
            <div className="text-right flex-shrink-0">
                <div className="text-xl font-bold text-slate-900">{awardSet.seen}/{awardSet.total}</div>
                <div className="small-text text-slate-400">{awardSet.completionPct}%</div>
            </div>
        </div>
        <AwardProgressBar seen={awardSet.seen} total={awardSet.total} />
        <div className="flex items-center justify-between gap-3">
            <AwardSetStatusBadge awardSet={awardSet} />
            <button
                type="button"
                onClick={(event) => { event.stopPropagation(); onOpen(awardSet); }}
                className="small-text font-semibold text-blue-700 hover:text-blue-900 px-2 py-1 rounded hover:bg-blue-50"
            >
                Open checklist
            </button>
        </div>
    </div>
);

const AwardSetMemberRow = ({ member, selected, onSelect }) => (
    <div
        role="button"
        tabIndex={0}
        onClick={() => onSelect(member)}
        onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') onSelect(member); }}
        className={`w-full grid grid-cols-[24px_minmax(0,1fr)_auto] items-center gap-3 text-left rounded-lg border px-3 py-2.5 ${selected ? 'border-blue-300 bg-blue-50' : 'border-slate-200 bg-white hover:bg-slate-50'}`}
    >
        <input
            type="checkbox"
            checked={!!member.checked}
            readOnly
            tabIndex={-1}
            aria-label={member.checked ? 'Seen' : 'Not seen'}
            className="h-4 w-4 rounded border-slate-300 text-emerald-600"
        />
        <div className="min-w-0">
            <div className="body-text font-semibold text-slate-900 truncate">{member.name}</div>
            <div className="small-text text-slate-500 truncate">{member.awardSummary}</div>
        </div>
        <div className="text-right flex-shrink-0">
            {member.checked ? (
                <span className="small-text font-bold px-2 py-1 rounded-full bg-emerald-100 text-emerald-700">{member.gamesSeen} games</span>
            ) : (
                <span className="small-text font-bold px-2 py-1 rounded-full bg-amber-100 text-amber-700">Missing</span>
            )}
        </div>
    </div>
);

const AwardSetDetailPanel = ({ awardSet, selectedMember, onSelectMember, onOpen }) => {
    if (!awardSet) return null;
    const previewMembers = (awardSet.members || []).slice(0, 8);
    const missingNames = (awardSet.nextMissing || []).filter(Boolean).slice(0, 4);
    return (
        <div className="space-y-4">
            <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-4" style={{ boxShadow: 'var(--shadow)' }}>
                <div className="flex items-start justify-between gap-3">
                    <div>
                        <div className="small-text font-bold uppercase text-slate-500 mb-1">Selected Set</div>
                        <h3 className="section-title font-bold text-slate-900">{awardSet.title}</h3>
                        <p className="small-text text-slate-500 mt-1 leading-snug">{awardSet.subtitle}</p>
                    </div>
                    <AwardSetStatusBadge awardSet={awardSet} />
                </div>
                <div className="grid grid-cols-4 gap-2">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-center">
                        <div className="text-lg font-bold text-slate-900">{awardSet.seen}</div>
                        <div className="small-text text-slate-500">Seen</div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-center">
                        <div className="text-lg font-bold text-slate-900">{awardSet.total}</div>
                        <div className="small-text text-slate-500">Total</div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-center">
                        <div className="text-lg font-bold text-slate-900">{awardSet.missing}</div>
                        <div className="small-text text-slate-500">Left</div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-center">
                        <div className="text-lg font-bold text-slate-900">{awardSet.completionPct}%</div>
                        <div className="small-text text-slate-500">Done</div>
                    </div>
                </div>
                <AwardProgressBar seen={awardSet.seen} total={awardSet.total} />
                {missingNames.length > 0 && (
                    <div className="small-text text-slate-500">
                        <span className="font-semibold text-slate-700">Next missing: </span>{missingNames.join(', ')}
                    </div>
                )}
                <button
                    type="button"
                    onClick={() => onOpen(awardSet)}
                    className="w-full px-4 py-2 rounded-lg bg-blue-600 text-white body-text font-semibold hover:bg-blue-700"
                >
                    Open checklist
                </button>
            </div>

            <div className="space-y-2">
                {previewMembers.map(member => (
                    <AwardSetMemberRow
                        key={member.id}
                        member={member}
                        selected={selectedMember?.id === member.id}
                        onSelect={onSelectMember}
                    />
                ))}
            </div>
        </div>
    );
};

const AwardChecklistDrillIn = ({ awardSet, seenPlayers, playerGames, pitcherGames, gamesById, entryLabel = 'Award Entries', onBack }) => {
    const [seenOnly, setSeenOnly] = useState(false);
    const [search, setSearch] = useState('');
    const firstSeenMember = (awardSet?.members || []).find(member => member.checked) || (awardSet?.members || [])[0] || null;
    const [selectedMember, setSelectedMember] = useState(firstSeenMember);

    useEffect(() => {
        const members = awardSet?.members || [];
        if (!members.some(member => member.id === selectedMember?.id)) {
            setSelectedMember(members.find(member => member.checked) || members[0] || null);
        }
    }, [awardSet?.id]);

    const rows = useMemo(() => {
        let members = awardSet?.members || [];
        if (seenOnly) members = members.filter(member => member.checked);
        if (search.trim()) {
            const needle = search.trim().toLowerCase();
            members = members.filter(member => (
                `${member.name} ${member.awardSummary} ${member.league} ${member.team}`.toLowerCase().includes(needle)
            ));
        }
        return members;
    }, [awardSet, seenOnly, search]);

    useEffect(() => {
        if (selectedMember && !rows.some(row => row.id === selectedMember.id)) {
            setSelectedMember(rows.find(row => row.checked) || rows[0] || null);
        }
    }, [rows, selectedMember]);

    if (!awardSet) return null;

    return (
        <div className="space-y-4">
            <div className="bg-white rounded-lg border border-slate-200 p-4" style={{ boxShadow: 'var(--shadow)' }}>
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <button
                            type="button"
                            onClick={onBack}
                            className="small-text font-semibold text-blue-700 hover:text-blue-900 mb-2"
                        >
                            Back to completion sets
                        </button>
                        <h2 className="section-title font-bold text-slate-900">{awardSet.title}</h2>
                        <p className="small-text text-slate-500 mt-1">{awardSet.subtitle}</p>
                    </div>
                    <div className="min-w-[200px]">
                        <div className="flex items-center justify-between small-text text-slate-500 mb-1">
                            <span>{awardSet.seen} of {awardSet.total}</span>
                            <span>{awardSet.completionPct}%</span>
                        </div>
                        <AwardProgressBar seen={awardSet.seen} total={awardSet.total} />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_420px] gap-4">
                <div className="bg-white rounded-lg border border-slate-200 overflow-hidden" style={{ boxShadow: 'var(--shadow)' }}>
                    <div className="flex flex-wrap items-center gap-3 justify-between p-4 border-b border-slate-100">
                        <div className="flex flex-wrap items-center gap-3">
                            <label className="inline-flex items-center gap-2 body-text text-slate-700 border border-slate-200 rounded-lg px-3 py-2">
                                <input
                                    type="checkbox"
                                    checked={seenOnly}
                                    onChange={(event) => setSeenOnly(event.target.checked)}
                                    className="h-4 w-4 rounded border-slate-300 text-emerald-600"
                                />
                                <span>Seen only</span>
                            </label>
                            <input
                                type="text"
                                value={search}
                                onChange={(event) => setSearch(event.target.value)}
                                placeholder={`Search ${entryLabel.toLowerCase()}...`}
                                className="px-3 py-2 body-text border border-slate-200 rounded-lg min-w-[220px] focus:border-blue-500 focus:outline-none"
                            />
                        </div>
                        <div className="small-text text-slate-500">{rows.length} of {awardSet.members?.length || 0}</div>
                    </div>
                    <div className="divide-y divide-slate-100 max-h-[640px] overflow-y-auto">
                        {rows.map(member => (
                            <div
                                role="button"
                                tabIndex={0}
                                key={member.id}
                                onClick={() => setSelectedMember(member)}
                                onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') setSelectedMember(member); }}
                                className={`w-full grid grid-cols-[28px_70px_minmax(0,1fr)_90px_86px] max-sm:grid-cols-[28px_54px_minmax(0,1fr)] items-center gap-3 text-left px-4 py-3 hover:bg-blue-50 ${selectedMember?.id === member.id ? 'bg-blue-50' : ''}`}
                            >
                                <input
                                    type="checkbox"
                                    checked={!!member.checked}
                                    readOnly
                                    tabIndex={-1}
                                    aria-label={member.checked ? 'Seen' : 'Not seen'}
                                    className="h-4 w-4 rounded border-slate-300 text-emerald-600"
                                />
                                <div className="font-bold text-slate-700 body-text">
                                    {member.year || ''}
                                    <div className="small-text text-slate-500 font-semibold">{member.league || ''}</div>
                                </div>
                                <div className="min-w-0">
                                    <div className="body-text font-bold text-slate-900 truncate">
                                        <PlayerLink playerId={member.playerId} name={member.name} />
                                    </div>
                                    <div className="small-text text-slate-500 truncate">{member.awardSummary}</div>
                                </div>
                                <div className="max-sm:hidden">
                                    {member.checked ? (
                                        <span className="small-text font-bold px-2 py-1 rounded-full bg-emerald-100 text-emerald-700">{member.gamesSeen} games</span>
                                    ) : (
                                        <span className="small-text font-bold px-2 py-1 rounded-full bg-amber-100 text-amber-700">Missing</span>
                                    )}
                                </div>
                                <div className="small-text text-slate-500 text-right max-sm:hidden">{member.firstSeen || ''}</div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="lg:sticky lg:top-4 self-start">
                    {selectedMember?.checked ? (
                        <AwardWinnerDetail
                            item={selectedMember}
                            seen={seenPlayers[selectedMember.playerId]}
                            playerGames={playerGames || []}
                            pitcherGames={pitcherGames || []}
                            gamesById={gamesById}
                        />
                    ) : selectedMember ? (
                        <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-3" style={{ boxShadow: 'var(--shadow)' }}>
                            <div>
                                <h3 className="section-title font-semibold text-slate-900">
                                    <PlayerLink playerId={selectedMember.playerId} name={selectedMember.name} />
                                </h3>
                                <div className="small-text text-slate-500 mt-1">{selectedMember.awardSummary}</div>
                            </div>
                            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                                <div className="body-text font-semibold text-amber-800">Not checked off yet</div>
                                <div className="small-text text-amber-700 mt-1">This player has not appeared in your attended games, so there are no live stats to show yet.</div>
                            </div>
                        </div>
                    ) : (
                        <EmptyState title={`No ${entryLabel}`} message="No entries match the current filters." />
                    )}
                </div>
            </div>
        </div>
    );
};

const AwardChecklistsView = ({ awardChecklists, playerGames, pitcherGames, games }) => {
    const groups = awardChecklists?.groups || [];
    const completionSets = awardChecklists?.completionSets || [];
    const awardSets = useMemo(() => completionSets.map(awardSet => ({
        ...awardSet,
        members: buildAwardSetMembers(awardSet, groups),
    })), [completionSets, groups]);
    const seenPlayers = awardChecklists?.seenPlayers || {};
    const totals = awardChecklists?.metadata || {};
    const entryLabel = totals.entryLabel || 'Award Entries';
    const allSetsSubtitle = totals.allSetsSubtitle || 'Every award collection';
    const emptyTitle = totals.emptyTitle || 'No Award Data';
    const emptyMessage = totals.emptyMessage || 'Run the awards scraper to generate award checklist data.';
    const firstSet = awardSets.find(set => set.status === 'started') || awardSets.find(set => set.isComplete) || awardSets[0];
    const [selectedSetId, setSelectedSetId] = useState(firstSet?.id || '');
    const [selectedMember, setSelectedMember] = useState(null);
    const [screen, setScreen] = useState('sets');
    const [libraryFilter, setLibraryFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('all');
    const [search, setSearch] = useState('');

    useEffect(() => {
        if (!awardSets.some(set => set.id === selectedSetId) && awardSets[0]) {
            setSelectedSetId(awardSets[0].id);
        }
    }, [awardSets, selectedSetId]);

    const selectedSet = awardSets.find(set => set.id === selectedSetId) || awardSets[0] || null;
    const gamesById = useMemo(() => {
        const lookup = {};
        (games || []).forEach(game => {
            if (game.gameId) lookup[game.gameId] = game;
        });
        return lookup;
    }, [games]);

    const libraryStats = useMemo(() => {
        const stats = {};
        awardSets.forEach(set => {
            const key = set.library || 'Other';
            if (!stats[key]) stats[key] = { label: key, count: 0, complete: 0, seen: 0, total: 0 };
            stats[key].count += 1;
            stats[key].complete += set.isComplete ? 1 : 0;
            stats[key].seen += set.seen || 0;
            stats[key].total += set.total || 0;
        });
        return Object.values(stats).sort((a, b) => a.label.localeCompare(b.label));
    }, [awardSets]);

    const filteredSets = useMemo(() => {
        const needle = search.trim().toLowerCase();
        return awardSets.filter(set => {
            if (libraryFilter !== 'all' && set.library !== libraryFilter) return false;
            if (statusFilter === 'complete' && !set.isComplete) return false;
            if (statusFilter === 'started' && (set.isComplete || !(set.seen > 0))) return false;
            if (statusFilter === 'empty' && set.seen > 0) return false;
            if (needle) {
                const text = `${set.title} ${set.subtitle} ${set.library} ${(set.nextMissing || []).join(' ')}`.toLowerCase();
                if (!text.includes(needle)) return false;
            }
            return true;
        }).sort((a, b) => {
            if (a.isComplete !== b.isComplete) return a.isComplete ? 1 : -1;
            if ((a.seen > 0) !== (b.seen > 0)) return a.seen > 0 ? -1 : 1;
            return (b.completionPct || 0) - (a.completionPct || 0) || a.title.localeCompare(b.title);
        });
    }, [awardSets, libraryFilter, statusFilter, search]);

    useEffect(() => {
        if (!selectedMember && selectedSet?.members?.length) {
            setSelectedMember(selectedSet.members.find(member => member.checked) || selectedSet.members[0]);
        }
    }, [selectedSet?.id, selectedMember]);

    const selectSet = (awardSet) => {
        setSelectedSetId(awardSet.id);
        setSelectedMember((awardSet.members || []).find(member => member.checked) || (awardSet.members || [])[0] || null);
    };

    const openSet = (awardSet) => {
        selectSet(awardSet);
        setScreen('checklist');
        setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 0);
    };

    if (!groups.length || !awardSets.length) {
        return <EmptyState title={emptyTitle} message={emptyMessage} />;
    }

    if (screen === 'checklist') {
        return (
            <AwardChecklistDrillIn
                awardSet={selectedSet}
                seenPlayers={seenPlayers}
                playerGames={playerGames || []}
                pitcherGames={pitcherGames || []}
                gamesById={gamesById}
                entryLabel={entryLabel}
                onBack={() => setScreen('sets')}
            />
        );
    }

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard title="Checked Off" value={(totals.seenCount || 0).toLocaleString()} subtitle={`${totals.uniqueSeenPlayers || 0} players seen`} color="blue" />
                <StatCard title={entryLabel} value={(totals.entryCount || 0).toLocaleString()} color="green" />
                <StatCard title="Completion Sets" value={(totals.setCount || awardSets.length).toLocaleString()} subtitle={`${totals.completedSetCount || 0} complete`} color="purple" />
                <StatCard title="Categories" value={(totals.groupCount || groups.length).toLocaleString()} color="orange" />
            </div>

            <div className="bg-white rounded-lg border border-slate-200 overflow-hidden" style={{ boxShadow: 'var(--shadow)' }}>
                <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-slate-100">
                    <div className="flex flex-wrap items-center gap-2">
                        <button onClick={() => setStatusFilter('all')} className={`px-3 py-2 rounded-lg body-text font-semibold ${statusFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>All</button>
                        <button onClick={() => setStatusFilter('complete')} className={`px-3 py-2 rounded-lg body-text font-semibold ${statusFilter === 'complete' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>Completed</button>
                        <button onClick={() => setStatusFilter('started')} className={`px-3 py-2 rounded-lg body-text font-semibold ${statusFilter === 'started' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>In Progress</button>
                        <button onClick={() => setStatusFilter('empty')} className={`px-3 py-2 rounded-lg body-text font-semibold ${statusFilter === 'empty' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>Not Started</button>
                    </div>
                    <input
                        type="text"
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        placeholder="Search completion sets..."
                        className="px-3 py-2 body-text border border-slate-200 rounded-lg min-w-[240px] focus:border-blue-500 focus:outline-none"
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-[240px_minmax(0,1fr)_320px] min-h-[620px]">
                    <aside className="border-r border-slate-200 bg-slate-50 p-4 space-y-3">
                        <button
                            type="button"
                            onClick={() => setLibraryFilter('all')}
                            className={`w-full text-left rounded-lg border px-3 py-2.5 ${libraryFilter === 'all' ? 'border-blue-300 bg-blue-50' : 'border-slate-200 bg-white hover:bg-slate-50'}`}
                        >
                            <div className="flex items-center justify-between gap-3">
                                <span className="body-text font-bold text-slate-900">All Sets</span>
                                <span className="small-text font-bold text-slate-500">{awardSets.length}</span>
                            </div>
                            <div className="small-text text-slate-500 mt-1">{allSetsSubtitle}</div>
                        </button>
                        {libraryStats.map(library => (
                            <button
                                type="button"
                                key={library.label}
                                onClick={() => setLibraryFilter(library.label)}
                                className={`w-full text-left rounded-lg border px-3 py-2.5 ${libraryFilter === library.label ? 'border-blue-300 bg-blue-50' : 'border-slate-200 bg-white hover:bg-slate-50'}`}
                            >
                                <div className="flex items-center justify-between gap-3">
                                    <span className="body-text font-bold text-slate-900">{library.label}</span>
                                    <span className="small-text font-bold text-slate-500">{library.count}</span>
                                </div>
                                <div className="small-text text-slate-500 mt-1">{library.complete} complete, {library.seen}/{library.total} entries</div>
                            </button>
                        ))}
                    </aside>

                    <section className="p-4 min-w-0">
                        <div className="flex items-end justify-between gap-3 mb-3">
                            <div>
                                <h2 className="section-title font-bold text-slate-900">Completion Sets</h2>
                                <div className="small-text text-slate-500">Finite award collections with missing-entry lists and badge-style completion.</div>
                            </div>
                            <div className="small-text text-slate-500">{filteredSets.length} sets</div>
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                            {filteredSets.map(awardSet => (
                                <AwardSetCard
                                    key={awardSet.id}
                                    awardSet={awardSet}
                                    selected={selectedSet?.id === awardSet.id}
                                    onSelect={selectSet}
                                    onOpen={openSet}
                                />
                            ))}
                        </div>
                    </section>

                    <aside className="border-l border-slate-200 bg-slate-50 p-4">
                        <AwardSetDetailPanel
                            awardSet={selectedSet}
                            selectedMember={selectedMember}
                            onSelectMember={setSelectedMember}
                            onOpen={openSet}
                        />
                    </aside>
                </div>
            </div>
        </div>
    );
};

const AwardWinnerDetail = ({ item, seen, playerGames, pitcherGames, gamesById }) => {
    if (!item || !seen) return null;
    const hittingGames = (playerGames || []).filter(game => game.playerId === item.playerId);
    const pitchingGames = (pitcherGames || []).filter(game => game.playerId === item.playerId);
    const attendedGames = (seen.gameIds || []).map(gameId => gamesById[gameId] || { gameId }).filter(Boolean);

    const hitting = seen.hitting;
    const pitching = seen.pitching;
    const contextLabel = item.team ? 'Award Team' : item.gameLabel ? 'All-Star Game' : 'League';
    const contextValue = item.team || item.gameLabel || item.league || '';

    return (
        <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-5" style={{ boxShadow: 'var(--shadow)' }}>
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h3 className="section-title font-semibold text-slate-900">
                        <PlayerLink playerId={item.playerId} name={item.name} />
                    </h3>
                    <div className="small-text text-slate-500 mt-1">{formatAwardEntryFullLabel(item)}</div>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-bold text-slate-900">{seen.gamesSeen}</div>
                    <div className="small-text text-slate-500">games seen</div>
                </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div>
                    <div className="small-text text-slate-500">First Seen</div>
                    <div className="body-text font-semibold text-slate-800">{seen.firstDate || ''}</div>
                </div>
                <div>
                    <div className="small-text text-slate-500">Last Seen</div>
                    <div className="body-text font-semibold text-slate-800">{seen.lastDate || ''}</div>
                </div>
                <div>
                    <div className="small-text text-slate-500">Teams Seen</div>
                    <div className="body-text font-semibold text-slate-800">{[hitting?.team, pitching?.team, seen.noStats?.teams].filter(Boolean).join(', ')}</div>
                </div>
                <div>
                    <div className="small-text text-slate-500">{contextLabel}</div>
                    <div className="body-text font-semibold text-slate-800">{contextValue}</div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <AwardStatsBlock
                    title="Batting When Seen"
                    stats={hitting}
                    fields={[
                        ['games', 'G'], ['pa', 'PA'], ['ab', 'AB'], ['h', 'H'], ['avg', 'AVG'],
                        ['obp', 'OBP'], ['slg', 'SLG'], ['ops', 'OPS'], ['hr', 'HR'], ['rbi', 'RBI'],
                        ['r', 'R'], ['sb', 'SB'], ['bb', 'BB'], ['so', 'SO'],
                    ]}
                />
                <AwardStatsBlock
                    title="Pitching When Seen"
                    stats={pitching}
                    fields={[
                        ['games', 'G'], ['gameStarts', 'GS'], ['ip', 'IP'], ['era', 'ERA'], ['whip', 'WHIP'],
                        ['wins', 'W'], ['losses', 'L'], ['saves', 'SV'], ['h', 'H'], ['er', 'ER'],
                        ['bb', 'BB'], ['so', 'SO'], ['hr', 'HR'],
                    ]}
                />
            </div>

            <AwardMiniTable
                title="Games Seen"
                rows={attendedGames}
                columns={[
                    { key: 'date', label: 'Date' },
                    { key: 'gameId', label: 'Game', render: value => <GameLink gameId={value} /> },
                    { key: 'awayTeam', label: 'Away' },
                    { key: 'homeTeam', label: 'Home' },
                    { key: 'score', label: 'Score' },
                    { key: 'venue', label: 'Venue' },
                ]}
            />

            {hittingGames.length > 0 && (
                <AwardMiniTable
                    title="Batting Lines"
                    rows={hittingGames}
                    columns={[
                        { key: 'date', label: 'Date' },
                        { key: 'gameId', label: 'Game', render: value => <GameLink gameId={value} /> },
                        { key: 'team', label: 'Tm' },
                        { key: 'opponent', label: 'Opp' },
                        { key: 'ab', label: 'AB' },
                        { key: 'h', label: 'H' },
                        { key: 'hr', label: 'HR' },
                        { key: 'rbi', label: 'RBI' },
                        { key: 'bb', label: 'BB' },
                        { key: 'so', label: 'SO' },
                    ]}
                />
            )}

            {pitchingGames.length > 0 && (
                <AwardMiniTable
                    title="Pitching Lines"
                    rows={pitchingGames}
                    columns={[
                        { key: 'date', label: 'Date' },
                        { key: 'gameId', label: 'Game', render: value => <GameLink gameId={value} /> },
                        { key: 'team', label: 'Tm' },
                        { key: 'opponent', label: 'Opp' },
                        { key: 'outs', label: 'IP', render: value => `${Math.floor((value || 0) / 3)}.${(value || 0) % 3}` },
                        { key: 'h', label: 'H' },
                        { key: 'er', label: 'ER' },
                        { key: 'bb', label: 'BB' },
                        { key: 'so', label: 'SO' },
                        { key: 'hr', label: 'HR' },
                    ]}
                />
            )}
        </div>
    );
};

const AwardStatsBlock = ({ title, stats, fields }) => (
    <div className="border border-slate-200 rounded-lg p-4">
        <h4 className="subsection-title font-semibold text-slate-800 mb-3">{title}</h4>
        {stats ? (
            <div className="grid grid-cols-3 gap-3">
                {fields.map(([key, label]) => (
                    <div key={key}>
                        <div className="small-text text-slate-500">{label}</div>
                        <div className="body-text font-semibold text-slate-900">{stats[key] ?? ''}</div>
                    </div>
                ))}
            </div>
        ) : (
            <div className="body-text text-slate-400">No line</div>
        )}
    </div>
);

const AwardMiniTable = ({ title, rows, columns }) => {
    if (!rows.length) return null;
    return (
        <div>
            <h4 className="subsection-title font-semibold text-slate-800 mb-2">{title}</h4>
            <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full min-w-full">
                    <thead className="bg-slate-50">
                        <tr>
                            {columns.map(col => (
                                <th key={col.key} className="px-3 py-2 text-left small-text font-medium text-slate-500 uppercase">{col.label}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {rows.map((row, idx) => (
                            <tr key={row.gameId || `${title}-${idx}`} className={idx % 2 === 1 ? 'bg-slate-50/50' : ''}>
                                {columns.map(col => (
                                    <td key={col.key} className="px-3 py-2 body-text text-slate-700">
                                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
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
        ...((data.awardChecklists?.groups || []).length > 0 ? [{ id: 'awards', label: 'Awards' }] : []),
        ...((data.allStarChecklists?.groups || []).length > 0 ? [{ id: 'allstars', label: 'All-Stars' }] : []),
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
            {view === 'awards' && <AwardChecklistsView awardChecklists={data.awardChecklists || {}} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} games={data.games || []} />}
            {view === 'allstars' && <AwardChecklistsView awardChecklists={data.allStarChecklists || {}} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} games={data.games || []} />}
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
            {view === 'milestones' && ((data.milestones?.length || data.allMilestones?.length) ? <MilestonesView milestones={data.milestones || []} allMilestones={data.allMilestones || data.milestones || []} games={data.games || []} careerFirsts={data.careerFirsts || []} careerLasts={data.careerLasts || []} allTimePassings={data.allTimePassings || []} onTabChange={onTabChange} /> : <EmptyState icon="🏆" title="No Milestones" message="No milestones have been recorded yet." />)}
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
            {view === 'badges' && <BadgesDisplay games={data.games || []} playerGames={data.playerGames || []} pitcherGames={data.pitcherGames || []} careerFirstsByGame={data.careerFirstsByGame || {}} debuts={data.debuts || []} finalGames={data.finalGames || []} />}
            {view === 'matchups' && (data.matchupMatrix ? <MatchupMatrix matchupData={data.matchupMatrix} games={data.games || []} /> : <EmptyState icon="🎯" title="No Matchup Data" message="No matchup data available." />)}
        </div>
    );
};

'''
