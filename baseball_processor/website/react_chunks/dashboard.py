"""React app chunk: dashboard."""

CODE = r'''const BadgeCell = ({ badges, badgeColors, onBadgeClick }) => {
    const anchorRef = useRef(null);
    const [open, setOpen] = useState(false);
    const [pos, setPos] = useState({ top: 0, left: 0 });
    const closeTimer = useRef(null);
    const handleBadgeClick = (badge) => (e) => {
        if (!onBadgeClick) return;
        e.stopPropagation();
        setOpen(false);
        onBadgeClick(badge);
    };

    const updatePos = () => {
        const el = anchorRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        setPos({ top: r.bottom + 4, left: r.left });
    };
    const openPopup = () => {
        if (closeTimer.current) { clearTimeout(closeTimer.current); closeTimer.current = null; }
        updatePos();
        setOpen(true);
    };
    const closePopupSoon = () => {
        if (closeTimer.current) clearTimeout(closeTimer.current);
        closeTimer.current = setTimeout(() => setOpen(false), 80);
    };
    useEffect(() => {
        if (!open) return;
        const onScroll = () => setOpen(false);
        window.addEventListener('scroll', onScroll, true);
        window.addEventListener('resize', onScroll);
        return () => {
            window.removeEventListener('scroll', onScroll, true);
            window.removeEventListener('resize', onScroll);
        };
    }, [open]);

    if (!badges || badges.length === 0) return null;
    const MAX_INLINE = 3;
    const hasOverflow = badges.length > MAX_INLINE;
    return (
        <div
            ref={anchorRef}
            className="relative flex flex-wrap gap-1 min-w-[16rem] max-w-[26rem]"
            onMouseEnter={hasOverflow ? openPopup : undefined}
            onMouseLeave={hasOverflow ? closePopupSoon : undefined}
        >
            {badges.slice(0, MAX_INLINE).map((badge, i) => (
                <span
                    key={`${badge.type}-${badge.text}-${i}`}
                    className={`inline-block max-w-[13rem] overflow-hidden text-ellipsis align-bottom px-1.5 py-0.5 rounded text-xs whitespace-nowrap ${onBadgeClick ? 'cursor-pointer hover:ring-1 hover:ring-blue-300' : ''} ${badgeColors[badge.type] || 'bg-slate-100 text-slate-700'}`}
                    title={badge.title}
                    onClick={onBadgeClick ? handleBadgeClick(badge) : undefined}
                >
                    {badge.text}
                </span>
            ))}
            {hasOverflow && (
                <span className="px-1.5 py-0.5 rounded text-xs bg-slate-200 text-slate-600">
                    +{badges.length - MAX_INLINE}
                </span>
            )}
            {hasOverflow && open && ReactDOM.createPortal(
                <div
                    className="fixed z-50 bg-white rounded-lg shadow-lg border p-2 max-w-lg"
                    style={{ top: pos.top, left: pos.left }}
                    onMouseEnter={openPopup}
                    onMouseLeave={closePopupSoon}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="flex flex-wrap gap-1">
                        {badges.map((badge, i) => (
                            <span key={`full-${badge.type}-${badge.text}-${i}`}
                                  className={`px-1.5 py-0.5 rounded text-xs whitespace-normal ${onBadgeClick ? 'cursor-pointer hover:ring-1 hover:ring-blue-300' : ''} ${badgeColors[badge.type] || 'bg-slate-100 text-slate-700'}`}
                                  title={badge.title}
                                  onClick={onBadgeClick ? handleBadgeClick(badge) : undefined}>
                                {badge.text}
                            </span>
                        ))}
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
};

// ---------------------------------------------------------------------------
// Badge Detail Modal
// ---------------------------------------------------------------------------
// Generic frame: header (badge text + game line), body (per-type sub-component
// or fallback "previous occurrence" generic detail), footer (close + go-to-game).
// All data lookups are recomputed on demand from playerGames/pitcherGames since
// badges only carry primitive metadata.

const HIT_KEY_MAP = { H: 'h', HR: 'hr', RBI: 'rbi', R: 'r', '2B': 'doubles', '3B': 'triples', SB: 'sb', BB: 'bb', SO: 'so' };
const PIT_KEY_MAP = { K: 'so', W: 'wins', SV: 'saves', G: 'games', GS: 'gameStarts' };
const RANK_LABEL = { G: 'Games', H: 'Hits', HR: 'HRs', RBI: 'RBI', R: 'Runs', '2B': 'Doubles', '3B': 'Triples', SB: 'Steals', BB: 'Walks', TB: 'Total Bases', K: 'Strikeouts', W: 'Wins', SV: 'Saves', IP: 'Innings Pitched', GS: 'Starts' };

// Build per-player cumulative totals for a given stat across all (regular-
// season) games up to and including upToGameId. Used by the player-rank and
// cumulative-stat detail views to recreate snapshots-in-time.
const buildPlayerLeaderboard = (games, playerGames, pitcherGames, stat, kind, upToGameId) => {
    const sortable = (s) => {
        if (!s) return '';
        if (s.includes('/')) {
            const [m, d, y] = s.split('/');
            return `${y.padStart(4, '0')}${m.padStart(2, '0')}${d.padStart(2, '0')}`;
        }
        return s;
    };
    const eligibleIds = new Set();
    let cutoff = null;
    if (upToGameId) {
        const target = (games || []).find(g => g.gameId === upToGameId);
        cutoff = target ? sortable(target.date) : null;
    }
    (games || []).forEach(g => {
        if (g.gameType === 'spring' || g.gameType === 'postseason') return;
        if (cutoff && sortable(g.date) > cutoff) return;
        eligibleIds.add(g.gameId);
    });
    const totals = {};
    const ensure = (pid, name) => {
        if (!totals[pid]) totals[pid] = { playerId: pid, name: name || pid, value: 0, games: 0 };
        else if (name && !totals[pid].name) totals[pid].name = name;
        return totals[pid];
    };
    const gamesPerPlayer = {};
    if (kind === 'g') {
        // Combined games attended (hitter or pitcher line in same game = 1)
        const seen = {};
        (playerGames || []).forEach(pg => {
            if (!eligibleIds.has(pg.gameId)) return;
            const k = `${pg.playerId}|${pg.gameId}`;
            if (seen[k]) return;
            seen[k] = true;
            const t = ensure(pg.playerId, pg.name);
            t.value += 1;
            t.games += 1;
        });
        (pitcherGames || []).forEach(pg => {
            if (!eligibleIds.has(pg.gameId)) return;
            const k = `${pg.playerId}|${pg.gameId}`;
            if (seen[k]) return;
            seen[k] = true;
            const t = ensure(pg.playerId, pg.name);
            t.value += 1;
            t.games += 1;
        });
    } else if (kind === 'hit') {
        const key = HIT_KEY_MAP[stat];
        // TB is computed (singles + 2*2B + 3*3B + 4*HR), no direct key.
        if (stat === 'TB') {
            (playerGames || []).forEach(pg => {
                if (!eligibleIds.has(pg.gameId)) return;
                const h = pg.h || 0, d = pg.doubles || 0, t3 = pg.triples || 0, hr = pg.hr || 0;
                const tb = (h - d - t3 - hr) + 2*d + 3*t3 + 4*hr;
                const t = ensure(pg.playerId, pg.name);
                t.value += tb;
                t.games += 1;
            });
        } else {
            if (!key) return [];
            (playerGames || []).forEach(pg => {
                if (!eligibleIds.has(pg.gameId)) return;
                const t = ensure(pg.playerId, pg.name);
                t.value += (pg[key] || 0);
                t.games += 1;
            });
        }
    } else if (kind === 'pit') {
        const key = PIT_KEY_MAP[stat];
        // IP is derived from outs/3 (float).
        if (stat === 'IP') {
            (pitcherGames || []).forEach(pg => {
                if (!eligibleIds.has(pg.gameId)) return;
                const t = ensure(pg.playerId, pg.name);
                t.value += (pg.outs || 0) / 3;
                t.games += 1;
            });
        } else {
            if (!key) return [];
            (pitcherGames || []).forEach(pg => {
                if (!eligibleIds.has(pg.gameId)) return;
                const t = ensure(pg.playerId, pg.name);
                t.value += (pg[key] || 0);
                t.games += 1;
            });
        }
    }
    return Object.values(totals)
        .filter(p => p.value > 0)
        .sort((a, b) => b.value - a.value || (a.name || '').localeCompare(b.name || ''));
};

const PlayerRankDetail = ({ badge, game, games, playerGames, pitcherGames }) => {
    const meta = badge.meta || {};
    const board = useMemo(
        () => buildPlayerLeaderboard(games, playerGames, pitcherGames, meta.stat, meta.kind, game?.gameId).slice(0, 10),
        [games, playerGames, pitcherGames, meta.stat, meta.kind, game?.gameId]
    );
    const label = meta.label || RANK_LABEL[meta.stat] || meta.stat;
    const playerIdx = board.findIndex(p => p.playerId === meta.playerId);
    const passed = (meta.prevRank && meta.rank < meta.prevRank)
        ? board.slice(meta.rank, Math.min(meta.prevRank, board.length))
        : [];

    return (
        <div className="space-y-4">
            <div className="flex items-baseline gap-3">
                <div className="text-sm text-slate-600">Rank change:</div>
                <div className="font-mono">
                    {meta.prevRank ? `#${meta.prevRank}` : '—'} → <span className="font-bold text-rose-700">#{meta.rank}</span>
                </div>
                <div className="text-sm text-slate-500">in {label.toLowerCase()}</div>
            </div>
            {passed.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm">
                    <div className="font-semibold text-amber-900 mb-1">Just passed:</div>
                    {passed.map(p => (
                        <div key={p.playerId} className="text-amber-800">{p.name} ({p.value})</div>
                    ))}
                </div>
            )}
            <div>
                <div className="text-sm font-semibold text-slate-700 mb-2">Top 10 in {label.toLowerCase()} you've witnessed (through this game):</div>
                <div className="border rounded divide-y">
                    {board.map((p, i) => (
                        <div key={p.playerId}
                             className={`flex items-center justify-between px-3 py-1.5 ${p.playerId === meta.playerId ? 'bg-rose-50 font-semibold' : 'bg-white'}`}>
                            <div className="flex items-center gap-3">
                                <span className="text-sm font-mono text-slate-500 w-6">#{i + 1}</span>
                                <span className="text-sm">{p.name}</span>
                            </div>
                            <div className="text-sm font-mono">{p.value.toLocaleString()}</div>
                        </div>
                    ))}
                    {board.length === 0 && <div className="px-3 py-2 text-sm text-slate-500">No data.</div>}
                </div>
                {playerIdx >= 0 && playerIdx < board.length - 1 && (
                    <div className="text-xs text-slate-500 mt-2">
                        Gap to #{playerIdx + 2}: {(board[playerIdx].value - board[playerIdx + 1].value).toLocaleString()}
                    </div>
                )}
            </div>
        </div>
    );
};

const CareerFirstDetail = ({ badge, game, games, careerFirstsByGame }) => {
    const meta = badge.meta || {};
    const playerName = meta.playerName;
    const playerId = meta.playerId;
    // Scan all career firsts to find every milestone for this player you've witnessed
    const all = useMemo(() => {
        const rows = [];
        Object.entries(careerFirstsByGame || {}).forEach(([gid, firsts]) => {
            (firsts || []).forEach(f => {
                if (playerId && f.player_id === playerId) {
                    rows.push({ ...f, gameId: gid });
                } else if (!playerId && f.player_name === playerName) {
                    rows.push({ ...f, gameId: gid });
                }
            });
        });
        const gameDate = (gid) => {
            const g = (games || []).find(gg => gg.gameId === gid);
            return g ? g.date : '';
        };
        rows.sort((a, b) => toSortableDate(gameDate(a.gameId)).localeCompare(toSortableDate(gameDate(b.gameId))));
        return rows.map(r => ({ ...r, displayDate: gameDate(r.gameId) }));
    }, [careerFirstsByGame, playerId, playerName, games]);
    const brefUrl = playerId ? `https://www.baseball-reference.com/players/${playerId.charAt(0)}/${playerId}.shtml` : null;
    return (
        <div className="space-y-4">
            <div className="bg-amber-50 border border-amber-200 rounded p-3">
                <div className="text-sm font-semibold text-amber-900">{playerName}</div>
                <div className="text-sm text-amber-800 mt-1">{meta.milestone}{meta.careerTotalAfter ? ` (career total: ${meta.careerTotalAfter})` : ''}</div>
                {brefUrl && (
                    <a href={brefUrl} target="_blank" rel="noopener noreferrer"
                       className="inline-block mt-2 text-xs text-blue-600 hover:underline">
                        View on Baseball-Reference →
                    </a>
                )}
            </div>
            <div>
                <div className="text-sm font-semibold text-slate-700 mb-2">
                    All milestones for {playerName} you've witnessed ({all.length}):
                </div>
                <div className="border rounded divide-y max-h-72 overflow-y-auto">
                    {all.map((r, i) => (
                        <div key={i} className={`flex items-center justify-between px-3 py-1.5 text-sm ${r.gameId === game?.gameId ? 'bg-amber-50 font-semibold' : 'bg-white'}`}>
                            <span>{r.milestone}</span>
                            <span className="text-slate-500 font-mono text-xs">{r.displayDate}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const CumulativeStatDetail = ({ badge, game, games, playerGames, pitcherGames }) => {
    const meta = badge.meta || {};
    const stat = meta.stat || '';
    const value = meta.value || 0;
    const isPitchingK = stat === 'K_pit';
    const baseStat = isPitchingK ? 'K' : stat;
    // Top contributors to this stat in your dataset (all-time, regular season only)
    const contributors = useMemo(() => {
        if (isPitchingK) {
            return buildPlayerLeaderboard(games, playerGames, pitcherGames, 'K', 'pit', null).slice(0, 10);
        }
        return buildPlayerLeaderboard(games, playerGames, pitcherGames, baseStat, 'hit', null).slice(0, 10);
    }, [games, playerGames, pitcherGames, baseStat, isPitchingK]);

    // Compute totals through this game and rate per game (regular season only)
    const through = useMemo(() => {
        const sortable = (s) => s && s.includes('/') ? (() => { const [m, d, y] = s.split('/'); return `${y}${m.padStart(2,'0')}${d.padStart(2,'0')}`; })() : s;
        const cutoff = game ? sortable(game.date) : null;
        let total = 0;
        let gameCount = 0;
        const eligible = new Set();
        (games || []).forEach(g => {
            if (g.gameType === 'spring' || g.gameType === 'postseason') return;
            if (cutoff && sortable(g.date) > cutoff) return;
            eligible.add(g.gameId);
            gameCount++;
        });
        if (isPitchingK) {
            (pitcherGames || []).forEach(pg => { if (eligible.has(pg.gameId)) total += (pg.so || 0); });
        } else {
            const key = HIT_KEY_MAP[baseStat];
            if (key) (playerGames || []).forEach(pg => { if (eligible.has(pg.gameId)) total += (pg[key] || 0); });
        }
        return { total, gameCount };
    }, [games, playerGames, pitcherGames, baseStat, isPitchingK, game]);

    const label = isPitchingK ? 'pitching strikeouts' : (RANK_LABEL[baseStat] || baseStat).toLowerCase();
    return (
        <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
                <div className="bg-teal-50 border border-teal-200 rounded p-3 text-center">
                    <div className="text-xs text-teal-700 uppercase tracking-wide">Milestone</div>
                    <div className="text-2xl font-bold text-teal-900">{value.toLocaleString()}</div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded p-3 text-center">
                    <div className="text-xs text-slate-600 uppercase tracking-wide">Through this game</div>
                    <div className="text-2xl font-bold text-slate-800">{through.total.toLocaleString()}</div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded p-3 text-center">
                    <div className="text-xs text-slate-600 uppercase tracking-wide">Per game</div>
                    <div className="text-2xl font-bold text-slate-800">
                        {through.gameCount > 0 ? (through.total / through.gameCount).toFixed(2) : '—'}
                    </div>
                </div>
            </div>
            <div>
                <div className="text-sm font-semibold text-slate-700 mb-2">Top contributors to {label}:</div>
                <div className="border rounded divide-y">
                    {contributors.map((p, i) => (
                        <div key={p.playerId} className="flex items-center justify-between px-3 py-1.5 bg-white">
                            <div className="flex items-center gap-3">
                                <span className="text-sm font-mono text-slate-500 w-6">#{i + 1}</span>
                                <span className="text-sm">{p.name}</span>
                            </div>
                            <div className="text-sm font-mono">{p.value.toLocaleString()}</div>
                        </div>
                    ))}
                    {contributors.length === 0 && <div className="px-3 py-2 text-sm text-slate-500">No data.</div>}
                </div>
            </div>
        </div>
    );
};

const PlayerStatDetail = ({ badge, game, games, allBadgesByGame }) => {
    const meta = badge.meta || {};
    const playerId = meta.playerId;
    const stat = meta.stat;
    // Find every player-stat crossing for this player + stat
    const crossings = useMemo(() => {
        const sortable = (s) => s && s.includes('/') ? (() => { const [m, d, y] = s.split('/'); return `${y}${m.padStart(2,'0')}${d.padStart(2,'0')}`; })() : s;
        const rows = [];
        Object.entries(allBadgesByGame || {}).forEach(([gid, list]) => {
            (list || []).forEach(b => {
                if (b.type !== 'player-stat') return;
                const m = b.meta || {};
                if (m.playerId !== playerId || m.stat !== stat) return;
                const g = (games || []).find(gg => gg.gameId === gid);
                rows.push({ gameId: gid, value: m.value, date: g ? g.date : '', away: g ? g.awayTeam : '', home: g ? g.homeTeam : '', venue: g ? g.venue : '' });
            });
        });
        rows.sort((a, b) => sortable(a.date).localeCompare(sortable(b.date)));
        return rows;
    }, [allBadgesByGame, playerId, stat, games]);

    const idx = crossings.findIndex(c => c.gameId === game?.gameId);
    const prior = idx > 0 ? crossings[idx - 1] : null;
    const next = idx >= 0 && idx < crossings.length - 1 ? crossings[idx + 1] : null;
    const statLabel = meta.kind === 'g' ? 'games attended' :
        (meta.kind === 'hit' ? (RANK_LABEL[stat] || stat) : (RANK_LABEL[stat] || stat));

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
                <div className="bg-sky-50 border border-sky-200 rounded p-3 text-center">
                    <div className="text-xs text-sky-700 uppercase tracking-wide">This milestone</div>
                    <div className="text-2xl font-bold text-sky-900">{ordinal(meta.value || 0)}</div>
                    <div className="text-xs text-sky-700">{statLabel}</div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded p-3 text-center">
                    <div className="text-xs text-slate-600 uppercase tracking-wide">Previous</div>
                    <div className="text-lg font-semibold text-slate-800">{prior ? ordinal(prior.value) : '—'}</div>
                    <div className="text-xs text-slate-500">{prior ? prior.date : 'first crossing'}</div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded p-3 text-center">
                    <div className="text-xs text-slate-600 uppercase tracking-wide">Next so far</div>
                    <div className="text-lg font-semibold text-slate-800">{next ? ordinal(next.value) : '—'}</div>
                    <div className="text-xs text-slate-500">{next ? next.date : 'no later milestone yet'}</div>
                </div>
            </div>
            <div>
                <div className="text-sm font-semibold text-slate-700 mb-2">
                    All {statLabel} milestones for {meta.playerName} with you ({crossings.length}):
                </div>
                <div className="border rounded divide-y max-h-72 overflow-y-auto">
                    {crossings.map((c, i) => (
                        <div key={c.gameId} className={`flex items-center justify-between px-3 py-1.5 text-sm ${c.gameId === game?.gameId ? 'bg-sky-50 font-semibold' : 'bg-white'}`}>
                            <span>{ordinal(c.value)} {meta.kind === 'g' ? 'game' : (RANK_LABEL[stat] || stat)}</span>
                            <span className="text-slate-500 font-mono text-xs">{c.date} • {c.away} @ {c.home}</span>
                        </div>
                    ))}
                    {crossings.length === 0 && <div className="px-3 py-2 text-sm text-slate-500">No data.</div>}
                </div>
            </div>
        </div>
    );
};

const GenericBadgeDetail = ({ badge, game, games, allBadgesByGame }) => {
    // Find the previous game (chronologically) where this badge type appeared
    const prior = useMemo(() => {
        if (!game || !games || !allBadgesByGame) return null;
        const sortable = (s) => s && s.includes('/') ? (() => { const [m, d, y] = s.split('/'); return `${y}${m.padStart(2,'0')}${d.padStart(2,'0')}`; })() : s;
        const cutoff = sortable(game.date);
        const earlier = (games || [])
            .filter(g => g.gameId !== game.gameId && sortable(g.date) <= cutoff)
            .sort((a, b) => sortable(b.date).localeCompare(sortable(a.date)));
        for (const g of earlier) {
            const list = allBadgesByGame[g.gameId] || [];
            const match = list.find(b => b.type === badge.type);
            if (match) return { game: g, badge: match };
        }
        return null;
    }, [badge, game, games, allBadgesByGame]);
    return (
        <div className="space-y-3 text-sm">
            {prior ? (
                <div className="border rounded p-3 bg-slate-50">
                    <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Previous {badge.type.replace(/-/g, ' ')}</div>
                    <div className="font-medium">{prior.badge.text}</div>
                    <div className="text-xs text-slate-500">{prior.game.date} • {prior.game.awayTeam} @ {prior.game.homeTeam} • {prior.game.venue}</div>
                </div>
            ) : (
                <div className="text-slate-500">No prior occurrence of this badge type.</div>
            )}
        </div>
    );
};

const BadgeDetailModal = ({ badge, game, games, playerGames, pitcherGames, careerFirstsByGame, allBadgesByGame, onClose, onGoToGame }) => {
    if (!badge) return null;
    let body = null;
    if (badge.type === 'player-rank') {
        body = <PlayerRankDetail badge={badge} game={game} games={games} playerGames={playerGames} pitcherGames={pitcherGames} />;
    } else if (badge.type === 'career-first') {
        body = <CareerFirstDetail badge={badge} game={game} games={games} careerFirstsByGame={careerFirstsByGame} />;
    } else if (badge.type === 'cumulative-stat') {
        body = <CumulativeStatDetail badge={badge} game={game} games={games} playerGames={playerGames} pitcherGames={pitcherGames} />;
    } else if (badge.type === 'player-stat') {
        body = <PlayerStatDetail badge={badge} game={game} games={games} allBadgesByGame={allBadgesByGame} />;
    } else {
        body = <GenericBadgeDetail badge={badge} game={game} games={games} allBadgesByGame={allBadgesByGame} />;
    }
    return (
        <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
                <div className="p-5 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                    <div className="text-xs uppercase tracking-wide text-blue-100">{(badge.type || '').replace(/-/g, ' ')}</div>
                    <h3 className="text-lg font-bold mt-1">{badge.text}</h3>
                    <p className="text-sm text-blue-100 mt-1">{badge.title}</p>
                    {game && (
                        <div className="mt-2 text-xs text-blue-100">
                            {game.date} • {game.awayTeam} @ {game.homeTeam}{game.score ? ` (${game.score})` : ''} • {game.venue}
                        </div>
                    )}
                </div>
                <div className="flex-1 overflow-y-auto p-5">
                    {body}
                </div>
                <div className="p-3 border-t bg-slate-50 flex gap-2 justify-end">
                    {onGoToGame && game && (
                        <button onClick={() => { onClose(); onGoToGame(); }}
                                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm font-semibold">Go to game</button>
                    )}
                    <button onClick={onClose}
                            className="px-4 py-2 bg-slate-200 rounded hover:bg-slate-300 text-sm font-semibold">Close</button>
                </div>
            </div>
        </div>
    );
};

const computeCumulativeStatBadges = (games, playerGames, pitcherGames) => {
    const badges = {};
    const STAT_MILESTONES = [100, 250, 500, 750, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 7500, 10000];

    const pgByGame = {};
    (playerGames || []).forEach(pg => {
        const gid = pg.gameId;
        if (!pgByGame[gid]) pgByGame[gid] = [];
        pgByGame[gid].push(pg);
    });
    const pitByGame = {};
    (pitcherGames || []).forEach(pg => {
        const gid = pg.gameId;
        if (!pitByGame[gid]) pitByGame[gid] = [];
        pitByGame[gid].push(pg);
    });

    const parseDate = toSortableDate;
    const springGameIds = new Set((games || []).filter(g => g.gameType === 'spring').map(g => g.gameId));
    const postseasonGameIds = new Set((games || []).filter(g => g.gameType === 'postseason').map(g => g.gameId));
    const sorted = [...games].filter(g => !springGameIds.has(g.gameId)).sort((a, b) => parseDate(a.date).localeCompare(parseDate(b.date)));

    let totals = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
    let pitK = 0;
    let prevTotals = { ...totals };
    let prevPitK = 0;

    // Venue-specific tracking
    const VENUE_MILESTONES = [50, 100, 250, 500, 750, 1000];
    const venueTotals = {};  // venue -> { H, R, HR, ... }
    const venuePrev = {};    // venue -> prev totals snapshot

    // Per-player tracking (regular season only) — emits two badge types:
    //   player-stat: a player crosses a personal threshold with you in attendance
    //   player-rank: a player moves up in your personal top-5 for a stat
    // G (games attended) is a single combined counter per player so two-way
    // players (e.g. Nolan McClean) don't double-fire on hitter-G + pitcher-G.
    const playerInfo = {};   // pid -> { name, G, H, HR, RBI, R, '2B', '3B', SB, BB, TB, K, W, SV, IP, GS, hadHit, hadPit }
    const PLAYER_HIT_THRESHOLDS = {
        H:   [10, 25, 50, 100, 150, 200, 250, 300, 400, 500],
        HR:  [5, 10, 15, 20, 25, 30, 40, 50, 75, 100],
        RBI: [10, 25, 50, 75, 100, 150, 200, 250, 300],
        R:   [10, 25, 50, 75, 100, 150, 200, 250, 300],
        '2B':[5, 10, 15, 20, 25, 30, 40, 50, 75],
        '3B':[3, 5, 10, 15, 20, 25, 30],
        SB:  [5, 10, 15, 20, 25, 30, 40, 50],
        BB:  [10, 25, 50, 75, 100, 150, 200],
        TB:  [10, 25, 50, 100, 150, 200, 300, 400, 500, 750, 1000],
    };
    const PLAYER_PIT_THRESHOLDS = {
        K: [25, 50, 100, 150, 200, 300, 400, 500],
        W: [5, 10, 15, 20, 25, 30, 40, 50],
        SV:[5, 10, 15, 20, 25, 30, 40, 50],
        IP:[10, 25, 50, 100, 150, 200, 300],
        GS:[5, 10, 15, 20, 25, 30, 50],
    };
    const PLAYER_G_THRESHOLDS = [10, 25, 50, 75, 100, 150, 200, 250, 300, 400, 500];
    const HIT_LABELS_S = { H: 'Hit', HR: 'HR', RBI: 'RBI', R: 'Run', '2B': 'Double', '3B': 'Triple', SB: 'Steal', BB: 'Walk', TB: 'Total Base' };
    const PIT_LABELS_S = { K: 'K', W: 'Win', SV: 'Save', IP: 'IP', GS: 'Start' };
    const HIT_LABELS_P = { H: 'Hits', HR: 'HRs', RBI: 'RBI', R: 'Runs', '2B': 'Doubles', '3B': 'Triples', SB: 'Steals', BB: 'Walks', TB: 'Total Bases' };
    const PIT_LABELS_P = { K: 'Strikeouts', W: 'Wins', SV: 'Saves', IP: 'Innings Pitched', GS: 'Starts' };
    const HIT_RANK_STATS = ['H', 'HR', 'RBI', 'R', '2B', '3B', 'SB', 'BB', 'TB'];
    const PIT_RANK_STATS = ['K', 'W', 'SV', 'IP', 'GS'];
    const lastNameOf = (n) => {
        const parts = (n || '').trim().split(/\s+/);
        return parts.length > 1 ? parts[parts.length - 1] : (n || '');
    };
    const topNForStat = (info, stat, n, kind) => {
        // kind: 'hit' filters to players with hit appearances, 'pit' to pitchers, 'all' to anyone
        return Object.values(info)
            .filter(p => {
                if ((p[stat] || 0) <= 0) return false;
                if (kind === 'hit') return p.hadHit;
                if (kind === 'pit') return p.hadPit;
                return true;
            })
            .sort((a, b) => (b[stat] || 0) - (a[stat] || 0) || (a.name || '').localeCompare(b.name || ''))
            .slice(0, n)
            .map(p => p.playerId);
    };

    sorted.forEach(game => {
        const gid = game.gameId;
        if (!gid) return;
        badges[gid] = [];
        const rawVenue = game.venue || '';
        const matched = matchStadiumByName(rawVenue);
        const venue = matched ? matched.name : rawVenue;

        // Initialize venue tracking
        if (venue && !venueTotals[venue]) {
            venueTotals[venue] = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
            venuePrev[venue] = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
        }

        (pgByGame[gid] || []).forEach(pg => {
            totals.H += (pg.h || 0);
            totals.R += (pg.r || 0);
            totals.HR += (pg.hr || 0);
            totals.RBI += (pg.rbi || 0);
            totals.SO += (pg.so || 0);
            totals.BB += (pg.bb || 0);
            totals.SB += (pg.sb || 0);
            totals['2B'] += (pg.doubles || 0);
            totals['3B'] += (pg.triples || 0);
            if (venue) {
                venueTotals[venue].H += (pg.h || 0);
                venueTotals[venue].R += (pg.r || 0);
                venueTotals[venue].HR += (pg.hr || 0);
                venueTotals[venue].RBI += (pg.rbi || 0);
                venueTotals[venue].SO += (pg.so || 0);
                venueTotals[venue].BB += (pg.bb || 0);
                venueTotals[venue].SB += (pg.sb || 0);
                venueTotals[venue]['2B'] += (pg.doubles || 0);
                venueTotals[venue]['3B'] += (pg.triples || 0);
            }
        });
        let gameMaxVelo = 0;
        let gameMaxVeloPitcher = '';
        (pitByGame[gid] || []).forEach(pg => {
            pitK += (pg.so || 0);
            if (pg.maxSpeed && pg.maxSpeed > gameMaxVelo) {
                gameMaxVelo = pg.maxSpeed;
                gameMaxVeloPitcher = pg.name;
            }
        });

        const labels = { H: 'Hits', R: 'Runs', HR: 'HRs', RBI: 'RBI', SO: 'K', BB: 'Walks', SB: 'Steals', '2B': 'Doubles', '3B': 'Triples' };
        Object.entries(totals).forEach(([stat, val]) => {
            const prev = prevTotals[stat];
            STAT_MILESTONES.forEach(m => {
                if (val >= m && prev < m) {
                    badges[gid].push({
                        type: 'cumulative-stat',
                        text: `${m.toLocaleString()} ${labels[stat]} Witnessed`,
                        title: `You've now witnessed ${m.toLocaleString()} total ${labels[stat].toLowerCase()} across all games`,
                        meta: { stat, value: m, scope: 'global' }
                    });
                }
            });
        });
        STAT_MILESTONES.forEach(m => {
            if (pitK >= m && prevPitK < m) {
                badges[gid].push({
                    type: 'cumulative-stat',
                    text: `${m.toLocaleString()} K Witnessed`,
                    title: `You've now witnessed ${m.toLocaleString()} total strikeouts (pitching) across all games`,
                    meta: { stat: 'K_pit', value: m, scope: 'global' }
                });
            }
        });

        // Pitch velocity milestones
        if (gameMaxVelo >= 100) {
            badges[gid].push({
                type: 'pitch-velo',
                text: `${gameMaxVelo} mph - ${gameMaxVeloPitcher}`,
                title: `${gameMaxVeloPitcher} hit ${gameMaxVelo} mph`
            });
        }

        // Venue-specific milestones
        if (venue) {
            const shortVenue = venue.replace(/ Stadium| Park| Field| Coliseum| Centre| Arena/gi, '').trim();
            Object.entries(venueTotals[venue]).forEach(([stat, val]) => {
                const prev = venuePrev[venue][stat];
                VENUE_MILESTONES.forEach(m => {
                    if (val >= m && prev < m) {
                        badges[gid].push({
                            type: 'venue-stat',
                            text: `${m.toLocaleString()} ${labels[stat]} at ${shortVenue}`,
                            title: `You've witnessed ${m.toLocaleString()} ${labels[stat].toLowerCase()} at ${venue}`
                        });
                    }
                });
            });
            venuePrev[venue] = { ...venueTotals[venue] };
        }

        prevTotals = { ...totals };
        prevPitK = pitK;

        // Per-player threshold + top-5 rank movement (regular season only)
        if (!postseasonGameIds.has(gid)) {
            // Snapshot prev top-5s (for rank-movement check)
            const prevGTop5 = topNForStat(playerInfo, 'G', 5, 'all');
            const prevHitTop5 = {};
            HIT_RANK_STATS.forEach(s => { prevHitTop5[s] = topNForStat(playerInfo, s, 5, 'hit'); });
            const prevPitTop5 = {};
            PIT_RANK_STATS.forEach(s => { prevPitTop5[s] = topNForStat(playerInfo, s, 5, 'pit'); });

            // Snapshot per-touched-player previous values, then accumulate
            const touched = new Map();  // pid -> { prevG, prevHit{}, prevPit{}, isHit, isPit }
            const ensure = (pid, name) => {
                if (!playerInfo[pid]) {
                    playerInfo[pid] = {
                        playerId: pid, name: name || pid,
                        G: 0, H: 0, HR: 0, RBI: 0, R: 0, '2B': 0, '3B': 0, SB: 0, BB: 0, TB: 0,
                        K: 0, W: 0, SV: 0, IP: 0, GS: 0,
                        hadHit: false, hadPit: false,
                    };
                } else if (name && !playerInfo[pid].name) {
                    playerInfo[pid].name = name;
                }
                if (!touched.has(pid)) {
                    const cur = playerInfo[pid];
                    touched.set(pid, {
                        prevG: cur.G,
                        prev: { H: cur.H, HR: cur.HR, RBI: cur.RBI, R: cur.R, '2B': cur['2B'], '3B': cur['3B'], SB: cur.SB, BB: cur.BB, TB: cur.TB, K: cur.K, W: cur.W, SV: cur.SV, IP: cur.IP, GS: cur.GS },
                        isHit: false, isPit: false,
                    });
                }
                return touched.get(pid);
            };

            (pgByGame[gid] || []).forEach(pg => {
                const pid = pg.playerId;
                if (!pid) return;
                const t = ensure(pid, pg.name);
                t.isHit = true;
                playerInfo[pid].hadHit = true;
                playerInfo[pid].H   += (pg.h || 0);
                playerInfo[pid].HR  += (pg.hr || 0);
                playerInfo[pid].RBI += (pg.rbi || 0);
                playerInfo[pid].R   += (pg.r || 0);
                playerInfo[pid]['2B'] += (pg.doubles || 0);
                playerInfo[pid]['3B'] += (pg.triples || 0);
                playerInfo[pid].SB  += (pg.sb || 0);
                playerInfo[pid].BB  += (pg.bb || 0);
                {
                    const h = pg.h || 0, d = pg.doubles || 0, t3 = pg.triples || 0, hr = pg.hr || 0;
                    playerInfo[pid].TB += (h - d - t3 - hr) + 2*d + 3*t3 + 4*hr;
                }
            });
            (pitByGame[gid] || []).forEach(pg => {
                const pid = pg.playerId;
                if (!pid) return;
                const t = ensure(pid, pg.name);
                t.isPit = true;
                playerInfo[pid].hadPit = true;
                playerInfo[pid].K  += (pg.so || 0);
                playerInfo[pid].W  += (pg.wins || 0);
                playerInfo[pid].SV += (pg.saves || 0);
                playerInfo[pid].IP += (pg.outs || 0) / 3;
                playerInfo[pid].GS += (pg.gameStarts || 0);
            });
            // Single G increment per touched player (covers two-way players)
            touched.forEach((_t, pid) => { playerInfo[pid].G += 1; });

            // Threshold badges
            touched.forEach((t, pid) => {
                const cur = playerInfo[pid];
                const ln = lastNameOf(cur.name);

                // Combined Games threshold (one badge for two-way players)
                PLAYER_G_THRESHOLDS.forEach(m => {
                    if (cur.G >= m && t.prevG < m) {
                        badges[gid].push({
                            type: 'player-stat',
                            text: `${ln}: ${ordinal(m)} game with you`,
                            title: `${cur.name}'s ${ordinal(m)} game with you in attendance`,
                            meta: { playerId: pid, playerName: cur.name, stat: 'G', value: m, kind: 'g' }
                        });
                    }
                });
                // Hit thresholds (only for players who hit this game)
                if (t.isHit) {
                    Object.entries(PLAYER_HIT_THRESHOLDS).forEach(([stat, thresholds]) => {
                        thresholds.forEach(m => {
                            if ((cur[stat] || 0) >= m && (t.prev[stat] || 0) < m) {
                                badges[gid].push({
                                    type: 'player-stat',
                                    text: `${ln}: ${ordinal(m)} ${HIT_LABELS_S[stat]}`,
                                    title: `${cur.name}'s ${ordinal(m)} ${HIT_LABELS_S[stat]} with you in attendance`,
                                    meta: { playerId: pid, playerName: cur.name, stat, value: m, kind: 'hit' }
                                });
                            }
                        });
                    });
                }
                // Pitch thresholds (only for pitchers this game)
                if (t.isPit) {
                    Object.entries(PLAYER_PIT_THRESHOLDS).forEach(([stat, thresholds]) => {
                        thresholds.forEach(m => {
                            if ((cur[stat] || 0) >= m && (t.prev[stat] || 0) < m) {
                                badges[gid].push({
                                    type: 'player-stat',
                                    text: `${ln}: ${ordinal(m)} ${PIT_LABELS_S[stat]}`,
                                    title: `${cur.name}'s ${ordinal(m)} ${PIT_LABELS_S[stat]} with you in attendance`,
                                    meta: { playerId: pid, playerName: cur.name, stat, value: m, kind: 'pit' }
                                });
                            }
                        });
                    });
                }
            });

            // Top-5 rank movement (only for players who played this game)
            const emitRankBadge = (pid, stat, prevTop5, newTop5, label, kind) => {
                const newRank = newTop5.indexOf(pid);
                if (newRank === -1) return;
                const prevRank = prevTop5.indexOf(pid);
                if (prevRank !== -1 && newRank >= prevRank) return;  // didn't improve
                const cur = playerInfo[pid];
                const ln = lastNameOf(cur.name);
                const baseMeta = {
                    playerId: pid, playerName: cur.name, stat, value: cur[stat] || 0,
                    rank: newRank + 1, prevRank: prevRank === -1 ? null : prevRank + 1,
                    kind, label,
                };
                if (newRank === 0) {
                    badges[gid].push({
                        type: 'player-rank',
                        text: `${ln}: most ${label} you've seen`,
                        title: `${cur.name} now leads your top-5 in ${label} (${cur[stat]})`,
                        meta: baseMeta,
                    });
                } else if (prevRank === -1) {
                    badges[gid].push({
                        type: 'player-rank',
                        text: `${ln}: top-5 ${label} (#${newRank + 1})`,
                        title: `${cur.name} entered your top-5 ${label} list at #${newRank + 1} (${cur[stat]})`,
                        meta: baseMeta,
                    });
                } else {
                    badges[gid].push({
                        type: 'player-rank',
                        text: `${ln}: #${newRank + 1} ${label}`,
                        title: `${cur.name} climbed to #${newRank + 1} on your top-5 ${label} list (${cur[stat]})`,
                        meta: baseMeta,
                    });
                }
            };
            const newGTop5 = topNForStat(playerInfo, 'G', 5, 'all');
            touched.forEach((_t, pid) => emitRankBadge(pid, 'G', prevGTop5, newGTop5, 'Games', 'g'));
            HIT_RANK_STATS.forEach(stat => {
                const newTop5 = topNForStat(playerInfo, stat, 5, 'hit');
                touched.forEach((t, pid) => {
                    if (t.isHit) emitRankBadge(pid, stat, prevHitTop5[stat], newTop5, HIT_LABELS_P[stat], 'hit');
                });
            });
            PIT_RANK_STATS.forEach(stat => {
                const newTop5 = topNForStat(playerInfo, stat, 5, 'pit');
                touched.forEach((t, pid) => {
                    if (t.isPit) emitRankBadge(pid, stat, prevPitTop5[stat], newTop5, PIT_LABELS_P[stat], 'pit');
                });
            });
        }
    });

    return badges;
};

const GameLogWithDetails = ({ games, playerGames, pitcherGames, careerFirstsByGame, allTimePassingsByGame }) => {
    const [selectedGame, setSelectedGame] = useState(null);
    const [selectedBadge, setSelectedBadge] = useState(null);  // { badge, gameId }
    const [badgeTypeFilter, setBadgeTypeFilter] = useState('all');
    const [badgeTextFilter, setBadgeTextFilter] = useState('');

    // Check for pending game selection (from player timeline click)
    useEffect(() => {
        if (window._pendingGameId) {
            const gameId = window._pendingGameId;
            window._pendingGameId = null;
            const game = (games || []).find(g => g.gameId === gameId);
            if (game) setSelectedGame(game);
        }
    });


    // Compute milestones for badge display
    const milestoneData = useMemo(() => computeGameMilestones(games), [games]);
    const gameMilestones = milestoneData.milestones || {};

    // Compute cumulative stat badges (total hits/runs/HRs witnessed)
    const cumulativeBadges = useMemo(() => computeCumulativeStatBadges(games, playerGames, pitcherGames), [games, playerGames, pitcherGames]);

    // Badge colors by type
    const badgeColors = {
        'game-count': 'bg-purple-100 text-purple-700',
        'team': 'bg-blue-100 text-blue-700',
        'venue': 'bg-green-100 text-green-700',
        'div-first': 'bg-orange-100 text-orange-700',
        'div-complete': 'bg-yellow-100 text-yellow-800 font-bold',
        'div-stadiums': 'bg-indigo-100 text-indigo-700 font-bold',
        'matchup': 'bg-slate-100 text-slate-700',
        'holiday': 'bg-red-100 text-red-700',
        'career-first': 'bg-amber-100 text-amber-800 font-bold',
        'cumulative-stat': 'bg-teal-100 text-teal-800 font-bold',
        'venue-stat': 'bg-purple-100 text-purple-800 font-bold',
        'pitch-velo': 'bg-red-100 text-red-700 font-bold',
        'player-stat': 'bg-sky-100 text-sky-800 font-bold',
        'player-rank': 'bg-rose-100 text-rose-800 font-bold'
    };

    const badgeTypeLabels = {
        'game-count': 'Game Count',
        'team': 'Team',
        'venue': 'Venue',
        'div-first': 'Division First',
        'div-complete': 'Division Complete',
        'div-stadiums': 'Division Stadiums',
        'matchup': 'Matchup',
        'holiday': 'Holiday',
        'career-first': 'Career First',
        'cumulative-stat': 'Cumulative Stat',
        'venue-stat': 'Venue Stat',
        'pitch-velo': '100+ mph',
        'player-stat': 'Player Milestone',
        'player-rank': 'Top-5 Movement'
    };

    // Drop "Career Pitching Game #N" when "Career Game #N" exists for the
    // same player on the same game — for pure pitchers (e.g. McClean, Povich)
    // these always coincide and emitting both is redundant.
    const dedupedCareerFirstsByGame = useMemo(() => {
        const result = {};
        Object.entries(careerFirstsByGame || {}).forEach(([gid, firsts]) => {
            const list = firsts || [];
            const haveBattingG = new Set();
            list.forEach(f => {
                const m = (f.milestone || '').match(/^Career Game #(\d+)$/);
                if (m) haveBattingG.add(`${f.player_name}|${m[1]}`);
            });
            result[gid] = list.filter(f => {
                const m = (f.milestone || '').match(/^Career Pitching Game #(\d+)$/);
                if (!m) return true;
                return !haveBattingG.has(`${f.player_name}|${m[1]}`);
            });
        });
        return result;
    }, [careerFirstsByGame]);

    // Precompute all badges per game for filtering
    const allBadgesByGame = useMemo(() => {
        const result = {};
        // shortenMilestone is now global
        // getLastName is now global
        games.forEach(game => {
            const gid = game.gameId;
            if (!gid) return;
            const regularBadges = gameMilestones[gid]?.badges || [];
            const gameCareerFirsts = dedupedCareerFirstsByGame[gid] || [];
            const careerFirstBadges = gameCareerFirsts.map(f => ({
                type: 'career-first',
                text: `⭐ ${getLastName(f.player_name)}: ${shortenMilestone(f.milestone)}`,
                title: `${f.player_name || 'Unknown'}'s ${f.milestone || 'milestone'}`,
                meta: {
                    playerId: f.player_id,
                    playerName: f.player_name,
                    milestone: f.milestone,
                    number: f.number,
                    careerTotalAfter: f.career_total_after,
                }
            }));
            result[gid] = [...regularBadges, ...careerFirstBadges, ...(cumulativeBadges[gid] || [])].filter(b => b.text && b.text.trim());
        });
        return result;
    }, [games, gameMilestones, dedupedCareerFirstsByGame, cumulativeBadges]);

    // Collect all badge types that actually appear
    const availableBadgeTypes = useMemo(() => {
        const types = new Set();
        Object.values(allBadgesByGame).forEach(badges => badges.forEach(b => types.add(b.type)));
        return [...types].sort();
    }, [allBadgesByGame]);

    // Filter games by badge criteria
    const badgeFilteredGames = useMemo(() => {
        if (badgeTypeFilter === 'all' && !badgeTextFilter) return games;
        if (badgeTypeFilter === 'any-badge') {
            return games.filter(g => (allBadgesByGame[g.gameId] || []).length > 0);
        }
        return games.filter(game => {
            const badges = allBadgesByGame[game.gameId] || [];
            if (badges.length === 0) return false;
            let matched = badges;
            if (badgeTypeFilter && badgeTypeFilter !== 'all') {
                matched = matched.filter(b => b.type === badgeTypeFilter);
            }
            if (badgeTextFilter) {
                const q = badgeTextFilter.toLowerCase();
                matched = matched.filter(b => (b.text || '').toLowerCase().includes(q) || (b.title || '').toLowerCase().includes(q));
            }
            return matched.length > 0;
        });
    }, [games, badgeTypeFilter, badgeTextFilter, allBadgesByGame]);

    const hasBadgeFilter = badgeTypeFilter !== 'all' || badgeTextFilter;

    // Compute total stats witnessed — responds to badge filter
    const totalStats = useMemo(() => {
        const springGameIds = new Set((games || []).filter(g => g.gameType === 'spring').map(g => g.gameId));
        const filteredGameIds = hasBadgeFilter ? new Set(badgeFilteredGames.map(g => g.gameId)) : null;
        const stats = { H: 0, R: 0, HR: 0, RBI: 0, SO: 0, BB: 0, SB: 0, '2B': 0, '3B': 0 };
        let pitK = 0;
        let gameCount = 0;
        const countedGames = new Set();
        (playerGames || []).forEach(pg => {
            if (springGameIds.has(pg.gameId)) return;
            if (filteredGameIds && !filteredGameIds.has(pg.gameId)) return;
            stats.H += (pg.h || 0); stats.R += (pg.r || 0); stats.HR += (pg.hr || 0);
            stats.RBI += (pg.rbi || 0); stats.SO += (pg.so || 0); stats.BB += (pg.bb || 0);
            stats.SB += (pg.sb || 0); stats['2B'] += (pg.doubles || 0); stats['3B'] += (pg.triples || 0);
            countedGames.add(pg.gameId);
        });
        (pitcherGames || []).forEach(pg => {
            if (springGameIds.has(pg.gameId)) return;
            if (filteredGameIds && !filteredGameIds.has(pg.gameId)) return;
            pitK += (pg.so || 0);
            countedGames.add(pg.gameId);
        });
        return { ...stats, pitK, gameCount: countedGames.size };
    }, [games, playerGames, pitcherGames, badgeFilteredGames, hasBadgeFilter]);

    const searchableGames = useMemo(() => badgeFilteredGames.map(g => ({
        ...g, _searchTeams: (TEAM_CODE_TO_NAME[g.awayTeam] || '') + ' ' + (TEAM_CODE_TO_NAME[g.homeTeam] || '')
    })), [badgeFilteredGames]);

    return (
        <>
            {/* Total Stats Witnessed */}
            <div className="bg-gradient-to-r from-teal-600 to-teal-700 rounded-lg shadow-lg p-5 text-white mb-4">
                <h2 className="text-xl font-bold mb-3">📊 Total Stats Witnessed <span className="text-sm font-normal opacity-80">({totalStats.gameCount} regular season & postseason games)</span></h2>
                <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-3">
                    {[
                        { label: 'Hits', val: totalStats.H },
                        { label: 'Runs', val: totalStats.R },
                        { label: 'HR', val: totalStats.HR },
                        { label: 'RBI', val: totalStats.RBI },
                        { label: '2B', val: totalStats['2B'] },
                        { label: '3B', val: totalStats['3B'] },
                        { label: 'K', val: totalStats.pitK },
                        { label: 'BB', val: totalStats.BB },
                        { label: 'SB', val: totalStats.SB },
                    ].map(s => (
                        <div key={s.label} className="bg-white/20 rounded-lg p-2 text-center">
                            <div className="text-2xl font-bold">{s.val.toLocaleString()}</div>
                            <div className="text-xs opacity-90">{s.label}</div>
                        </div>
                    ))}
                </div>
            </div>
            {/* Badge filter bar */}
            <div className="bg-white rounded-lg border border-slate-200 mb-2 p-3">
                <div className="flex flex-wrap items-center gap-3">
                    <span className="small-text font-semibold text-slate-600">🏅 Badge Filter:</span>
                    <select
                        value={badgeTypeFilter}
                        onChange={(e) => setBadgeTypeFilter(e.target.value)}
                        className="px-3 py-1.5 body-text border rounded-lg"
                    >
                        <option value="all">All Games</option>
                        <option value="any-badge">Any Badge</option>
                        {availableBadgeTypes.map(t => (
                            <option key={t} value={t}>{badgeTypeLabels[t] || t}</option>
                        ))}
                    </select>
                    <input
                        type="text"
                        placeholder="Search badge text..."
                        value={badgeTextFilter}
                        onChange={(e) => setBadgeTextFilter(e.target.value)}
                        className="px-3 py-1.5 body-text border rounded-lg min-w-[200px]"
                    />
                    {hasBadgeFilter && (
                        <button
                            onClick={() => { setBadgeTypeFilter('all'); setBadgeTextFilter(''); }}
                            className="px-3 py-1.5 body-text text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded"
                        >
                            Clear
                        </button>
                    )}
                    {hasBadgeFilter && (
                        <span className="small-text text-slate-500">{badgeFilteredGames.length} of {games.length} games</span>
                    )}
                </div>
            </div>
            <DataTable
                title="📋 Game Log"
                data={searchableGames}
                defaultSortKey="date"
                enableDateFilter={true}
                onRowClick={(row) => setSelectedGame(row)}
                filterOptions={[
                    { key: 'gameType', label: 'Game Type', displayFn: (v) => v === 'spring' ? 'Spring Training' : v === 'postseason' ? 'Postseason' : v === 'regular' ? 'Regular Season' : v },
                    { key: 'homeTeam', label: 'Home Team' },
                    { key: 'venue', label: 'Venue' }
                ]}
                columns={[
                    { key: 'date', label: 'Date', render: (v, row) => (
                        <div className="flex items-center gap-1.5">
                            <button className="text-blue-600 hover:underline font-medium" title="Open game recap" onClick={(e) => { e.stopPropagation(); setSelectedGame(row); }}>{v}</button>
                            {row.gameType === 'spring' && <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-[10px] font-semibold rounded">ST</span>}
                            {row.gameType === 'postseason' && <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 text-[10px] font-semibold rounded">PS</span>}
                        </div>
                    )},
                    { key: 'awayTeam', label: 'Away', render: (v) => <button className="text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('progress', 'matchups'); }}><TeamToken code={v} logoSize={18} /></button> },
                    { key: 'homeTeam', label: 'Home', render: (v) => <button className="text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('progress', 'matchups'); }}><TeamToken code={v} logoSize={18} /></button> },
                    { key: 'score', label: 'Score' },
                    { key: 'venue', label: 'Venue', render: (v) => <button className="text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('venues'); }}>{v}</button> },
                    { key: 'source', label: 'Source', render: (_, row) => <SourceBadge game={row} compact /> },
                    {
                        key: 'badges',
                        label: 'Badges',
                        className: 'min-w-[18rem] max-w-[30rem]',
                        headerClassName: 'min-w-[18rem]',
                        render: (_, row) => (
                            <BadgeCell
                                badges={allBadgesByGame[row.gameId] || []}
                                badgeColors={badgeColors}
                                onBadgeClick={(badge) => setSelectedBadge({ badge, gameId: row.gameId })}
                            />
                        )
                    },
                    {
                        key: 'gameId',
                        label: 'Game',
                        className: 'min-w-[8.5rem]',
                        render: (v, row) => (
                            <div className="flex items-center gap-2 whitespace-nowrap">
                                <GameLink gameId={v} />
                                <button
                                    onClick={() => setSelectedGame(row)}
                                    className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold"
                                >
                                    Open
                                </button>
                            </div>
                        )
                    }
                ]}
            />
            
            {selectedGame && (() => {
                const toSort = toSortableDate;
                const sortedGames = [...(games || [])].sort((a, b) => toSort(b.date).localeCompare(toSort(a.date)));
                const idx = sortedGames.findIndex(g => g.gameId === selectedGame.gameId);
                const prevGame = idx > 0 ? sortedGames[idx - 1] : null;
                const nextGame = idx < sortedGames.length - 1 ? sortedGames[idx + 1] : null;
                return (
                    <GameDetailsModal
                        game={selectedGame}
                        playerGames={playerGames}
                        pitcherGames={pitcherGames}
                        careerFirsts={dedupedCareerFirstsByGame[selectedGame.gameId] || []}
                        allTimePassings={(allTimePassingsByGame || {})[selectedGame.gameId] || []}
                        badges={allBadgesByGame?.[selectedGame.gameId] || []}
                        onClose={() => setSelectedGame(null)}
                        onPrev={prevGame ? () => setSelectedGame(prevGame) : null}
                        onNext={nextGame ? () => setSelectedGame(nextGame) : null}
                        gameIndex={idx >= 0 ? idx + 1 : null}
                        totalGames={sortedGames.length}
                    />
                );
            })()}

            {selectedBadge && (
                <BadgeDetailModal
                    badge={selectedBadge.badge}
                    game={(games || []).find(g => g.gameId === selectedBadge.gameId) || null}
                    games={games}
                    playerGames={playerGames}
                    pitcherGames={pitcherGames}
                    careerFirstsByGame={careerFirstsByGame}
                    allBadgesByGame={allBadgesByGame}
                    onClose={() => setSelectedBadge(null)}
                    onGoToGame={() => {
                        const g = (games || []).find(gg => gg.gameId === selectedBadge.gameId);
                        if (g) setSelectedGame(g);
                    }}
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
                    <h2 className="section-title font-bold text-slate-900">🗺️ Stadium Checklist</h2>

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
                    <span className="text-slate-600">Legend:</span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-slate-400 opacity-40"></span>
                        <span className="text-slate-600">Not Visited</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-green-500"></span>
                        <span className="text-slate-600">Visited</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-4 h-4 rounded-full bg-orange-500"></span>
                        <span className="text-slate-600">Visited + Saw Orioles</span>
                    </span>
                </div>
            </div>

            {/* Map Container */}
            <div ref={mapRef} style={{ height: '500px', width: '100%' }}></div>

            {/* Progress Stats */}
            <div className="p-4 border-t bg-slate-50">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">{stats.visitedCurrent}/{stats.currentTotal}</div>
                        <div className="small-text text-slate-600">Current Stadiums</div>
                        <div className="text-xs text-slate-400">{stats.percentCurrent}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-500">{stats.oriolesCurrent}/{stats.currentTotal}</div>
                        <div className="small-text text-slate-600">Saw Orioles</div>
                        <div className="text-xs text-slate-400">{stats.percentOrioles}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">{stats.totalVisited}</div>
                        <div className="small-text text-slate-600">Total Stadiums</div>
                        <div className="text-xs text-slate-400">Including historical</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">{stats.totalOrioles}</div>
                        <div className="small-text text-slate-600">O's Venues</div>
                        <div className="text-xs text-slate-400">Total Orioles venues</div>
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
                            <h3 className="font-semibold text-slate-700 mb-3">
                                Visited Stadiums
                                <span className="text-sm font-normal text-slate-500 ml-2">({visitedStadiums.length})</span>
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
                                                <div className="font-medium truncate text-slate-900">{stadium.name}</div>
                                                <div className="text-xs text-slate-500">
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
                            <h3 className="font-semibold text-slate-700 mb-3">
                                Still To Visit
                                <span className="text-sm font-normal text-slate-500 ml-2">({toVisit.length} remaining)</span>
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                {toVisit.map(stadium => (
                                    <div
                                        key={stadium.id}
                                        className="flex items-center gap-2 p-2 rounded text-sm bg-slate-50 border border-slate-200"
                                    >
                                        <span className="text-lg opacity-30">⬜</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium truncate text-slate-400">{stadium.name}</div>
                                            <div className="text-xs text-slate-400">{stadium.team}</div>
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
    'AL West': ['ANA', 'HOU', 'ATH', 'SEA', 'TEX'],
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
    'MIN': 'MIN', 'HOU': 'HOU', 'OAK': 'ATH', 'ATH': 'ATH', 'SEA': 'SEA', 'TEX': 'TEX',
    'ATL': 'ATL', 'MIA': 'MIA', 'PHI': 'PHI', 'CIN': 'CIN', 'MIL': 'MIL',
    'PIT': 'PIT', 'ARI': 'ARI', 'COL': 'COL',
};

const TEAM_CODE_TO_NAME = {
    // Retrosheet codes
    'BAL': 'Baltimore Orioles', 'BOS': 'Boston Red Sox', 'NYA': 'New York Yankees',
    'TBA': 'Tampa Bay Rays', 'TOR': 'Toronto Blue Jays', 'CHA': 'Chicago White Sox',
    'CLE': 'Cleveland Guardians', 'DET': 'Detroit Tigers', 'KCA': 'Kansas City Royals',
    'MIN': 'Minnesota Twins', 'ANA': 'Los Angeles Angels', 'HOU': 'Houston Astros',
    'OAK': 'Oakland Athletics', 'ATH': 'Athletics', 'SEA': 'Seattle Mariners', 'TEX': 'Texas Rangers',
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
    'OAK': 'ATH',  // Oakland Athletics -> Athletics (Sacramento 2025+)
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
// Regular-season game-count thresholds (postseason/spring tracked separately below)
const GAME_MILESTONES = [1, 10, 25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 750, 1000];
const POSTSEASON_MILESTONES = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100];
const SPRING_MILESTONES = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100];

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
        const parseDate = toSortableDate;
        return parseDate(dateA).localeCompare(parseDate(dateB));
    });

    const gameMilestones = {};
    let gameCount = 0;
    let regularCount = 0;
    let postseasonCount = 0;
    let springCount = 0;
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

        // Game count milestones — split by game type so regular season,
        // postseason, and spring training each get their own track.
        const gameType = (game.gameType || 'regular').toLowerCase();
        if (gameType === 'regular') {
            regularCount++;
            if (GAME_MILESTONES.includes(regularCount)) {
                gameMilestones[gameId].badges.push({
                    type: 'game-count',
                    text: `Game #${regularCount}`,
                    title: `${ordinal(regularCount)} regular-season game attended`
                });
            }
        } else if (gameType === 'postseason') {
            postseasonCount++;
            if (POSTSEASON_MILESTONES.includes(postseasonCount)) {
                gameMilestones[gameId].badges.push({
                    type: 'game-count-postseason',
                    text: `Postseason #${postseasonCount}`,
                    title: `${ordinal(postseasonCount)} postseason game attended`
                });
            }
        } else if (gameType === 'spring' || gameType === 'exhibition') {
            springCount++;
            if (SPRING_MILESTONES.includes(springCount)) {
                gameMilestones[gameId].badges.push({
                    type: 'game-count-spring',
                    text: `Spring #${springCount}`,
                    title: `${ordinal(springCount)} spring training game attended`
                });
            }
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
        <div className="bg-white rounded-lg border border-slate-200">
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
                                className={`px-3 py-2 ${viewMode === 'teams' ? 'bg-blue-500 text-white' : 'bg-slate-100'}`}
                            >
                                Teams
                            </button>
                            <button
                                onClick={() => setViewMode('stadiums')}
                                className={`px-3 py-2 ${viewMode === 'stadiums' ? 'bg-blue-500 text-white' : 'bg-slate-100'}`}
                            >
                                Stadiums
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Progress Summary */}
            <div className="p-4 bg-slate-50 border-b">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">
                            {currentData.teamsSeen}/{currentData.totalTeams}
                        </div>
                        <div className="text-sm text-slate-600">Teams Seen</div>
                        <div className="text-xs text-slate-400">{teamProgress}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">
                            {currentData.stadiumsVisited}/{currentData.totalStadiums}
                        </div>
                        <div className="text-sm text-slate-600">Stadiums Visited</div>
                        <div className="text-xs text-slate-400">{stadiumProgress}% complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">
                            {Object.keys(tracking.divisionTeamsCompleted || {}).length}/6
                        </div>
                        <div className="text-sm text-slate-600">Div. Teams</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-indigo-600">
                            {Object.keys(tracking.divisionStadiumsCompleted || {}).length}/6
                        </div>
                        <div className="text-sm text-slate-600">Div. Stadiums</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-600">
                            {tracking.totalGames || games?.length || 0}
                        </div>
                        <div className="text-sm text-slate-600">Total Games</div>
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
                                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:shadow-sm transition-all ${
                                    isSeen
                                        ? 'bg-green-50 border-green-200 hover:border-green-300'
                                        : 'bg-slate-50 border-slate-200 hover:border-slate-300'
                                }`}
                                onClick={() => {
                                    if (isSeen) {
                                        if (viewMode === 'teams') window.__navigateTab('progress', 'matchups');
                                        else window.__navigateTab('venues');
                                    }
                                }}
                            >
                                <span className="text-2xl">{isSeen ? '✅' : '⬜'}</span>
                                <div className="flex-1 min-w-0">
                                    <div className={`font-medium truncate ${!isSeen ? 'text-slate-400' : 'text-blue-700'}`}>
                                        {displayName || 'Unknown'}
                                    </div>
                                    <div className="text-xs text-slate-500">
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
                    <h3 className="font-semibold text-slate-700 mb-4">Division Progress</h3>
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
                                        isComplete ? 'bg-green-50 border-green-300' : 'bg-white border-slate-200'
                                    }`}
                                >
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-semibold">{div}</span>
                                        <span className="text-sm">{divData.teamsSeen}/{divData.totalTeams}</span>
                                    </div>
                                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
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
const BadgesDisplay = ({ games, playerGames, pitcherGames, careerFirstsByGame }) => {
    const [filter, setFilter] = useState('all');
    const [selectedBadge, setSelectedBadge] = useState(null);  // { badge, gameId }
    const milestoneData = useMemo(() => computeGameMilestones(games), [games]);
    const cumulativeBadges = useMemo(
        () => computeCumulativeStatBadges(games || [], playerGames || [], pitcherGames || []),
        [games, playerGames, pitcherGames]
    );

    // Drop "Career Pitching Game #N" when "Career Game #N" exists for the same player.
    const dedupedCareerFirstsByGame = useMemo(() => {
        const result = {};
        Object.entries(careerFirstsByGame || {}).forEach(([gid, firsts]) => {
            const list = firsts || [];
            const haveBattingG = new Set();
            list.forEach(f => {
                const m = (f.milestone || '').match(/^Career Game #(\d+)$/);
                if (m) haveBattingG.add(`${f.player_name}|${m[1]}`);
            });
            result[gid] = list.filter(f => {
                const m = (f.milestone || '').match(/^Career Pitching Game #(\d+)$/);
                if (!m) return true;
                return !haveBattingG.has(`${f.player_name}|${m[1]}`);
            });
        });
        return result;
    }, [careerFirstsByGame]);

    // Collect all badges (regular game milestones + cumulative + career firsts)
    const allBadges = useMemo(() => {
        const badges = [];
        const sortedGames = [...(games || [])].sort((a, b) => toSortableDate(b.date).localeCompare(toSortableDate(a.date)));

        sortedGames.forEach(game => {
            const meta = { date: game.date, gameId: game.gameId, away: game.awayTeam, home: game.homeTeam, venue: game.venue };
            const regularBadges = milestoneData.milestones?.[game.gameId]?.badges || [];
            regularBadges.forEach(b => badges.push({ ...b, ...meta }));
            const cuml = cumulativeBadges[game.gameId] || [];
            cuml.forEach(b => badges.push({ ...b, ...meta }));
            const firsts = dedupedCareerFirstsByGame[game.gameId] || [];
            firsts.forEach(f => badges.push({
                type: 'career-first',
                text: `⭐ ${getLastName(f.player_name)}: ${shortenMilestone(f.milestone)}`,
                title: `${f.player_name || 'Unknown'}'s ${f.milestone || 'milestone'}`,
                meta: {
                    playerId: f.player_id, playerName: f.player_name,
                    milestone: f.milestone, number: f.number, careerTotalAfter: f.career_total_after,
                },
                ...meta,
            }));
        });

        return badges;
    }, [games, milestoneData, cumulativeBadges, dedupedCareerFirstsByGame]);

    // Need allBadgesByGame structure for the GenericBadgeDetail "previous occurrence" lookup
    const allBadgesByGame = useMemo(() => {
        const result = {};
        allBadges.forEach(b => {
            if (!result[b.gameId]) result[b.gameId] = [];
            result[b.gameId].push(b);
        });
        return result;
    }, [allBadges]);

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
            'game-count-postseason': '🏆',
            'game-count-spring': '🌱',
            'team': '👕',
            'venue': '🏟️',
            'div-first': '🌟',
            'div-complete': '🏆',
            'div-stadiums': '🏟️',
            'matchup': '⚔️',
            'holiday': '🎉',
            'career-first': '⭐',
            'cumulative-stat': '📊',
            'venue-stat': '🏟️',
            'pitch-velo': '🚀',
            'player-stat': '🎯',
            'player-rank': '📈',
        };
        return icons[type] || '🏅';
    };

    const getBadgeColor = (type) => {
        const colors = {
            'game-count': 'bg-purple-100 border-purple-300',
            'game-count-postseason': 'bg-yellow-100 border-yellow-300',
            'game-count-spring': 'bg-green-100 border-green-300',
            'team': 'bg-blue-100 border-blue-300',
            'venue': 'bg-green-100 border-green-300',
            'div-first': 'bg-yellow-100 border-yellow-300',
            'div-complete': 'bg-orange-100 border-orange-300',
            'matchup': 'bg-pink-100 border-pink-300',
            'holiday': 'bg-red-100 border-red-300',
            'div-stadiums': 'bg-indigo-100 border-indigo-300',
            'career-first': 'bg-amber-100 border-amber-300',
            'cumulative-stat': 'bg-teal-100 border-teal-300',
            'venue-stat': 'bg-purple-100 border-purple-300',
            'pitch-velo': 'bg-red-100 border-red-300',
            'player-stat': 'bg-sky-100 border-sky-300',
            'player-rank': 'bg-rose-100 border-rose-300',
        };
        return colors[type] || 'bg-slate-100 border-slate-300';
    };

    return (
        <div className="bg-white rounded-lg border border-slate-200">
            <div className="p-4 border-b">
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <h2 className="section-title font-bold">Badges & Milestones</h2>
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="px-3 py-2 border rounded-lg"
                    >
                        <option value="all">All Badges ({badgeCounts.all})</option>
                        <option value="game-count">Reg-Season Game Count ({badgeCounts['game-count'] || 0})</option>
                        <option value="game-count-postseason">Postseason Game Count ({badgeCounts['game-count-postseason'] || 0})</option>
                        <option value="game-count-spring">Spring Training Game Count ({badgeCounts['game-count-spring'] || 0})</option>
                        <option value="team">Team Milestones ({badgeCounts['team'] || 0})</option>
                        <option value="venue">Venue ({badgeCounts['venue'] || 0})</option>
                        <option value="div-first">Division Firsts ({badgeCounts['div-first'] || 0})</option>
                        <option value="div-complete">Div. Teams Complete ({badgeCounts['div-complete'] || 0})</option>
                        <option value="div-stadiums">Div. Stadiums Complete ({badgeCounts['div-stadiums'] || 0})</option>
                        <option value="matchup">First Matchups ({badgeCounts['matchup'] || 0})</option>
                        <option value="holiday">Holiday Games ({badgeCounts['holiday'] || 0})</option>
                        <option value="career-first">Career Firsts ({badgeCounts['career-first'] || 0})</option>
                        <option value="cumulative-stat">Cumulative Stats ({badgeCounts['cumulative-stat'] || 0})</option>
                        <option value="venue-stat">Venue Stats ({badgeCounts['venue-stat'] || 0})</option>
                        <option value="pitch-velo">100+ mph ({badgeCounts['pitch-velo'] || 0})</option>
                        <option value="player-stat">Player Milestones ({badgeCounts['player-stat'] || 0})</option>
                        <option value="player-rank">Top-5 Movement ({badgeCounts['player-rank'] || 0})</option>
                    </select>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="p-4 bg-slate-50 border-b">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">{badgeCounts.all}</div>
                        <div className="text-sm text-slate-600">Total Badges</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">{badgeCounts['div-complete'] || 0}</div>
                        <div className="text-sm text-slate-600">Divisions Complete</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">{milestoneData.tracking?.venueOrder?.length || 0}</div>
                        <div className="text-sm text-slate-600">Unique Venues</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-orange-600">{Object.keys(milestoneData.tracking?.matchupsSeen || {}).length}</div>
                        <div className="text-sm text-slate-600">Unique Matchups</div>
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
                                onClick={() => setSelectedBadge({ badge, gameId: badge.gameId })}
                            >
                                <div className="flex items-start gap-3">
                                    <span className="text-2xl">{getBadgeIcon(badge.type)}</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold text-slate-800 truncate">{badge.text}</div>
                                        <div className="text-xs text-slate-600 truncate">{badge.away} vs {badge.home}</div>
                                        <div className="text-xs text-slate-400 mt-1">{badge.date}</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
            {selectedBadge && (
                <BadgeDetailModal
                    badge={selectedBadge.badge}
                    game={(games || []).find(g => g.gameId === selectedBadge.gameId) || null}
                    games={games}
                    playerGames={playerGames}
                    pitcherGames={pitcherGames}
                    careerFirstsByGame={careerFirstsByGame}
                    allBadgesByGame={allBadgesByGame}
                    onClose={() => setSelectedBadge(null)}
                    onGoToGame={() => {
                        window._pendingGameId = selectedBadge.gameId;
                        if (window.__navigateTab) window.__navigateTab('gamelog');
                    }}
                />
            )}
        </div>
    );
};

// Error Boundary to catch rendering errors gracefully
'''
