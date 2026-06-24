"""React app chunk: core."""

CODE = r'''const GameDetailsModal = ({ game, playerGames, pitcherGames, careerFirsts, allTimePassings, debuts, finalGames, badges, onClose, onPrev, onNext, gameIndex, totalGames, initialTab, focusInning }) => {
    const [activeTab, setActiveTab] = useState(initialTab || 'boxscore');

    useEffect(() => {
        const onKey = (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'ArrowLeft' && onPrev) { e.stopPropagation(); onPrev(); }
            if (e.key === 'ArrowRight' && onNext) { e.stopPropagation(); onNext(); }
        };
        window.addEventListener('keydown', onKey, true);
        return () => window.removeEventListener('keydown', onKey, true);
    }, [onPrev, onNext]);

    useEffect(() => {
        setActiveTab(initialTab || 'boxscore');
    }, [game?.gameId, initialTab]);

    useEffect(() => {
        if (activeTab !== 'playbyplay' || !focusInning) return;
        const targetId = `pbp-${game.gameId}-${focusInning.half}-${focusInning.inning}`;
        window.setTimeout(() => {
            const target = document.getElementById(targetId);
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 80);
    }, [activeTab, focusInning, game?.gameId]);

    const cleanPersonName = (name) => String(name || '').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim();
    const compactPlayDescription = (description, playerName) => {
        let text = String(description || '').replace(/\u00a0/g, ' ').trim();
        const cleanName = cleanPersonName(playerName);
        if (cleanName && text.toLowerCase().startsWith(cleanName.toLowerCase())) {
            text = text.slice(cleanName.length).trim();
        }
        return text.replace(/^\s*[.,-]\s*/, '').replace(/\.$/, '');
    };

    const gameData = useMemo(() => {
        if (!game) return null;

        // Get all players/pitchers from this game
        const gamePlayers = playerGames.filter(pg => pg.gameId === game.gameId);
        const gamePitchers = pitcherGames.filter(pg => pg.gameId === game.gameId);

        const sortHittersForBoxScore = (rows) => rows
            .map((player, index) => ({ player, index }))
            .sort((a, b) => {
                const aOrder = Number(a.player.battingOrder);
                const bOrder = Number(b.player.battingOrder);
                const aRank = Number.isFinite(aOrder) ? aOrder : a.index;
                const bRank = Number.isFinite(bOrder) ? bOrder : b.index;
                return aRank - bRank || a.index - b.index;
            })
            .map(({ player }) => player);

        // Separate by team, preserving the source box-score batting order.
        const homeHitters = sortHittersForBoxScore(gamePlayers.filter(p => p.team === game.homeTeam && (p.pa > 0 || p.ab > 0)));
        const awayHitters = sortHittersForBoxScore(gamePlayers.filter(p => p.team === game.awayTeam && (p.pa > 0 || p.ab > 0)));
        const homePitchers = gamePitchers.filter(p => p.team === game.homeTeam).sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
        const awayPitchers = gamePitchers.filter(p => p.team === game.awayTeam).sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
        
        // Calculate team totals
        const homeHittingTotals = homeHitters.reduce((acc, p) => ({
            ab: acc.ab + p.ab,
            h: acc.h + p.h,
            r: acc.r + p.r,
            rbi: acc.rbi + p.rbi,
            hr: acc.hr + p.hr,
            doubles: acc.doubles + (p.doubles || 0),
            triples: acc.triples + (p.triples || 0),
            bb: acc.bb + p.bb,
            so: acc.so + p.so
        }), { ab: 0, h: 0, r: 0, rbi: 0, hr: 0, doubles: 0, triples: 0, bb: 0, so: 0 });

        const awayHittingTotals = awayHitters.reduce((acc, p) => ({
            ab: acc.ab + p.ab,
            h: acc.h + p.h,
            r: acc.r + p.r,
            rbi: acc.rbi + p.rbi,
            hr: acc.hr + p.hr,
            doubles: acc.doubles + (p.doubles || 0),
            triples: acc.triples + (p.triples || 0),
            bb: acc.bb + p.bb,
            so: acc.so + p.so
        }), { ab: 0, h: 0, r: 0, rbi: 0, hr: 0, doubles: 0, triples: 0, bb: 0, so: 0 });
        
        // Build annotations from career firsts and superlatives
        const playerAnnotations = {};
        (careerFirsts || []).forEach(f => {
            if (!playerAnnotations[f.player_id]) playerAnnotations[f.player_id] = [];
            playerAnnotations[f.player_id].push(f.milestone);
        });

        // Players seen live for the first time in this game (precomputed
        // by the serializer by walking attended games chronologically).
        const firstSeenSet = new Set(game.firstSeenPlayerIds || []);

        // Find game superlatives from pitch/hit data
        let fastestPitch = null, hardestHit = null, mostKs = null;
        if (game.pitchData) {
            Object.entries(game.pitchData).forEach(([pid, pd]) => {
                if (pd.maxSpeed && (!fastestPitch || pd.maxSpeed > fastestPitch.speed)) {
                    fastestPitch = { playerId: pid, name: pd.name, speed: pd.maxSpeed };
                }
            });
        }
        if (game.hitData) {
            Object.entries(game.hitData).forEach(([pid, hd]) => {
                if (hd.maxExitVelo && (!hardestHit || hd.maxExitVelo > hardestHit.velo)) {
                    const exactDescription = hd.maxExitVeloDescription || hd.maxExitVeloResult || '';
                    const result = exactDescription ? compactPlayDescription(exactDescription, hd.name) : '';
                    hardestHit = {
                        playerId: pid,
                        name: hd.name,
                        velo: hd.maxExitVelo,
                        dist: hd.maxExitVeloDistance || hd.maxDistance,
                        result
                    };
                }
            });
        }
        const allPitchers = [...homePitchers, ...awayPitchers];
        allPitchers.forEach(p => {
            if (p.so > 0 && (!mostKs || p.so > mostKs.so)) {
                mostKs = { playerId: p.playerId, name: p.name, so: p.so };
            }
        });

        return {
            homeHitters, awayHitters, homePitchers, awayPitchers,
            homeHittingTotals, awayHittingTotals,
            playerAnnotations, fastestPitch, hardestHit, mostKs,
            firstSeenSet
        };
    }, [game, playerGames, pitcherGames, careerFirsts]);

    if (!game || !gameData) return null;

    const awayRuns = game.linescore?.away?.runs;
    const homeRuns = game.linescore?.home?.runs;
    const winnerTeam = awayRuns != null && homeRuns != null
        ? awayRuns > homeRuns ? game.awayTeam : homeRuns > awayRuns ? game.homeTeam : 'Tie'
        : null;
    const runMargin = awayRuns != null && homeRuns != null ? Math.abs(awayRuns - homeRuns) : null;
    const formatHardestHitDetail = (hit) => {
        if (!hit) return '';
        return `${hit.name}${hit.result ? ` - ${hit.result}` : ''}${hit.dist ? ` (${hit.dist} ft)` : ''}`;
    };
    const formatCareerEventPerformance = (r) => {
        if (!r) return '';
        if (r.ip && r.ip !== '' && r.ip !== '0.0') {
            return `${r.ip} IP, ${r.h_p || 0} H, ${r.er || 0} ER, ${r.bb_p || 0} BB, ${r.so_p || 0} SO${r.decision ? ` (${r.decision})` : ''}`;
        }
        if ((r.ab || 0) > 0) {
            const parts = [`${r.h || 0}-${r.ab}`];
            if ((r.hr || 0) > 0) parts.push(`${r.hr} HR`);
            if ((r.rbi || 0) > 0) parts.push(`${r.rbi} RBI`);
            if ((r.r || 0) > 0) parts.push(`${r.r} R`);
            if ((r.bb || 0) > 0) parts.push(`${r.bb} BB`);
            if ((r.so || 0) > 0) parts.push(`${r.so} SO`);
            return parts.join(', ');
        }
        return r.position ? `${r.position} appearance` : 'Defensive appearance';
    };
    const showHardestHitHighlight = gameData.hardestHit && gameData.hardestHit.velo >= 105;
    const showFastestPitchHighlight = gameData.fastestPitch && gameData.fastestPitch.speed >= 100;
    const showMostKsHighlight = gameData.mostKs && gameData.mostKs.so >= 10;
    const careerMilestoneItems = (careerFirsts || []).map(f => `${getLastName(f.player_name)} ${shortenMilestone(f.milestone)}`);
    const careerMilestoneDetail = careerMilestoneItems.length > 2
        ? `${careerMilestoneItems.slice(0, 2).join(', ')}, +${careerMilestoneItems.length - 2} more`
        : careerMilestoneItems.join(', ');
    const careerBookendItems = [
        ...(debuts || []).map(d => ({ ...d, kind: 'Debut', summary: `${getLastName(d.player)} debut` })),
        ...(finalGames || []).map(f => ({ ...f, kind: 'Final Game', summary: `${getLastName(f.player)} final game` })),
    ];
    const careerBookendDetails = careerBookendItems.slice(0, 4).map(e => `${e.summary}${e.team ? ` (${e.team})` : ''}`);
    if (careerBookendItems.length > 4) careerBookendDetails.push(`+${careerBookendItems.length - 4} more`);
    const gameStoryItems = [
        winnerTeam && winnerTeam !== 'Tie' && {
            label: 'Result',
            value: `${winnerTeam} by ${runMargin}`,
            detail: `${game.awayTeam} ${awayRuns}, ${game.homeTeam} ${homeRuns}`,
            color: 'blue'
        },
        careerBookendItems.length > 0 && {
            label: 'Debuts / finals',
            value: `${careerBookendItems.length} event${careerBookendItems.length === 1 ? '' : 's'}`,
            details: careerBookendDetails,
            color: 'green'
        },
        showHardestHitHighlight && {
            label: 'Hardest contact',
            value: `${gameData.hardestHit.velo} mph`,
            detail: formatHardestHitDetail(gameData.hardestHit),
            color: 'slate'
        },
        showFastestPitchHighlight && {
            label: 'Fastest pitch',
            value: `${gameData.fastestPitch.speed} mph`,
            detail: gameData.fastestPitch.name,
            color: 'red'
        },
        showMostKsHighlight && {
            label: 'Most strikeouts',
            value: `${gameData.mostKs.so} K`,
            detail: `${gameData.mostKs.name} led all pitchers`,
            color: 'orange'
        },
        careerFirsts?.length > 0 && {
            label: 'Career milestones',
            value: careerFirsts.length,
            detail: careerMilestoneDetail,
            color: 'slate'
        },
        allTimePassings?.length > 0 && {
            label: 'All-time movement',
            value: allTimePassings.length,
            detail: allTimePassings.slice(0, 2).map(p => `${getLastName(p.player_name)} #${p.new_rank} ${p.stat_name}`).join(', '),
            color: 'purple'
        },
        game.keyPlays?.length > 0 && {
            label: 'Key plays',
            value: game.keyPlays.length,
            detail: game.keyPlays.slice(0, 2).map(p => `${p.batter} ${p.type === 'grand_slam' ? 'grand slam' : 'HR'}`).join(', '),
            color: 'green'
        }
    ].filter(Boolean).slice(0, 6);

    const pitchDataEntries = Object.entries(game.pitchData || {});
    const normalizePitcherName = (name) => cleanPersonName(name).toLowerCase().replace(/[^a-z0-9]/g, '');
    const usedPitchDataIds = new Set();

    const resolvePitchDataForPitcher = (pitcher) => {
        const playerId = String(pitcher?.playerId || '');
        if (playerId && game.pitchData?.[playerId] && !usedPitchDataIds.has(playerId)) {
            return [playerId, game.pitchData[playerId]];
        }

        const pitcherNameKey = normalizePitcherName(pitcher?.name);
        if (!pitcherNameKey) return null;

        return pitchDataEntries.find(([candidateId, pitchData]) => {
            return !usedPitchDataIds.has(candidateId) && normalizePitcherName(pitchData?.name) === pitcherNameKey;
        }) || null;
    };

    const buildPitchDataGroup = (team, pitchers) => {
        const items = (pitchers || []).map((pitcher) => {
            const match = resolvePitchDataForPitcher(pitcher);
            if (!match) return null;

            const [pid, pd] = match;
            const hasPitcherOrder = Number.isFinite(pitcher.order);
            usedPitchDataIds.add(pid);
            return {
                pid,
                pd,
                role: hasPitcherOrder ? (pitcher.order === 0 ? 'Starter' : 'Relief') : '',
                order: hasPitcherOrder ? pitcher.order : Number.MAX_SAFE_INTEGER
            };
        }).filter(Boolean).sort((a, b) => a.order - b.order);

        return {
            team,
            label: `${team} Pitchers`,
            totalPitches: items.reduce((sum, item) => sum + (item.pd.totalPitches || 0), 0),
            items
        };
    };

    const pitchDataGroups = [
        buildPitchDataGroup(game.awayTeam, gameData.awayPitchers),
        buildPitchDataGroup(game.homeTeam, gameData.homePitchers)
    ].filter(group => group.items.length > 0);

    const unmatchedPitchData = pitchDataEntries
        .filter(([pid]) => !usedPitchDataIds.has(pid))
        .sort((a, b) => (b[1].totalPitches || 0) - (a[1].totalPitches || 0))
        .map(([pid, pd]) => ({ pid, pd, role: '', order: Number.MAX_SAFE_INTEGER }));

    if (unmatchedPitchData.length > 0) {
        pitchDataGroups.push({
            team: 'other',
            label: 'Other Pitch Data',
            totalPitches: unmatchedPitchData.reduce((sum, item) => sum + (item.pd.totalPitches || 0), 0),
            items: unmatchedPitchData
        });
    }

    const CareerHighBadges = ({ data }) => {
        if (!data.careerHighs?.length) return null;
        return <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">Career-high {data.careerHighs.join(', ')}</span>;
    };

    const HitterRow = ({ player }) => {
        const annotations = gameData.playerAnnotations[player.playerId] || [];
        const isHardestHit = gameData.hardestHit?.playerId === player.playerId;
        const isFirstSeen = gameData.firstSeenSet?.has(player.playerId);
        return (
        <tr className="hover:bg-slate-50">
            <td className="px-3 py-2">
                <div className="flex items-center gap-1 flex-wrap">
                    <PlayerLink playerId={player.playerId} name={player.name} />
                    {isFirstSeen && <span title="First time seeing this player live" className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">1st seen</span>}
                    {annotations.length > 0 && <span title={annotations.join(', ')} className="text-amber-500 text-xs">⭐</span>}
                    {isHardestHit && <span title={`Hardest hit: ${gameData.hardestHit.velo} mph`} className="text-red-500 text-xs">💪</span>}
                    <CareerHighBadges data={player} />
                </div>
            </td>
            <td className="px-2 py-2 text-center">{player.ab || 0}</td>
            <td className="px-2 py-2 text-center font-semibold">{player.h || 0}</td>
            <td className="px-2 py-2 text-center">{player.r || 0}</td>
            <td className="px-2 py-2 text-center">{player.rbi || 0}</td>
            <td className={`px-2 py-2 text-center ${player.hr > 0 ? 'font-bold text-blue-600' : ''}`}>{player.hr || 0}</td>
            <td className="px-2 py-2 text-center">{player.doubles || 0}</td>
            <td className="px-2 py-2 text-center">{player.triples || 0}</td>
            <td className="px-2 py-2 text-center">{player.bb || 0}</td>
            <td className="px-2 py-2 text-center">{player.so || 0}</td>
        </tr>
    );
    };

    const PitcherRow = ({ pitcher }) => {
        const ip = `${Math.floor(pitcher.outs / 3)}.${pitcher.outs % 3}`;
        const decision = pitcher.wins ? 'W' : pitcher.losses ? 'L' : pitcher.saves ? 'SV' : '';
        const annotations = gameData.playerAnnotations[pitcher.playerId] || [];
        const isFastest = gameData.fastestPitch?.playerId === pitcher.playerId;
        const isMostKs = gameData.mostKs?.playerId === pitcher.playerId && pitcher.so >= 6;
        const isFirstSeen = gameData.firstSeenSet?.has(pitcher.playerId);

        return (
            <tr className="hover:bg-slate-50">
                <td className="px-3 py-2">
                    <div className="flex items-center gap-2 flex-wrap">
                        <PlayerLink playerId={pitcher.playerId} name={pitcher.name} />
                        {isFirstSeen && <span title="First time seeing this player live" className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">1st seen</span>}
                        {decision && (
                            <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                                decision === 'W' ? 'bg-green-100 text-green-700' :
                                decision === 'L' ? 'bg-red-100 text-red-700' :
                                'bg-blue-100 text-blue-700'
                            }`}>
                                {decision}
                            </span>
                        )}
                        {annotations.length > 0 && <span title={annotations.join(', ')} className="text-amber-500 text-xs">⭐</span>}
                        {isFastest && <span title={`Fastest pitch: ${gameData.fastestPitch.speed} mph`} className="text-red-500 text-xs">🔥</span>}
                        {isMostKs && <span title={`Game-high ${pitcher.so} strikeouts`} className="text-orange-500 text-xs">🔥</span>}
                        <CareerHighBadges data={pitcher} />
                    </div>
                </td>
                <td className="px-2 py-2 text-center font-semibold">{ip}</td>
                <td className="px-2 py-2 text-center">{pitcher.h || 0}</td>
                <td className="px-2 py-2 text-center">{pitcher.r || 0}</td>
                <td className="px-2 py-2 text-center">{pitcher.er || 0}</td>
                <td className="px-2 py-2 text-center">{pitcher.bb || 0}</td>
                <td className="px-2 py-2 text-center font-semibold">{pitcher.so || 0}</td>
                <td className="px-2 py-2 text-center">{pitcher.hr || 0}</td>
            </tr>
        );
    };

    const PitchDataCard = ({ item }) => {
        const { pid, pd, role } = item;

        return (
            <div key={pid} className="bg-slate-50 rounded-lg p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="min-w-0">
                        <span className="font-semibold body-text">{pd.name}</span>
                        {role && <span className="ml-2 px-2 py-0.5 rounded bg-white text-slate-500 text-xs font-medium">{role}</span>}
                    </div>
                    <span className="small-text text-slate-500 whitespace-nowrap">{pd.totalPitches} pitches</span>
                </div>
                <div className="grid grid-cols-3 gap-3 small-text mb-3">
                    {pd.maxSpeed && (
                        <div className="bg-white p-2 rounded text-center">
                            <div className="text-slate-500">Max Velo</div>
                            <div className="font-bold text-red-600">{pd.maxSpeed} mph</div>
                        </div>
                    )}
                    {pd.avgSpeed && (
                        <div className="bg-white p-2 rounded text-center">
                            <div className="text-slate-500">Avg Velo</div>
                            <div className="font-bold text-slate-900">{pd.avgSpeed} mph</div>
                        </div>
                    )}
                    {pd.avgSpinRate && (
                        <div className="bg-white p-2 rounded text-center">
                            <div className="text-slate-500">Avg Spin</div>
                            <div className="font-bold text-purple-600">{pd.avgSpinRate} rpm</div>
                        </div>
                    )}
                </div>
                {pd.pitchTypes && Object.keys(pd.pitchTypes).length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                        {Object.entries(pd.pitchTypes).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
                            <span key={type} className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                                {pd.pitchTypeNames?.[type] || type}: {count}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        );
    };
    
    // Tab content components
    const BoxScoreTab = () => (
        <>
            {/* Away Team Hitters */}
            <div className="p-6 border-b">
                <h4 className="subsection-title font-bold mb-3">{game.awayTeam} Batting</h4>
                <div className="overflow-x-auto">
                    <table className="w-full small-text">
                        <thead className="bg-slate-50 border-b-2">
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
                            {gameData.awayHitters.map((p) => <HitterRow key={p.playerId} player={p} />)}
                            <tr className="bg-blue-50 font-bold">
                                <td className="px-3 py-2">Team Totals</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.ab}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.h}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.r}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.rbi}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.hr}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.doubles}</td>
                                <td className="px-2 py-2 text-center">{gameData.awayHittingTotals.triples}</td>
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
                        <thead className="bg-slate-50 border-b-2">
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
                            {gameData.homeHitters.map((p) => <HitterRow key={p.playerId} player={p} />)}
                            <tr className="bg-blue-50 font-bold">
                                <td className="px-3 py-2">Team Totals</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.ab}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.h}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.r}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.rbi}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.hr}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.doubles}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.triples}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.bb}</td>
                                <td className="px-2 py-2 text-center">{gameData.homeHittingTotals.so}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            {/* Pitching */}
            <div className="p-6 bg-slate-50">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Away Pitchers */}
                    <div>
                        <h4 className="subsection-title font-bold mb-3">{game.awayTeam} Pitching</h4>
                        <div className="overflow-x-auto">
                            <table className="w-full small-text bg-white rounded">
                                <thead className="bg-slate-50 border-b-2">
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
                                    {gameData.awayPitchers.map((p) => <PitcherRow key={p.playerId} pitcher={p} />)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    {/* Home Pitchers */}
                    <div>
                        <h4 className="subsection-title font-bold mb-3">{game.homeTeam} Pitching</h4>
                        <div className="overflow-x-auto">
                            <table className="w-full small-text bg-white rounded">
                                <thead className="bg-slate-50 border-b-2">
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
                                    {gameData.homePitchers.map((p) => <PitcherRow key={p.playerId} pitcher={p} />)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            {/* Pitch Data */}
            {game.pitchData && Object.keys(game.pitchData).length > 0 && (
                <div className="p-6 border-t">
                    <h4 className="subsection-title font-bold mb-3">Pitch Data</h4>
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                        {pitchDataGroups.map((group) => (
                            <section key={group.team} className={group.team === 'other' ? 'xl:col-span-2' : ''}>
                                <div className="flex items-center justify-between gap-3 mb-3 border-b pb-2">
                                    <span className="font-bold body-text">{group.label}</span>
                                    <span className="small-text text-slate-500 whitespace-nowrap">{group.totalPitches} pitches</span>
                                </div>
                                <div className="space-y-3">
                                    {group.items.map(item => <PitchDataCard key={item.pid} item={item} />)}
                                </div>
                            </section>
                        ))}
                    </div>
                </div>
            )}
        </>
    );

    const LineupsTab = () => {
        if (!game.lineups) {
            return (
                <div className="p-8 text-center text-slate-500 body-text">
                    Starting lineup data not available for this game
                </div>
            );
        }
        
        const LineupTable = ({ lineup, team }) => {
            const sortedLineup = [...lineup].sort((a, b) => a.slot - b.slot);
            const startingPitcher = sortedLineup.find(player => player.slot === 0 && player.position === 'P');
            const battingOrder = sortedLineup.filter(player => !(player.slot === 0 && player.position === 'P'));
            return (
            <div>
                <h4 className="subsection-title font-bold mb-3">{team} Lineup</h4>
                {startingPitcher && (
                    <div className="mb-3 flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                        <div>
                            <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Starting pitcher</div>
                            <div className="body-text font-semibold text-slate-800">
                                <PlayerLink playerId={startingPitcher.playerId} name={startingPitcher.name} />
                            </div>
                        </div>
                        <span className="px-2 py-1 bg-white rounded font-semibold text-slate-700 border border-slate-200">
                            {startingPitcher.position}
                        </span>
                    </div>
                )}
                <div className="bg-white rounded-lg overflow-hidden">
                    <table className="w-full small-text">
                        <thead className="bg-slate-50 border-b-2">
                            <tr>
                                <th className="px-3 py-2 text-center">#</th>
                                <th className="px-3 py-2 text-left">Player</th>
                                <th className="px-3 py-2 text-center">Position</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {battingOrder.map((player) => (
                                <tr key={player.playerId} className="hover:bg-blue-50">
                                    <td className="px-3 py-2 text-center font-bold text-blue-600">{player.slot}</td>
                                    <td className="px-3 py-2">
                                        <div className="flex items-center gap-2">
                                            <PlayerLink playerId={player.playerId} name={player.name} />
                                            {player.jerseyNumber && <button className="text-xs text-slate-400 hover:text-blue-600 hover:underline" onClick={(e) => { e.stopPropagation(); window.__navigateTab('trivia', 'jerseys'); if (onClose) onClose(); }}>#{player.jerseyNumber}</button>}
                                        </div>
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                        <span className="px-2 py-1 bg-slate-100 rounded font-semibold">
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
        };
        
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
        // Derive substitutions from batting/pitching data if PBP parser didn't find any
        const derivedSubs = useMemo(() => {
            if (game.substitutions && game.substitutions.length > 0) return game.substitutions;
            const subs = [];
            ['away', 'home'].forEach(side => {
                const team = side === 'away' ? game.awayTeam : game.homeTeam;
                (game.batters?.[side] || []).forEach(p => {
                    if (p.isStarter) return;
                    const pos = p.position || '';
                    const type = pos === 'PH' ? 'pinch_hit' : pos === 'PR' ? 'pinch_run' : pos === 'P' ? 'pitching_change' : 'defensive_sub';
                    subs.push({ type, playerIn: p.name, playerOut: '', position: pos, inning: 0, half: side === 'away' ? 'top' : 'bottom', text: `${p.name} entered as ${pos} (${team})` });
                });
                (game.pitchers?.[side] || []).forEach((p, i) => {
                    if (i === 0) return; // starter
                    subs.push({ type: 'pitching_change', playerIn: p.name, playerOut: '', position: 'P', inning: 0, half: side === 'away' ? 'top' : 'bottom', text: `${p.name} entered to pitch (${team})` });
                });
            });
            return subs;
        }, [game]);

        if (!derivedSubs || derivedSubs.length === 0) {
            return (
                <div className="p-8 text-center text-slate-500 body-text">
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
                    {derivedSubs.map((sub, idx) => (
                        <div key={`sub-${idx}-${sub.inning}-${sub.half}`} className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-blue-400 hover:shadow-md transition-all">
                            <div className="flex items-start gap-3">
                                <span className="text-2xl">{getSubIcon(sub.type)}</span>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-bold">
                                            {sub.half.toUpperCase()} {sub.inning}
                                        </span>
                                        <span className="body-text font-bold text-slate-700">
                                            {getSubLabel(sub.type)}
                                        </span>
                                    </div>
                                    <div className="body-text text-slate-800">
                                        {sub.playerIn && sub.playerOut ? (
                                            <>
                                                <span className="font-semibold text-green-600">{sub.playerIn}</span>
                                                {' '}replaces{' '}
                                                <span className="font-semibold text-red-600">{sub.playerOut}</span>
                                                {sub.position && <span className="text-slate-500"> at {sub.position}</span>}
                                            </>
                                        ) : (
                                            <span className="text-slate-600">{sub.text}</span>
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
                <div className="p-8 text-center text-slate-500 body-text">
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
                    {sortedInnings.map((inning) => {
                        const isFocused = focusInning && String(focusInning.half) === String(inning.half) && Number(focusInning.inning) === Number(inning.inning);
                        return (
                        <div id={`pbp-${game.gameId}-${inning.half}-${inning.inning}`} key={`${inning.half}-${inning.inning}`} className={`bg-white rounded-lg shadow-sm overflow-hidden scroll-mt-20 ${isFocused ? 'ring-2 ring-blue-500 ring-offset-2' : ''}`}>
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
                                    <div key={`play-${inning.inning}-${inning.half}-${playIdx}`} className={`p-3 hover:bg-blue-50 ${
                                        play.isHomeRun ? 'bg-orange-50' : 
                                        play.isStrikeout ? 'bg-red-50' : 
                                        play.isStolenBase ? 'bg-green-50' :
                                        play.isCaughtStealing ? 'bg-red-50' :
                                        ''
                                    }`}>
                                        <div className="flex items-start gap-3">
                                            <div className="text-center min-w-12">
                                                <div className="text-xs font-bold text-slate-500">
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
                                                    <span className="font-semibold text-slate-900">{play.batter}</span>
                                                    {' '}
                                                    <span className="text-slate-600">
                                                        {play.description}
                                                    </span>
                                                </div>
                                                <div className="small-text text-slate-500 mt-1">
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
                        );
                    })}
                </div>
            </div>
        );
    };
    
    return (
        <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div className="bg-white rounded-lg shadow-lg w-full max-h-[90vh] flex flex-col overflow-hidden" style={{ maxWidth: 'min(72rem, 95vw)' }} onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className={`p-6 border-b ${game.gameType === 'spring' ? 'bg-gradient-to-r from-green-600 to-green-700' : 'bg-gradient-to-r from-blue-600 to-blue-700'} text-white flex-shrink-0`}>
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                            <h3 className="section-title font-bold flex flex-wrap items-center gap-2">
                                <TeamToken code={game.awayTeam} logoSize={26} />
                                <span className="text-white/70">@</span>
                                <TeamToken code={game.homeTeam} logoSize={26} />
                            </h3>
                            {game.gameType === 'spring' && <span className="px-2 py-0.5 bg-white/20 text-white text-xs font-semibold rounded">Spring Training</span>}
                            {game.gameType === 'postseason' && <span className="px-2 py-0.5 bg-yellow-400/30 text-white text-xs font-semibold rounded">Postseason</span>}
                        </div>
                        <button onClick={onClose} className="text-white hover:text-slate-200 text-2xl leading-none">&times;</button>
                    </div>
                    <div className="flex items-center gap-4 body-text text-blue-100">
                        <span>{game.date}</span>
                        <span>•</span>
                        <span>{game.startTime}</span>
                        <span>•</span>
                        <span className="font-mono text-2xl text-white font-bold">{game.score}</span>
                    </div>
                    <div className="body-text text-blue-100 mt-2">
                        📍 <button className="hover:underline hover:text-white" onClick={() => { if (window.__navigateTab) window.__navigateTab('venues'); if (onClose) onClose(); }}>{game.venue}</button>
                        {game.attendance > 0 && <> • 👥 {game.attendance.toLocaleString()} fans</>}
                        {game.gameLength && <> • ⏱️ {game.gameLength}</>}
                    </div>
                    {/* Weather and Temperature */}
                    {game.weather && (
                        <div className="body-text text-blue-100 mt-1">
                            <span>🌤️ {game.weather}</span>
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
                
                {/* Scrollable body */}
                <div className="overflow-y-auto flex-1 min-h-0">
                {/* Game Context Section */}
                <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
                    {gameStoryItems.length > 0 && (
                        <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
                            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-3">
                                <div>
                                    <h5 className="small-text font-bold text-slate-700 uppercase tracking-wide">Game recap</h5>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
                                {gameStoryItems.map((item, idx) => {
                                    const colorClass =
                                        item.color === 'red' ? 'border-red-200 bg-red-50 text-red-800' :
                                        item.color === 'orange' ? 'border-orange-200 bg-orange-50 text-orange-800' :
                                        item.color === 'amber' ? 'border-amber-200 bg-amber-50 text-amber-800' :
                                        item.color === 'purple' ? 'border-purple-200 bg-purple-50 text-purple-800' :
                                        item.color === 'green' ? 'border-emerald-200 bg-emerald-50 text-emerald-800' :
                                        item.color === 'slate' ? 'border-slate-200 bg-slate-50 text-slate-800' :
                                        'border-blue-200 bg-blue-50 text-blue-800';
                                    return (
                                        <div key={`story-${idx}`} className={`rounded-lg border p-3 ${colorClass}`}>
                                            <div className="small-text font-bold uppercase tracking-wide opacity-75">{item.label}</div>
                                            <div className="text-lg font-bold mt-1">{item.value}</div>
                                            {item.details ? (
                                                <div className="small-text mt-1 opacity-80 space-y-0.5">
                                                    {item.details.map((detail, detailIdx) => (
                                                        <div key={`story-detail-${idx}-${detailIdx}`} className="break-words">{detail}</div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <div className="small-text mt-1 opacity-80 break-words">{item.detail}</div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Linescore */}
                    {game.linescore && (
                        <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
                            <h5 className="small-text font-bold mb-3 text-slate-700">📊 Line Score</h5>
                            <div className="overflow-x-auto">
                                <table className="w-full text-center small-text" style={{ tableLayout: 'fixed' }}>
                                    <thead className="bg-slate-50">
                                        <tr>
                                            <th className="py-2 text-left" style={{ width: '15%' }}>Team</th>
                                            {Array.from({ length: Math.max(game.linescore.away?.innings?.length || 9, game.linescore.home?.innings?.length || 9, 9) }, (_, i) => (
                                                <th key={`inning-${i}`} className="py-2">{i + 1}</th>
                                            ))}
                                            <th className="py-2 font-bold border-l-2">R</th>
                                            <th className="py-2 font-bold">H</th>
                                            <th className="py-2 font-bold">E</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="border-b">
                                            <td className="px-3 py-2 text-left font-semibold"><TeamToken code={game.awayTeam} logoSize={18} /></td>
                                            {Array.from({ length: Math.max(game.linescore.away?.innings?.length || 9, game.linescore.home?.innings?.length || 9, 9) }, (_, i) => (
                                                <td key={`away-inning-${i}`} className="px-2 py-2">
                                                    {game.linescore.away?.innings?.[i] !== undefined ? game.linescore.away.innings[i] : '-'}
                                                </td>
                                            ))}
                                            <td className="px-3 py-2 font-bold border-l-2">{game.linescore.away?.runs || 0}</td>
                                            <td className="px-3 py-2 font-bold">{game.linescore.away?.hits || 0}</td>
                                            <td className="px-3 py-2 font-bold">{game.linescore.away?.errors || 0}</td>
                                        </tr>
                                        <tr>
                                            <td className="px-3 py-2 text-left font-semibold"><TeamToken code={game.homeTeam} logoSize={18} /></td>
                                            {Array.from({ length: Math.max(game.linescore.away?.innings?.length || 9, game.linescore.home?.innings?.length || 9, 9) }, (_, i) => (
                                                <td key={`home-inning-${i}`} className="px-2 py-2">
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
                            <h5 className="small-text font-bold mb-3 text-slate-700">👨‍⚖️ Umpires</h5>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                                {['hp', '1b', '2b', '3b', 'lf', 'rf'].map(pos => game.umpires[pos] ? (
                                    <div key={pos} className="small-text">
                                        <span className="text-slate-500">{pos.toUpperCase()}:</span>{' '}
                                        <button className="font-medium text-blue-600 hover:underline" onClick={() => {
                                            window._pendingUmpireSearch = game.umpires[pos];
                                            if (window.__navigateTab) window.__navigateTab('trivia', 'umpires');
                                            if (onClose) onClose();
                                        }}>{game.umpires[pos]}</button>
                                    </div>
                                ) : null)}
                            </div>
                        </div>
                    )}

                    {/* Key Plays (Home Runs) */}
                    {game.keyPlays && game.keyPlays.length > 0 && (
                        <div className="bg-white rounded-lg p-4 shadow-sm mb-4">
                            <h5 className="small-text font-bold mb-3 text-slate-700">⚾ Key Plays</h5>
                            <div className="space-y-2">
                                {game.keyPlays.map((play, idx) => (
                                    <div key={`keyplay-${play.inning}-${play.batter}-${idx}`} className="flex items-start gap-2 p-2 bg-orange-50 rounded border-l-4 border-orange-400">
                                        <span className="text-lg">
                                            {play.type === 'grand_slam' ? '💣' : '🏠'}
                                        </span>
                                        <div className="flex-1">
                                            <div className="body-text font-semibold">
                                                {play.batter} {play.type === 'grand_slam' ? 'Grand Slam' : 'Home Run'}
                                            </div>
                                            <div className="small-text text-slate-600">
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
                                <h5 className="small-text font-bold mb-3 text-slate-700">🏆 Milestones Achieved</h5>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {gameMilestones.map((milestone, idx) => (
                                        <div key={milestone.id || `${milestone.type}-${milestone.gameId}-${idx}`} className="bg-white rounded-lg p-3 shadow-sm border-l-4 border-purple-400">
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
                                                    <div className="body-text font-bold text-slate-900">{milestone.type}</div>
                                                    <div className="body-text text-slate-700 mt-1">{milestone.player}</div>
                                                    {milestone.detail && (
                                                        <div className="small-text text-slate-600 mt-1">{milestone.detail}</div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })()}

                    {/* Career Milestones from this game */}
                    {careerFirsts && careerFirsts.length > 0 && (
                        <div className="mt-4 bg-gradient-to-r from-amber-50 to-yellow-50 rounded-lg p-4 shadow-sm border border-amber-200">
                            <h5 className="small-text font-bold mb-3 text-amber-800">⭐ Career Milestones Witnessed</h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {careerFirsts.map((first, idx) => (
                                    <div key={`career-${first.milestone}-${first.player || idx}`} className="bg-white rounded-lg p-3 shadow-sm border-l-4 border-amber-400">
                                        <div className="flex items-start gap-2">
                                            <span className="text-xl">
                                                {first.milestone.includes('Home Run') ? '💣' :
                                                 first.milestone.includes('Hit') ? '🎯' :
                                                 first.milestone.includes('RBI') ? '💪' :
                                                 first.milestone.includes('Double') ? '2️⃣' :
                                                 first.milestone.includes('Triple') ? '3️⃣' :
                                                 first.milestone.includes('Walk') ? '🚶' :
                                                 first.milestone.includes('Stolen') ? '🏃' :
                                                 first.milestone.includes('Win') ? '🏆' :
                                                 first.milestone.includes('Save') ? '💾' :
                                                 first.milestone.includes('Strikeout') ? 'K' :
                                                 '⭐'}
                                            </span>
                                            <div className="flex-1">
                                                <div className="body-text font-bold text-amber-800">{first.milestone}</div>
                                                <div className="body-text text-slate-700 mt-1">{first.player_name}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
                
                {/* Tab Navigation */}
                <div className="border-b bg-slate-50 sticky top-0 z-10">
                    <div className="flex gap-1 px-6">
                        {['boxscore', 'lineups', 'substitutions', 'playbyplay', 'context'].map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-4 sm:px-6 py-3 body-text font-semibold transition-all whitespace-nowrap ${
                                    activeTab === tab
                                        ? 'bg-white text-blue-600 border-b-4 border-blue-600'
                                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                                }`}
                            >
                                {tab === 'boxscore' ? 'Box Score' :
                                 tab === 'lineups' ? 'Lineups' :
                                 tab === 'substitutions' ? 'Substitutions' :
                                 tab === 'playbyplay' ? 'Play-by-Play' :
                                 `Context${(careerFirsts?.length || 0) + (allTimePassings?.length || 0) + (debuts?.length || 0) + (finalGames?.length || 0) + (badges?.length || 0) > 0 ? ' ✦' : ''}`}
                            </button>
                        ))}
                    </div>
                </div>
                
                {/* Tab Content */}
                <div>
                    {activeTab === 'boxscore' && <BoxScoreTab />}
                    {activeTab === 'lineups' && <LineupsTab />}
                    {activeTab === 'substitutions' && <SubstitutionsTab />}
                    {activeTab === 'playbyplay' && <PlayByPlayTab />}
                    {activeTab === 'context' && (
                        <div className="p-6 space-y-6">
                            {/* Game Superlatives */}
                            {(gameData.fastestPitch || gameData.hardestHit || showMostKsHighlight) && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">Game Highlights</h4>
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                        {gameData.fastestPitch && (
                                            <div className="bg-red-50 rounded-lg p-3 border border-red-200">
                                                <div className="text-xs text-red-600 font-semibold">Fastest Pitch</div>
                                                <div className="text-lg font-bold text-red-700">{gameData.fastestPitch.speed} mph</div>
                                                <div className="text-xs text-slate-600">{gameData.fastestPitch.name}</div>
                                            </div>
                                        )}
                                        {gameData.hardestHit && (
                                            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                                                <div className="text-xs text-blue-600 font-semibold">Hardest Hit</div>
                                                <div className="text-lg font-bold text-blue-700">{gameData.hardestHit.velo} mph</div>
                                                <div className="text-xs text-slate-600">{formatHardestHitDetail(gameData.hardestHit)}</div>
                                            </div>
                                        )}
                                        {showMostKsHighlight && (
                                            <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
                                                <div className="text-xs text-orange-600 font-semibold">Most Strikeouts</div>
                                                <div className="text-lg font-bold text-orange-700">{gameData.mostKs.so} K</div>
                                                <div className="text-xs text-slate-600">{gameData.mostKs.name}</div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {game.absChallenges?.reviews?.length > 0 && (() => {
                                const reviews = game.absChallenges.reviews;
                                // Derive team summaries from challengeTeam field
                                const awayChallenges = reviews.filter(r => r.challengeTeam === 'away');
                                const homeChallenges = reviews.filter(r => r.challengeTeam === 'home');
                                const awayOvt = awayChallenges.filter(r => r.overturned).length;
                                const homeOvt = homeChallenges.filter(r => r.overturned).length;
                                const awayFailed = awayChallenges.length - awayOvt;
                                const homeFailed = homeChallenges.length - homeOvt;
                                // Remaining: start with 2, lose 1 per failed challenge
                                const awayLeft = Math.max(0, 2 - awayFailed);
                                const homeLeft = Math.max(0, 2 - homeFailed);
                                return (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">⚖️ ABS Challenges</h4>
                                    <div className="grid grid-cols-2 gap-3 mb-3">
                                        <div className="bg-slate-50 rounded-lg p-3 text-sm">
                                            <div className="font-semibold mb-1"><TeamToken code={game.awayTeam} logoSize={18} /></div>
                                            <div className="flex gap-3">
                                                <span className="text-green-600">✓ {awayOvt}</span>
                                                <span className="text-red-600">✗ {awayFailed}</span>
                                                <span className="text-slate-500">{awayLeft} left</span>
                                            </div>
                                        </div>
                                        <div className="bg-slate-50 rounded-lg p-3 text-sm">
                                            <div className="font-semibold mb-1"><TeamToken code={game.homeTeam} logoSize={18} /></div>
                                            <div className="flex gap-3">
                                                <span className="text-green-600">✓ {homeOvt}</span>
                                                <span className="text-red-600">✗ {homeFailed}</span>
                                                <span className="text-slate-500">{homeLeft} left</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        {reviews.sort((a, b) => a.inning - b.inning || (a.half === 'top' ? 0 : 1) - (b.half === 'top' ? 0 : 1)).map((r, i) => (
                                            <div key={`abs-${i}`} className={`text-sm p-3 rounded-lg ${r.overturned ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                                                <div className="flex items-center justify-between">
                                                    <span className={`font-bold ${r.overturned ? 'text-green-700' : 'text-red-700'}`}>
                                                        {r.overturned ? '✓ Overturned' : '✗ Upheld'}
                                                    </span>
                                                    <span className="text-xs text-slate-500">{r.half === 'top' ? 'Top' : 'Bot'} {r.inning} • {r.count} count</span>
                                                </div>
                                                <div className="mt-1">
                                                    <span className="font-medium">{r.challengePlayer || r.batter}</span>
                                                    {' challenged call'}
                                                    {r.pitchType && <span className="text-slate-500"> ({r.pitchType})</span>}
                                                    {r.edgeDistance != null && <span className="text-xs text-slate-400 ml-2">edge: {r.edgeDistance.toFixed(3)}</span>}
                                                </div>
                                                <div className="text-xs text-slate-500 mt-0.5">{r.batter} batting vs {r.pitcher}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                );
                            })()}

                            {badges && badges.length > 0 && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">🏅 Badges Earned</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {badges.map((b, i) => (
                                            <span key={`badge-${i}`} className="px-3 py-1.5 bg-blue-50 text-blue-800 rounded-lg text-sm font-medium border border-blue-200" title={b.title}>
                                                {b.text}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {careerBookendItems.length > 0 && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">Career Bookends</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        {(debuts || []).map((debut, i) => (
                                            <div key={`context-debut-${debut.playerId || debut.player}-${i}`} className="flex items-start gap-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                                                <span className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-emerald-100 text-emerald-700 text-sm font-bold flex-shrink-0">MLB</span>
                                                <div className="min-w-0">
                                                    <div className="font-semibold body-text">
                                                        <PlayerLink playerId={debut.playerId} name={debut.player} /> — MLB debut{debut.team ? ` with ${debut.team}` : ''}
                                                    </div>
                                                    <div className="small-text text-slate-600 mt-0.5">{formatCareerEventPerformance(debut)}</div>
                                                    {debut.opponent && <div className="small-text text-slate-500 mt-0.5">vs {debut.opponent}</div>}
                                                </div>
                                            </div>
                                        ))}
                                        {(finalGames || []).map((finalGame, i) => (
                                            <div key={`context-final-${finalGame.playerId || finalGame.player}-${i}`} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                                                <span className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-slate-200 text-slate-700 text-xs font-bold flex-shrink-0">FINAL</span>
                                                <div className="min-w-0">
                                                    <div className="font-semibold body-text">
                                                        <PlayerLink playerId={finalGame.playerId} name={finalGame.player} /> — Final MLB game{finalGame.team ? ` with ${finalGame.team}` : ''}
                                                    </div>
                                                    <div className="small-text text-slate-600 mt-0.5">{formatCareerEventPerformance(finalGame)}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {careerFirsts && careerFirsts.length > 0 && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">⭐ Career Milestones</h4>
                                    <div className="space-y-2">
                                        {careerFirsts.map((first, i) => (
                                            <div key={`first-${i}`} className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                                                <span className="text-xl">⭐</span>
                                                <div>
                                                    <div className="font-semibold body-text">
                                                        <PlayerLink playerId={first.player_id} name={first.player_name} /> — {first.milestone}
                                                    </div>
                                                    {first.opponent && <div className="small-text text-slate-600">vs {first.opponent}</div>}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {allTimePassings && allTimePassings.length > 0 && (
                                <div>
                                    <h4 className="subsection-title font-bold mb-3">📜 All-Time List Passings</h4>
                                    <div className="space-y-2">
                                        {allTimePassings.map((passing, i) => (
                                            <div key={`passing-${i}`} className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                                                <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-white text-sm font-bold flex-shrink-0 ${passing.new_rank <= 10 ? 'bg-gradient-to-br from-yellow-400 to-amber-500' : 'bg-gradient-to-br from-purple-500 to-violet-600'}`}>
                                                    #{passing.new_rank}
                                                </span>
                                                <div>
                                                    <div className="font-semibold body-text">
                                                        <PlayerLink playerId={passing.player_id} name={passing.player_name} /> — #{passing.new_rank} all-time in {passing.stat_name}
                                                    </div>
                                                    <div className="small-text text-slate-600">
                                                        {passing.new_value} career {passing.stat_name.toLowerCase()}
                                                        {passing.passed_names && ` • Passed ${passing.passed_names}`}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
                </div>{/* End scrollable body */}

                {/* Footer */}
                <div className="p-3 border-t bg-slate-50 flex justify-between items-center flex-shrink-0">
                    <div className="flex items-center gap-2">
                        {onPrev && <button onClick={onPrev} className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 rounded text-sm font-medium" title="Previous game">← Prev</button>}
                        {gameIndex != null && totalGames && <span className="text-xs text-slate-500">Game {gameIndex} of {totalGames}</span>}
                        {onNext && <button onClick={onNext} className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 rounded text-sm font-medium" title="Next game">Next →</button>}
                    </div>
                    <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                    <button onClick={onClose} className="px-5 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium">
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

const PlayerTimeline = ({ playerId, playerName, playerGames, onGameClick, careerMilestones, allTimePassings, gameMilestones, debuts, finalGames }) => {
    const [showGameLog, setShowGameLog] = useState(false);
    const [sortKey, setSortKey] = useState('dateSort');
    const [sortDir, setSortDir] = useState('desc');
    const [opponentFilter, setOpponentFilter] = useState(null);
    const [showSeasons, setShowSeasons] = useState(false);

    // Get all games for this player
    const gamesForPlayer = useMemo(() => {
        return playerGames.filter(g => g.playerId === playerId).sort((a, b) => b.dateSort.localeCompare(a.dateSort));
    }, [playerId, playerGames]);

    const timelineData = useMemo(() => {
        if (gamesForPlayer.length === 0) return [];
        const byYearType = {};
        gamesForPlayer.forEach(game => {
            const year = game.dateSort.substring(0, 4);
            const isSpring = game.gameType === 'spring' || game.gameType === 'exhibition';
            const key = isSpring ? `${year}_spring` : year;
            if (!byYearType[key]) byYearType[key] = { year, isSpring, games: [] };
            byYearType[key].games.push(game);
        });
        return Object.values(byYearType).map(({ year, isSpring, games }) => {
            const aggregated = aggregateHitterStats(games)[0] || {};
            return { year, isSpring, ...aggregated };
        }).sort((a, b) => a.year !== b.year ? a.year - b.year : (a.isSpring ? -1 : 0) - (b.isSpring ? -1 : 0));
    }, [gamesForPlayer]);

    // Totals for stat cards
    const totals = useMemo(() => {
        const regGames = gamesForPlayer.filter(g => g.gameType === 'regular' || (!g.gameType));
        const agg = aggregateHitterStats(regGames)[0] || {};
        const multiHitGames = regGames.filter(g => g.h >= 3).length;
        const hrGames = regGames.filter(g => (g.hr || 0) >= 1).length;
        const multiHrGames = regGames.filter(g => (g.hr || 0) >= 2).length;
        return { ...agg, multiHitGames, hrGames, multiHrGames };
    }, [gamesForPlayer]);

    // Notable games: multi-HR, 3+ hits, HR+multi-hit, 3+ RBI, 2+ SB, 4+ R
    const notableGames = useMemo(() => {
        return gamesForPlayer.filter(g => {
            const isSpring = g.gameType === 'spring' || g.gameType === 'exhibition';
            if (isSpring) return false;
            const hr = g.hr || 0, h = g.h || 0, rbi = g.rbi || 0, sb = g.sb || 0, r = g.r || 0;
            return hr >= 2 || h >= 3 || (hr >= 1 && h >= 2) || (hr >= 1 && rbi >= 3) || rbi >= 4 || sb >= 2 || r >= 4 || g.careerHighs?.length;
        }).map(g => {
            const hr = g.hr || 0, h = g.h || 0, rbi = g.rbi || 0, sb = g.sb || 0, r = g.r || 0, bb = g.bb || 0;
            // Build compact batting line
            const parts = [`${h}-${g.ab}`];
            if (hr > 0) parts.push(`${hr} HR`);
            if (rbi > 0) parts.push(`${rbi} RBI`);
            if (r > 0) parts.push(`${r} R`);
            if (bb > 0) parts.push(`${bb} BB`);
            if (sb > 0) parts.push(`${sb} SB`);
            const line = parts.join(', ');
            // Highlight tag for the best thing about this game
            let highlight = null;
            if (hr >= 3) highlight = { label: `${hr}-HR game`, color: 'bg-red-200 text-red-800' };
            else if (hr >= 2) highlight = { label: 'Multi-HR', color: 'bg-red-100 text-red-700' };
            else if (h >= 5) highlight = { label: `${h}-hit game`, color: 'bg-emerald-100 text-emerald-700' };
            else if (h >= 4) highlight = { label: `${h}-hit game`, color: 'bg-emerald-100 text-emerald-700' };
            else if (h >= 3 && hr >= 1) highlight = { label: `${h}-hit, HR`, color: 'bg-orange-100 text-orange-700' };
            else if (h >= 3) highlight = { label: `${h}-hit game`, color: 'bg-green-100 text-green-700' };
            else if (rbi >= 5) highlight = { label: `${rbi} RBI`, color: 'bg-blue-100 text-blue-700' };
            else if (rbi >= 4) highlight = { label: `${rbi} RBI`, color: 'bg-blue-100 text-blue-700' };
            else if (hr >= 1 && rbi >= 3) highlight = { label: `HR, ${rbi} RBI`, color: 'bg-orange-100 text-orange-700' };
            else if (hr >= 1 && h >= 2) highlight = { label: `${h}-hit, HR`, color: 'bg-orange-100 text-orange-700' };
            else if (g.careerHighs?.length) highlight = { label: `Career-high ${g.careerHighs.join(', ')}`, color: 'bg-purple-100 text-purple-700' };
            else if (r >= 4) highlight = { label: `${r} runs`, color: 'bg-sky-100 text-sky-700' };
            else if (sb >= 2) highlight = { label: `${sb} SB`, color: 'bg-violet-100 text-violet-700' };
            else if (rbi >= 4) highlight = { label: `${rbi} RBI`, color: 'bg-blue-100 text-blue-700' };
            // Score for sorting (best games first)
            const score = hr * 4 + h * 1.5 + rbi * 2 + r + sb * 2 + (g.careerHighs ? 5 : 0);
            return { ...g, line, highlight, score };
        }).sort((a, b) => b.score - a.score);
    }, [gamesForPlayer]);

    // Combined milestones list
    const allMilestones = useMemo(() => {
        const toSort = (d) => { if (!d) return ''; const p = d.split('/'); return p.length === 3 ? `${p[2]}-${p[0].padStart(2,'0')}-${p[1].padStart(2,'0')}` : d; };
        const items = [];
        (debuts || []).forEach(d => items.push({ sort: toSort(d.date), badgeClass: 'bg-green-100 text-green-700', badgeText: 'DEBUT', text: `MLB Debut (${d.team})`, sub: `vs ${d.opponent || ''}`, date: d.date, gameId: d.gameId }));
        (finalGames || []).forEach(f => items.push({ sort: toSort(f.date), badgeClass: 'bg-slate-200 text-slate-700', badgeText: 'FINAL', text: `Final MLB Game (${f.team})`, date: f.date, gameId: f.gameId }));
        (gameMilestones || []).forEach(m => items.push({ sort: m._dateSort || m.date || '', badgeClass: 'bg-orange-100 text-orange-700', badgeText: m.type, text: m.detail, sub: `vs ${m.opponent}`, date: m.date, gameId: m.gameId }));
        (careerMilestones || []).forEach(m => items.push({ sort: m.date || '', badgeClass: m.category === 'first' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700', badgeText: m.category === 'first' ? 'FIRST' : 'MILESTONE', text: m.milestone, date: m.date_display || m.date, gameId: m.game_id }));
        (allTimePassings || []).forEach(p => {
            const passed = (p.passed_players || []).filter(pp => !pp.tied).map(pp => pp.name);
            const tied = (p.passed_players || []).filter(pp => pp.tied).map(pp => pp.name);
            const parts = [];
            if (passed.length) parts.push('passed ' + passed.join(', '));
            if (tied.length) parts.push('tied ' + tied.join(', '));
            items.push({ sort: p.date || '', badgeClass: 'bg-purple-100 text-purple-700', badgeText: `#${p.new_rank}`, text: parts.join(' and ') || p.milestone, sub: p.stat_name, date: p.date_display || p.date, gameId: p.game_id });
        });
        return items.sort((a, b) => (b.sort).localeCompare(a.sort));
    }, [gameMilestones, careerMilestones, allTimePassings, debuts, finalGames]);

    // Sorted game log
    const sortedGameLog = useMemo(() => {
        const filtered = opponentFilter ? gamesForPlayer.filter(g => g.opponent === opponentFilter) : gamesForPlayer;
        return [...filtered].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            const aMissing = isMissingValue(aVal);
            const bMissing = isMissingValue(bVal);
            if (aMissing && bMissing) return 0;
            if (aMissing) return 1;
            if (bMissing) return -1;
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal || '').localeCompare(String(bVal || ''));
            return sortDir === 'asc' ? result : -result;
        });
    }, [gamesForPlayer, sortKey, sortDir, opponentFilter]);

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    if (gamesForPlayer.length === 0) {
        return (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h3 className="subsection-title font-bold mb-4">📊 Player Stats</h3>
                <p className="body-text text-slate-500 text-center py-8">No games found for this player</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Stat Cards */}
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
                {[
                    { label: 'G', value: totals.games, bold: true },
                    { label: 'AVG', value: totals.avg, bold: true },
                    { label: 'H', value: totals.h },
                    { label: 'HR', value: totals.hr, color: totals.hr > 0 ? 'text-orange-600' : '' },
                    { label: 'RBI', value: totals.rbi },
                    { label: 'SB', value: totals.sb },
                    { label: 'OPS', value: totals.ops, bold: true, color: parseFloat(totals.ops) >= 0.800 ? 'text-purple-600' : '' },
                    { label: 'BB', value: totals.bb },
                ].map(s => (
                    <div key={s.label} className="bg-slate-50 rounded-lg px-3 py-2 text-center">
                        <div className={`text-lg font-bold ${s.color || 'text-slate-800'}`}>{s.value}</div>
                        <div className="text-[10px] uppercase font-semibold text-slate-400">{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Notable Games */}
            {notableGames.length > 0 && (
                <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-2">Notable Games ({notableGames.length})</h4>
                    <div className="space-y-0.5">
                        {notableGames.map((g, i) => (
                            <button key={i} onClick={() => onGameClick && onGameClick(g.gameId)} className="w-full flex items-center gap-2 text-sm px-3 py-1.5 rounded hover:bg-slate-50 text-left transition-colors">
                                {g.highlight && <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 ${g.highlight.color}`}>{g.highlight.label}</span>}
                                <span className="text-slate-600 text-xs">{g.line}</span>
                                <span className="text-slate-400 text-xs ml-auto shrink-0">vs {g.opponent} · {g.date}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Milestones */}
            {allMilestones.length > 0 && (
                <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-2">Milestones ({allMilestones.length})</h4>
                    <div className="space-y-1">
                        {allMilestones.map((m, i) => (
                            <button key={i} onClick={() => onGameClick && onGameClick(m.gameId)} className="w-full flex items-center gap-2 text-sm px-3 py-1.5 rounded hover:bg-slate-50 text-left transition-colors">
                                <span className="text-slate-400 text-xs w-20 shrink-0">{m.date}</span>
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 ${m.badgeClass}`}>{m.badgeText}</span>
                                <span className="font-medium truncate">{m.text}</span>
                                {m.sub && <span className="text-slate-400 text-xs ml-auto shrink-0">{m.sub}</span>}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Season Breakdown (collapsible) */}
            {timelineData.length > 0 && (
                <div>
                    <button onClick={() => setShowSeasons(!showSeasons)} className="flex items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-900">
                        <span className={`transition-transform ${showSeasons ? 'rotate-90' : ''}`}>&#9656;</span>
                        Season Breakdown ({timelineData.filter(s => !s.isSpring).length} season{timelineData.filter(s => !s.isSpring).length !== 1 ? 's' : ''})
                    </button>
                    {showSeasons && (
                        <div className="mt-2 overflow-x-auto border rounded-lg">
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 border-b">
                                    <tr>
                                        {['Year','Team','G','AB','H','R','RBI','HR','2B','3B','SB','BB','SO','AVG','OPS'].map(col => (
                                            <th key={col} className="px-2 py-2 text-center text-xs font-semibold text-slate-500">{col}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {timelineData.map((s) => (
                                        <tr key={`${s.year}${s.isSpring ? '-st' : ''}`} className={s.isSpring ? 'bg-green-50' : 'hover:bg-blue-50'}>
                                            <td className="px-2 py-2 text-center font-bold text-blue-600 whitespace-nowrap">
                                                {s.year}{s.isSpring ? <span className="ml-1 text-[10px] text-green-600 font-normal">ST</span> : ''}
                                            </td>
                                            <td className="px-2 py-2 text-center text-xs">{s.team || '-'}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.games}</td>
                                            <td className="px-2 py-2 text-center">{s.ab}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.h}</td>
                                            <td className="px-2 py-2 text-center">{s.r}</td>
                                            <td className="px-2 py-2 text-center">{s.rbi}</td>
                                            <td className={`px-2 py-2 text-center ${s.hr > 0 ? 'font-bold text-orange-600' : ''}`}>{s.hr}</td>
                                            <td className="px-2 py-2 text-center">{s.doubles || 0}</td>
                                            <td className="px-2 py-2 text-center">{s.triples || 0}</td>
                                            <td className="px-2 py-2 text-center">{s.sb || 0}</td>
                                            <td className="px-2 py-2 text-center">{s.bb}</td>
                                            <td className="px-2 py-2 text-center">{s.so}</td>
                                            <td className="px-2 py-2 text-center font-bold">{s.avg}</td>
                                            <td className="px-2 py-2 text-center font-bold text-purple-600">{s.ops}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* Full Game Log (collapsible) */}
            <div>
                <button onClick={() => setShowGameLog(!showGameLog)} className="flex items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-900">
                    <span className={`transition-transform ${showGameLog ? 'rotate-90' : ''}`}>&#9656;</span>
                    Full Game Log ({gamesForPlayer.length} game{gamesForPlayer.length !== 1 ? 's' : ''})
                </button>
                {showGameLog && (
                    <div className="mt-2">
                        <div className="text-sm text-slate-500 mb-2 flex items-center gap-2">
                            {opponentFilter && (
                                <button onClick={() => setOpponentFilter(null)} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium hover:bg-blue-200">
                                    vs {opponentFilter} <span className="ml-0.5">&times;</span>
                                </button>
                            )}
                        </div>
                        <div className="overflow-x-auto border rounded-lg" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 sticky top-0">
                                    <tr>
                                        {[
                                            { key: 'dateSort', label: 'Date' },
                                            { key: 'opponent', label: 'vs' },
                                            { key: 'ab', label: 'AB' },
                                            { key: 'h', label: 'H' },
                                            { key: 'r', label: 'R' },
                                            { key: 'rbi', label: 'RBI' },
                                            { key: 'hr', label: 'HR' },
                                            { key: 'bb', label: 'BB' },
                                            { key: 'so', label: 'SO' },
                                            { key: 'sb', label: 'SB' },
                                        ].map(col => (
                                            <th key={col.key} onClick={() => handleSort(col.key)}
                                                className="px-3 py-2 text-left font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 whitespace-nowrap text-xs">
                                                {col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {sortedGameLog.map((game) => {
                                        const isMultiHit = game.h >= 2;
                                        const isHR = game.hr > 0;
                                        return (
                                            <tr key={`${game.date}-${game.opponent}-${game.team}`} className={`hover:bg-blue-50 cursor-pointer ${isHR ? 'bg-orange-50' : isMultiHit ? 'bg-green-50' : ''}`} onClick={() => onGameClick && onGameClick(game.gameId)}>
                                                <td className="px-3 py-1.5 whitespace-nowrap font-medium text-xs">
                                                    <div className="flex items-center gap-1">
                                                        {game.date}
                                                        {game.careerHighs?.length > 0 && <span className="px-1 py-0.5 rounded text-[9px] font-semibold bg-purple-100 text-purple-700" title={`Career-high ${game.careerHighs.join(', ')}`}>CH</span>}
                                                    </div>
                                                </td>
                                                <td className="px-3 py-1.5"><button className="text-blue-600 hover:underline text-xs" onClick={(e) => { e.stopPropagation(); setOpponentFilter(opponentFilter === game.opponent ? null : game.opponent); }}>{game.opponent}</button></td>
                                                <td className="px-3 py-1.5">{game.ab}</td>
                                                <td className={`px-3 py-1.5 ${isMultiHit ? 'font-bold text-green-600' : ''}`}>{game.h}</td>
                                                <td className="px-3 py-1.5">{game.r}</td>
                                                <td className="px-3 py-1.5">{game.rbi}</td>
                                                <td className={`px-3 py-1.5 ${isHR ? 'font-bold text-orange-600' : ''}`}>{game.hr || 0}</td>
                                                <td className="px-3 py-1.5">{game.bb}</td>
                                                <td className="px-3 py-1.5">{game.so}</td>
                                                <td className="px-3 py-1.5">{game.sb || 0}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const PitcherTimeline = ({ playerId, playerName, pitcherGames, onGameClick, careerMilestones, allTimePassings, gameMilestones, debuts, finalGames }) => {
    const [showGameLog, setShowGameLog] = useState(false);
    const [sortKey, setSortKey] = useState('dateSort');
    const [sortDir, setSortDir] = useState('desc');
    const [opponentFilter, setOpponentFilter] = useState(null);
    const [showSeasons, setShowSeasons] = useState(false);

    // Get all games for this pitcher with derived fields
    const gamesForPitcher = useMemo(() => {
        return pitcherGames.filter(g => g.playerId === playerId).map(g => ({
            ...g,
            ip: `${Math.floor(g.outs / 3)}.${g.outs % 3}`,
            decision: g.wins ? 'W' : g.losses ? 'L' : g.saves ? 'S' : '',
        })).sort((a, b) => b.dateSort.localeCompare(a.dateSort));
    }, [playerId, pitcherGames]);

    const timelineData = useMemo(() => {
        if (gamesForPitcher.length === 0) return [];
        const byYearType = {};
        gamesForPitcher.forEach(game => {
            const year = game.dateSort.substring(0, 4);
            const isSpring = game.gameType === 'spring' || game.gameType === 'exhibition';
            const key = isSpring ? `${year}_spring` : year;
            if (!byYearType[key]) byYearType[key] = { year, isSpring, games: [] };
            byYearType[key].games.push(game);
        });
        return Object.values(byYearType).map(({ year, isSpring, games }) => {
            const aggregated = aggregatePitcherStats(games)[0] || {};
            return { year, isSpring, ...aggregated };
        }).sort((a, b) => a.year !== b.year ? a.year - b.year : (a.isSpring ? -1 : 0) - (b.isSpring ? -1 : 0));
    }, [gamesForPitcher]);

    // Totals for stat cards (regular season only, matching the table default)
    const totals = useMemo(() => {
        const regGames = gamesForPitcher.filter(g => g.gameType === 'regular' || (!g.gameType));
        const agg = aggregatePitcherStats(regGames)[0] || {};
        const totalOuts = regGames.reduce((s, g) => s + (g.outs || 0), 0);
        const innings = totalOuts / 3;
        const totalER = regGames.reduce((s, g) => s + (g.er || 0), 0);
        const totalH = regGames.reduce((s, g) => s + (g.h || 0), 0);
        const totalBB = regGames.reduce((s, g) => s + (g.bb || 0), 0);
        const era = innings > 0 ? ((totalER * 9) / innings).toFixed(2) : '-';
        const whip = innings > 0 ? ((totalH + totalBB) / innings).toFixed(3) : '-';
        const ip = `${Math.floor(innings)}.${totalOuts % 3}`;
        return { ...agg, era, whip, ip };
    }, [gamesForPitcher]);

    // Notable games: 6+ K, QS, W, SV, low-hit games
    const notableGames = useMemo(() => {
        return gamesForPitcher.filter(g => {
            const isSpring = g.gameType === 'spring' || g.gameType === 'exhibition';
            const ipNum = parseFloat(g.ip);
            return !isSpring && (g.so >= 6 || (ipNum >= 6 && g.er <= 3) || g.decision === 'W' || g.decision === 'S' || (ipNum >= 5 && g.h <= 2));
        }).map(g => {
            const tags = [];
            const ipNum = parseFloat(g.ip);
            if (g.so >= 10) tags.push({ label: `${g.so} K`, color: 'bg-red-100 text-red-700' });
            else if (g.so >= 6) tags.push({ label: `${g.so} K`, color: 'bg-orange-100 text-orange-700' });
            if (ipNum >= 6 && g.er <= 3) tags.push({ label: 'QS', color: 'bg-blue-100 text-blue-700' });
            if (g.decision === 'W') tags.push({ label: 'W', color: 'bg-green-100 text-green-700' });
            if (g.decision === 'S') tags.push({ label: 'SV', color: 'bg-sky-100 text-sky-700' });
            if (ipNum >= 5 && g.h <= 2) tags.push({ label: `${g.h}H`, color: 'bg-violet-100 text-violet-700' });
            return { ...g, tags };
        });
    }, [gamesForPitcher]);

    // Combined milestones list
    const allMilestones = useMemo(() => {
        const toSort = (d) => { if (!d) return ''; const p = d.split('/'); return p.length === 3 ? `${p[2]}-${p[0].padStart(2,'0')}-${p[1].padStart(2,'0')}` : d; };
        const items = [];
        (debuts || []).forEach(d => items.push({ sort: toSort(d.date), badgeClass: 'bg-green-100 text-green-700', badgeText: 'DEBUT', text: `MLB Debut (${d.team})`, sub: `vs ${d.opponent || ''}`, date: d.date, gameId: d.gameId }));
        (finalGames || []).forEach(f => items.push({ sort: toSort(f.date), badgeClass: 'bg-slate-200 text-slate-700', badgeText: 'FINAL', text: `Final MLB Game (${f.team})`, date: f.date, gameId: f.gameId }));
        (gameMilestones || []).forEach(m => items.push({ sort: m._dateSort || m.date || '', badgeClass: 'bg-orange-100 text-orange-700', badgeText: m.type, text: m.detail, sub: `vs ${m.opponent}`, date: m.date, gameId: m.gameId }));
        (careerMilestones || []).forEach(m => items.push({ sort: m.date || '', badgeClass: m.category === 'first' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700', badgeText: m.category === 'first' ? 'FIRST' : 'MILESTONE', text: m.milestone, date: m.date_display || m.date, gameId: m.game_id }));
        (allTimePassings || []).forEach(p => {
            const passed = (p.passed_players || []).filter(pp => !pp.tied).map(pp => pp.name);
            const tied = (p.passed_players || []).filter(pp => pp.tied).map(pp => pp.name);
            const parts = [];
            if (passed.length) parts.push('passed ' + passed.join(', '));
            if (tied.length) parts.push('tied ' + tied.join(', '));
            items.push({ sort: p.date || '', badgeClass: 'bg-purple-100 text-purple-700', badgeText: `#${p.new_rank}`, text: parts.join(' and ') || p.milestone, sub: p.stat_name, date: p.date_display || p.date, gameId: p.game_id });
        });
        return items.sort((a, b) => (b.sort).localeCompare(a.sort));
    }, [gameMilestones, careerMilestones, allTimePassings, debuts, finalGames]);

    // Sorted game log
    const sortedGameLog = useMemo(() => {
        const filtered = opponentFilter ? gamesForPitcher.filter(g => g.opponent === opponentFilter) : gamesForPitcher;
        return [...filtered].sort((a, b) => {
            const aVal = a[sortKey], bVal = b[sortKey];
            const aMissing = isMissingValue(aVal);
            const bMissing = isMissingValue(bVal);
            if (aMissing && bMissing) return 0;
            if (aMissing) return 1;
            if (bMissing) return -1;
            const aNum = parseFloat(String(aVal).replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(String(bVal).replace(/[^0-9.-]/g, ''));
            let result = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : String(aVal || '').localeCompare(String(bVal || ''));
            return sortDir === 'asc' ? result : -result;
        });
    }, [gamesForPitcher, sortKey, sortDir, opponentFilter]);

    const handleSort = (key) => {
        if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        else { setSortKey(key); setSortDir('desc'); }
    };

    if (gamesForPitcher.length === 0) {
        return (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h3 className="subsection-title font-bold mb-4">📊 Pitcher Stats</h3>
                <p className="body-text text-slate-500 text-center py-8">No games found for this pitcher</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Stat Cards */}
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
                {[
                    { label: 'G', value: totals.games, bold: true },
                    { label: 'W-L', value: `${totals.wins || 0}-${totals.losses || 0}`, color: (totals.wins || 0) > (totals.losses || 0) ? 'text-green-600' : '' },
                    { label: 'ERA', value: totals.era, bold: true, color: totals.era !== '-' && parseFloat(totals.era) <= 3.00 ? 'text-purple-600' : '' },
                    { label: 'IP', value: totals.ip },
                    { label: 'SO', value: totals.so, bold: true },
                    { label: 'WHIP', value: totals.whip },
                    { label: 'SV', value: totals.saves || 0 },
                    { label: 'BB', value: totals.bb },
                ].map(s => (
                    <div key={s.label} className="bg-slate-50 rounded-lg px-3 py-2 text-center">
                        <div className={`text-lg font-bold ${s.color || 'text-slate-800'}`}>{s.value}</div>
                        <div className="text-[10px] uppercase font-semibold text-slate-400">{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Notable Games */}
            {notableGames.length > 0 && (
                <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-2">Notable Games ({notableGames.length})</h4>
                    <div className="space-y-1">
                        {notableGames.map((g, i) => (
                            <button key={i} onClick={() => onGameClick && onGameClick(g.gameId)} className="w-full flex items-center gap-2 text-sm px-3 py-1.5 rounded hover:bg-slate-50 text-left transition-colors">
                                <span className="text-slate-400 text-xs w-20 shrink-0">{g.date}</span>
                                <span className="text-slate-500 w-8 shrink-0 text-xs">vs</span>
                                <span className="font-medium w-12 shrink-0">{g.opponent}</span>
                                <span className="flex gap-1 flex-wrap">
                                    {g.tags.map((t, j) => (
                                        <span key={j} className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${t.color}`}>{t.label}</span>
                                    ))}
                                </span>
                                <span className="text-slate-400 text-xs ml-auto">{g.ip} IP, {g.er} ER</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Milestones */}
            {allMilestones.length > 0 && (
                <div>
                    <h4 className="text-sm font-bold text-slate-700 mb-2">Milestones ({allMilestones.length})</h4>
                    <div className="space-y-1">
                        {allMilestones.map((m, i) => (
                            <button key={i} onClick={() => onGameClick && onGameClick(m.gameId)} className="w-full flex items-center gap-2 text-sm px-3 py-1.5 rounded hover:bg-slate-50 text-left transition-colors">
                                <span className="text-slate-400 text-xs w-20 shrink-0">{m.date}</span>
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0 ${m.badgeClass}`}>{m.badgeText}</span>
                                <span className="font-medium truncate">{m.text}</span>
                                {m.sub && <span className="text-slate-400 text-xs ml-auto shrink-0">{m.sub}</span>}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Season Breakdown (collapsible) */}
            {timelineData.length > 0 && (
                <div>
                    <button onClick={() => setShowSeasons(!showSeasons)} className="flex items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-900">
                        <span className={`transition-transform ${showSeasons ? 'rotate-90' : ''}`}>&#9656;</span>
                        Season Breakdown ({timelineData.filter(s => !s.isSpring).length} season{timelineData.filter(s => !s.isSpring).length !== 1 ? 's' : ''})
                    </button>
                    {showSeasons && (
                        <div className="mt-2 overflow-x-auto border rounded-lg">
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 border-b">
                                    <tr>
                                        {['Year','Team','G','GS','W','L','SV','IP','H','ER','BB','SO','ERA','WHIP'].map(col => (
                                            <th key={col} className="px-2 py-2 text-center text-xs font-semibold text-slate-500">{col}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {timelineData.map((s) => (
                                        <tr key={`${s.year}${s.isSpring ? '-st' : ''}`} className={s.isSpring ? 'bg-green-50' : 'hover:bg-purple-50'}>
                                            <td className="px-2 py-2 text-center font-bold text-purple-600 whitespace-nowrap">
                                                {s.year}{s.isSpring ? <span className="ml-1 text-[10px] text-green-600 font-normal">ST</span> : ''}
                                            </td>
                                            <td className="px-2 py-2 text-center text-xs">{s.team || '-'}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.games}</td>
                                            <td className="px-2 py-2 text-center">{s.gameStarts || 0}</td>
                                            <td className="px-2 py-2 text-center font-bold text-green-600">{s.wins}</td>
                                            <td className="px-2 py-2 text-center text-red-600">{s.losses}</td>
                                            <td className="px-2 py-2 text-center">{s.saves || 0}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.ip}</td>
                                            <td className="px-2 py-2 text-center">{s.h}</td>
                                            <td className="px-2 py-2 text-center">{s.er}</td>
                                            <td className="px-2 py-2 text-center">{s.bb}</td>
                                            <td className="px-2 py-2 text-center font-semibold">{s.so}</td>
                                            <td className="px-2 py-2 text-center font-bold text-purple-700">{s.era}</td>
                                            <td className="px-2 py-2 text-center font-bold">{s.whip}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* Full Game Log (collapsible) */}
            <div>
                <button onClick={() => setShowGameLog(!showGameLog)} className="flex items-center gap-2 text-sm font-bold text-slate-700 hover:text-slate-900">
                    <span className={`transition-transform ${showGameLog ? 'rotate-90' : ''}`}>&#9656;</span>
                    Full Game Log ({gamesForPitcher.length} game{gamesForPitcher.length !== 1 ? 's' : ''})
                </button>
                {showGameLog && (
                    <div className="mt-2">
                        <div className="text-sm text-slate-500 mb-2 flex items-center gap-2">
                            {opponentFilter && (
                                <button onClick={() => setOpponentFilter(null)} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium hover:bg-blue-200">
                                    vs {opponentFilter} <span className="ml-0.5">&times;</span>
                                </button>
                            )}
                        </div>
                        <div className="overflow-x-auto border rounded-lg" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 sticky top-0">
                                    <tr>
                                        {[
                                            { key: 'dateSort', label: 'Date' },
                                            { key: 'opponent', label: 'vs' },
                                            { key: 'ip', label: 'IP' },
                                            { key: 'h', label: 'H' },
                                            { key: 'er', label: 'ER' },
                                            { key: 'bb', label: 'BB' },
                                            { key: 'so', label: 'SO' },
                                            { key: 'decision', label: 'Dec' },
                                        ].map(col => (
                                            <th key={col.key} onClick={() => handleSort(col.key)}
                                                className="px-3 py-2 text-left font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 whitespace-nowrap text-xs">
                                                {col.label} {sortKey === col.key && (sortDir === 'asc' ? '↑' : '↓')}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {sortedGameLog.map((game) => {
                                        const isWin = game.decision === 'W';
                                        const isQS = parseFloat(game.ip) >= 6 && game.er <= 3;
                                        return (
                                            <tr key={`${game.date}-${game.opponent}-${game.team}`} className={`hover:bg-blue-50 cursor-pointer ${isWin ? 'bg-green-50' : isQS ? 'bg-blue-50' : ''}`} onClick={() => onGameClick && onGameClick(game.gameId)}>
                                                <td className="px-3 py-1.5 whitespace-nowrap font-medium text-xs">
                                                    <div className="flex items-center gap-1">
                                                        {game.date}
                                                        {game.careerHighs?.length > 0 && <span className="px-1 py-0.5 rounded text-[9px] font-semibold bg-purple-100 text-purple-700" title={`Career-high ${game.careerHighs.join(', ')}`}>CH</span>}
                                                    </div>
                                                </td>
                                                <td className="px-3 py-1.5"><button className="text-blue-600 hover:underline text-xs" onClick={(e) => { e.stopPropagation(); setOpponentFilter(opponentFilter === game.opponent ? null : game.opponent); }}>{game.opponent}</button></td>
                                                <td className="px-3 py-1.5 font-medium">{game.ip}</td>
                                                <td className="px-3 py-1.5">{game.h}</td>
                                                <td className="px-3 py-1.5">{game.er}</td>
                                                <td className="px-3 py-1.5">{game.bb}</td>
                                                <td className={`px-3 py-1.5 ${game.so >= 8 ? 'font-bold text-orange-600' : ''}`}>{game.so}</td>
                                                <td className={`px-3 py-1.5 font-bold ${isWin ? 'text-green-600' : game.decision === 'L' ? 'text-red-600' : game.decision === 'S' ? 'text-blue-600' : ''}`}>
                                                    {game.decision || '-'}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};


'''
