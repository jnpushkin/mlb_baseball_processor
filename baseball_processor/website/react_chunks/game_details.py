"""React app chunk: game details."""

CODE = r'''const Calendar = ({ games }) => {
    const [selectedDate, setSelectedDate] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [selectedMonthForModal, setSelectedMonthForModal] = useState(null);

    const monthNames = ['March', 'April', 'May', 'June', 'July', 'August', 'September', 'October'];
    const monthIndices = [2, 3, 4, 5, 6, 7, 8, 9];

    const gamesByMonthDay = useMemo(() => {
        const aggregated = {};
        games.forEach(game => {
            const date = new Date(game.date);
            if (isNaN(date)) return;
            const month = date.getMonth();
            const day = date.getDate();
            const key = `${month}-${day}`;
            if (!aggregated[key]) aggregated[key] = [];
            aggregated[key].push(game);
        });
        return aggregated;
    }, [games]);

    const maxGamesOnDate = useMemo(() => {
        return Math.max(...Object.values(gamesByMonthDay).map(g => g.length), 1);
    }, [gamesByMonthDay]);

    const getHeatmapColor = (gameCount) => {
        if (gameCount === 0) return 'bg-slate-50 border-slate-200';
        const intensity = Math.min(gameCount / maxGamesOnDate, 1);
        if (intensity <= 0.25) return 'bg-blue-100 border-blue-200';
        if (intensity <= 0.5) return 'bg-blue-200 border-blue-300';
        if (intensity <= 0.75) return 'bg-blue-400 border-blue-500';
        return 'bg-blue-600 border-blue-700';
    };

    const getTextColor = (gameCount) => {
        if (gameCount === 0) return 'text-slate-700';
        const intensity = Math.min(gameCount / maxGamesOnDate, 1);
        return intensity > 0.5 ? 'text-white' : 'text-slate-700';
    };

    const year = useMemo(() => {
        const currentYear = new Date().getFullYear();
        const yearsWithGames = new Set();
        games.forEach(game => {
            const date = new Date(game.date);
            if (!isNaN(date)) yearsWithGames.add(date.getFullYear());
        });
        if (yearsWithGames.size === 0) return currentYear;
        return Math.max(...yearsWithGames);
    }, [games]);

    const getCalendarDaysForMonth = (monthIndex) => {
        const firstDay = new Date(year, monthIndex, 1);
        const lastDay = new Date(year, monthIndex + 1, 0);
        const startingDayOfWeek = firstDay.getDay();
        const daysInMonth = lastDay.getDate();
        const days = [];
        for (let i = 0; i < startingDayOfWeek; i++) days.push(null);
        for (let day = 1; day <= daysInMonth; day++) {
            const key = `${monthIndex}-${day}`;
            const gamesOnDate = gamesByMonthDay[key] || [];
            days.push({ day, games: gamesOnDate, key, month: monthIndex });
        }
        return days;
    };

    const handleDateClick = (day, monthIndex) => {
        if (day && day.games.length > 0) {
            setSelectedDate(day);
            setSelectedMonthForModal(monthIndex);
            setShowModal(true);
        }
    };

    const totalStats = useMemo(() => {
        const uniqueDates = new Set();
        games.forEach(g => {
            const date = new Date(g.date);
            if (!isNaN(date)) uniqueDates.add(g.date);
        });
        return {
            totalGames: games.length,
            uniqueDates: uniqueDates.size
        };
    }, [games]);

    const MonthCalendar = ({ monthIndex }) => {
        const days = getCalendarDaysForMonth(monthIndex);
        const gamesInMonth = games.filter(g => {
            const date = new Date(g.date);
            return !isNaN(date) && date.getMonth() === monthIndex;
        }).length;

        return (
            <div className="bg-white rounded-lg border border-slate-200 p-2">
                <div className="text-center mb-2">
                    <h3 className="font-bold text-slate-800" style={{ fontSize: '13px' }}>{monthNames[monthIndices.indexOf(monthIndex)]}</h3>
                    <span className="text-slate-500" style={{ fontSize: '11px' }}>{gamesInMonth} game{gamesInMonth !== 1 ? 's' : ''}</span>
                </div>
                <div className="grid grid-cols-7 gap-0.5">
                    {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
                        <div key={`day-header-${i}`} className="text-center text-slate-500 font-medium" style={{ fontSize: '9px' }}>{day}</div>
                    ))}
                    {days.map((day, idx) => {
                        if (!day) return <div key={`empty-${idx}`} className="aspect-square" />;
                        const hasGames = day.games.length > 0;
                        const bgColor = getHeatmapColor(day.games.length);
                        const textColor = getTextColor(day.games.length);
                        return (
                            <div
                                key={`day-${day.day}`}
                                onClick={() => handleDateClick(day, monthIndex)}
                                className={`aspect-square border rounded flex items-center justify-center transition-all ${bgColor} ${hasGames ? 'cursor-pointer hover:scale-110 hover:shadow-md' : ''}`}
                                title={hasGames ? `${day.games.length} game${day.games.length > 1 ? 's' : ''}` : ''}
                            >
                                <span className={`font-medium ${textColor}`} style={{ fontSize: '10px' }}>{day.day}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    };

    return (
        <>
            <div className="bg-white rounded-lg border border-slate-200">
                <div className="p-4 border-b">
                    <div className="flex justify-between items-center">
                        <div>
                            <h2 className="section-title font-bold">📅 Season Calendar Heatmap</h2>
                            <p className="small-text text-slate-500 mt-1">
                                {totalStats.totalGames} games • {totalStats.uniqueDates} unique dates • Click any date with games for details
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="small-text text-slate-600">Legend:</span>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-slate-50 border border-slate-200 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-slate-500">0</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-slate-500">1</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-400 border border-blue-500 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-slate-500">2-3</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 bg-blue-600 border border-blue-700 rounded"></div>
                                <span style={{ fontSize: '10px' }} className="text-slate-500">4+</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="p-4">
                    <div className="grid grid-cols-4 gap-3">
                        {monthIndices.map((monthIndex) => (
                            <MonthCalendar key={monthIndex} monthIndex={monthIndex} />
                        ))}
                    </div>
                </div>
            </div>
            {showModal && selectedDate && (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                            <h3 className="section-title font-bold">{monthNames[monthIndices.indexOf(selectedMonthForModal)]} {selectedDate.day} • All Years</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedDate.games.length} game{selectedDate.games.length !== 1 ? 's' : ''} attended</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            <div className="divide-y">
                                {selectedDate.games.sort((a, b) => new Date(b.date) - new Date(a.date)).map((game) => (
                                    <div key={game.gameId} className="p-4 hover:bg-blue-50 transition-colors cursor-pointer"
                                        onClick={() => { requestGameDetails(game.gameId); setShowModal(false); }}>
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-3">
                                                <span className="body-text font-bold text-blue-600">{game.date}</span>
                                                <span className="small-text text-slate-500">{game.startTime}</span>
                                            </div>
                                            <div onClick={(e) => e.stopPropagation()}>
                                                <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4 flex-wrap">
                                            <div className="flex items-center gap-2">
                                                <span className="body-text font-semibold w-12 text-right">{game.awayTeam}</span>
                                                <span className="body-text text-slate-500">@</span>
                                                <span className="body-text font-semibold w-12">{game.homeTeam}</span>
                                            </div>
                                            <span className="font-mono body-text bg-slate-100 px-3 py-1 rounded font-bold">{game.score}</span>
                                            <span className="body-text text-slate-600">{game.venue}</span>
                                            {game.attendance > 0 && <span className="small-text text-slate-500">👥 {game.attendance.toLocaleString()}</span>}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="p-4 border-t bg-slate-50">
                            <button onClick={() => setShowModal(false)} className="px-6 py-2 bg-blue-600 text-white body-text rounded-lg hover:bg-blue-700 font-medium w-full">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

const MatchupMatrix = ({ matchupData, games }) => {
    const [selectedMatchup, setSelectedMatchup] = useState(null);
    const [showModal, setShowModal] = useState(false);

    if (!matchupData || !matchupData.teams || matchupData.teams.length === 0) {
        return <div className="bg-white rounded-lg border border-slate-200 p-6 body-text">No matchup data available</div>;
    }

    const { teams, matrix } = matchupData;

    // Calculate matchup completion stats
    const totalPossibleMatchups = 30 * 29 / 2; // 435 unique matchups for 30 MLB teams
    const seenMatchups = new Set();

    matrix.forEach((row, i) => {
        teams.forEach((opponent, j) => {
            if (i < j) {
                const count = row[opponent];
                if (count !== 'X' && count > 0) {
                    const key = [row.team, opponent].sort().join('-');
                    seenMatchups.add(key);
                }
            }
        });
    });

    const uniqueMatchupsSeen = seenMatchups.size;
    const completionPercent = Math.round((uniqueMatchupsSeen / totalPossibleMatchups) * 100);

    // Normalize team codes for matching (e.g., ATH -> OAK)
    const normalizeCode = (code) => {
        return normalizeTeamCode(code);
    };

    const handleCellClick = (team, opponent, count) => {
        if (count === 'X' || count === 0) return;
        const nTeam = normalizeCode(team);
        const nOpp = normalizeCode(opponent);
        const matchupGames = games.filter(game => {
            const home = normalizeCode(game.homeTeam);
            const away = normalizeCode(game.awayTeam);
            return (home === nTeam && away === nOpp) ||
                   (home === nOpp && away === nTeam);
        }).sort((a, b) => new Date(b.date) - new Date(a.date));
        setSelectedMatchup({ team, opponent, games: matchupGames, count });
        setShowModal(true);
    };

    return (
        <>
            <div className="bg-white rounded-lg border border-slate-200">
                <div className="p-4 border-b">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h2 className="section-title font-bold">🎯 Team Matchup Matrix</h2>
                            <p className="body-text text-slate-500 mt-1">Click any cell to see games between those teams</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="text-center px-4 py-2 bg-blue-50 rounded-lg">
                                <div className="text-xl font-bold text-blue-600">{uniqueMatchupsSeen}/{totalPossibleMatchups}</div>
                                <div className="text-xs text-slate-500">Matchups Seen</div>
                            </div>
                            <div className="text-center px-4 py-2 bg-green-50 rounded-lg">
                                <div className="text-xl font-bold text-green-600">{completionPercent}%</div>
                                <div className="text-xs text-slate-500">Complete</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="p-2">
                    <table className="w-full border-collapse" style={{ tableLayout: 'fixed' }}>
                        <thead>
                            <tr>
                                <th className="border bg-slate-100 font-bold" style={{ fontSize: '9px', padding: '2px', width: '28px' }}></th>
                                {teams.map(team => (
                                    <th key={team} className="border bg-slate-50 font-medium" style={{ fontSize: '8px', padding: '1px', width: '24px' }}>{team}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {matrix.map((row) => (
                                <tr key={row.team}>
                                    <td className="border font-bold bg-slate-100" style={{ fontSize: '8px', padding: '1px' }}>{row.team}</td>
                                    {teams.map(opponent => {
                                        const value = row[opponent];
                                        const isX = value === 'X';
                                        const hasGames = !isX && value > 0;
                                        return (
                                            <td key={opponent} onClick={() => hasGames && handleCellClick(row.team, opponent, value)} className={`border text-center ${isX ? 'bg-slate-300' : hasGames ? 'bg-blue-100 font-bold cursor-pointer hover:bg-blue-300' : 'bg-white'}`} style={{ fontSize: '9px', padding: '1px' }}>
                                                {isX ? '' : (value || '')}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="p-2 border-t bg-slate-50">
                    <div className="flex items-center gap-4 justify-center text-slate-600" style={{ fontSize: '10px' }}>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-slate-300 border rounded"></div><span>Same team</span></div>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-white border rounded"></div><span>No games</span></div>
                        <div className="flex items-center gap-1"><div className="w-4 h-4 bg-blue-100 border rounded"></div><span>Has games (click)</span></div>
                    </div>
                </div>
            </div>
            {showModal && selectedMatchup && (() => {
                // Compute record from selectedMatchup.team's perspective
                const getResult = (game) => {
                    const scoreStr = game.score || '';
                    const m = scoreStr.match(/(\w+)\s+(\d+)\s*-\s*(\d+)\s+(\w+)/);
                    let awayScore, homeScore;
                    if (m) {
                        const [, team1, s1, s2, team2] = m;
                        const nHome = normalizeCode(game.homeTeam);
                        if (normalizeCode(team2) === nHome) {
                            awayScore = parseInt(s1); homeScore = parseInt(s2);
                        } else {
                            awayScore = parseInt(s2); homeScore = parseInt(s1);
                        }
                    } else {
                        const m2 = scoreStr.match(/(\d+)\s*-\s*(\d+)/);
                        if (!m2) return null;
                        awayScore = parseInt(m2[1]); homeScore = parseInt(m2[2]);
                    }
                    if (isNaN(awayScore) || isNaN(homeScore)) return null;
                    const isHome = normalizeCode(game.homeTeam) === normalizeCode(selectedMatchup.team);
                    const teamScore = isHome ? homeScore : awayScore;
                    const oppScore = isHome ? awayScore : homeScore;
                    if (teamScore === oppScore) return { result: 'T', teamScore, oppScore };
                    return { result: teamScore > oppScore ? 'W' : 'L', teamScore, oppScore };
                };
                let wins = 0, losses = 0, ties = 0;
                selectedMatchup.games.forEach(g => {
                    const r = getResult(g);
                    if (!r) return;
                    if (r.result === 'W') wins++;
                    else if (r.result === 'L') losses++;
                    else ties++;
                });
                const recordStr = ties > 0 ? `${wins}-${losses}-${ties}` : `${wins}-${losses}`;
                const decided = wins + losses;
                const winPct = decided > 0 ? (wins / decided) : null;
                return (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                            <div className="flex items-center justify-between gap-4 flex-wrap">
                                <div>
                                    <h3 className="section-title font-bold">{selectedMatchup.team} vs {selectedMatchup.opponent}</h3>
                                    <p className="body-text text-blue-100 mt-1">{selectedMatchup.count} game{selectedMatchup.count !== 1 ? 's' : ''} attended</p>
                                </div>
                                <div className="text-center px-4 py-2 bg-white bg-opacity-15 rounded-lg">
                                    <div className="text-2xl font-bold font-mono">{recordStr}</div>
                                    <div className="text-xs text-blue-100">{selectedMatchup.team} record{winPct !== null ? ` • ${winPct.toFixed(3).replace(/^0/, '')}` : ''}</div>
                                </div>
                            </div>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            {selectedMatchup.games.length > 0 ? (
                                <div className="divide-y">
                                    {selectedMatchup.games.map((game) => {
                                        const isHomeGame = game.homeTeam === selectedMatchup.team;
                                        const res = getResult(game);
                                        const badgeClass = res?.result === 'W' ? 'bg-green-100 text-green-700 border-green-300'
                                            : res?.result === 'L' ? 'bg-red-100 text-red-700 border-red-300'
                                            : 'bg-slate-100 text-slate-600 border-slate-300';
                                        return (
                                            <div key={game.gameId} className="p-4 hover:bg-blue-50 transition-colors cursor-pointer"
                                                onClick={() => { requestGameDetails(game.gameId); setShowModal(false); }}>
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-3">
                                                        <span className="body-text font-bold text-blue-600">{game.date}</span>
                                                        <span className="small-text text-slate-500">{game.startTime}</span>
                                                    </div>
                                                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                                                        <GameLink gameId={game.gameId} mlbGamePk={game.mlbGamePk} source={game.source} />
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4 flex-wrap">
                                                    {res && <span className={`small-text font-bold px-2 py-0.5 rounded border ${badgeClass}`} title={`${selectedMatchup.team} ${res.result === 'W' ? 'won' : res.result === 'L' ? 'lost' : 'tied'} ${res.teamScore}-${res.oppScore}`}>{selectedMatchup.team} {res.result}</span>}
                                                    <div className="flex items-center gap-2">
                                                        <span className={`body-text w-12 text-right ${isHomeGame ? 'font-normal' : 'font-bold'}`}>{game.awayTeam}</span>
                                                        <span className="body-text text-slate-500">@</span>
                                                        <span className={`body-text w-12 ${isHomeGame ? 'font-bold' : 'font-normal'}`}>{game.homeTeam}</span>
                                                    </div>
                                                    <span className="font-mono body-text bg-slate-100 px-3 py-1 rounded font-bold">{game.score}</span>
                                                    <span className="body-text text-slate-600">{game.venue}</span>
                                                    {game.attendance > 0 && <span className="small-text text-slate-500">👥 {game.attendance.toLocaleString()}</span>}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="p-8 text-center body-text text-slate-500">No games found between these teams</div>
                            )}
                        </div>
                        <div className="p-4 border-t bg-slate-50">
                            <button onClick={() => setShowModal(false)} className="px-6 py-2 bg-blue-600 text-white body-text rounded-lg hover:bg-blue-700 font-medium w-full">Close</button>
                        </div>
                    </div>
                </div>
                );
            })()}
        </>
    );
};

const OriolesStadiumMap = ({ orioles }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markersRef = useRef([]);

    // Build visited stadiums data from Orioles data
    const visitedData = useMemo(() => {
        const visited = {};
        (orioles || []).forEach(o => {
            const match = matchStadiumByName(o.stadium);
            if (match) {
                visited[match.id] = {
                    ...o,
                    stadiumInfo: match,
                    hasVisited: true,
                };
            }
        });
        return visited;
    }, [orioles]);

    // Calculate stats (only count current MLB stadiums toward the goal - exclude spring training)
    const stats = useMemo(() => {
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const historicalStadiums = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining);
        const springTrainingStadiums = ALL_MLB_STADIUMS.filter(s => s.springTraining);
        const visitedCount = currentStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        const historicalVisited = historicalStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        const springVisited = springTrainingStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        return {
            currentTotal: currentStadiums.length,
            visitedCount,
            historicalVisited,
            springVisited,
            remaining: currentStadiums.length - visitedCount,
            percent: Math.round((visitedCount / currentStadiums.length) * 100),
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

        // Show current MLB stadiums + historical that were visited + spring training that were visited
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const visitedHistorical = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining && visitedData[s.id]?.hasVisited);
        const visitedSpringTraining = ALL_MLB_STADIUMS.filter(s => s.springTraining && visitedData[s.id]?.hasVisited);
        const stadiumsToShow = [...currentStadiums, ...visitedHistorical, ...visitedSpringTraining];

        stadiumsToShow.forEach(stadium => {
            const data = visitedData[stadium.id];
            const hasVisited = data?.hasVisited;
            const isHistorical = !stadium.current && !stadium.springTraining;
            const isSpringTraining = stadium.springTraining;

            // Determine marker color
            let fillColor = '#9ca3af'; // gray - not visited
            let borderColor = '#6b7280';
            if (hasVisited && isSpringTraining) {
                fillColor = '#22c55e'; // green - spring training visited
                borderColor = '#16a34a';
            } else if (hasVisited && isHistorical) {
                fillColor = '#a855f7'; // purple - historical visited
                borderColor = '#9333ea';
            } else if (hasVisited) {
                fillColor = '#f97316'; // orange - saw Orioles (current)
                borderColor = '#ea580c';
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
            let statusText = '<span style="color: #9ca3af;">Not yet visited with Orioles</span>';
            let detailsHtml = '';
            let teamLabel = stadium.team;

            if (hasVisited && isSpringTraining) {
                statusText = '<span style="color: #22c55e; font-weight: bold;">✓ Spring Training - Saw Orioles here!</span>';
                teamLabel = 'Spring Training';
            } else if (hasVisited && isHistorical) {
                statusText = '<span style="color: #a855f7; font-weight: bold;">✓ Historical - Saw Orioles here!</span>';
                detailsHtml += `<div style="color: #666; font-size: 11px;">${stadium.years}</div>`;
            } else if (hasVisited) {
                statusText = '<span style="color: #f97316; font-weight: bold;">✓ Saw Orioles here!</span>';
            }

            if (hasVisited) {
                if (data.record) {
                    detailsHtml += `<div><strong>O's Record:</strong> ${data.record}</div>`;
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

            const popupContent = `
                <div style="min-width: 180px; font-family: system-ui, sans-serif;">
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">${stadium.name}</div>
                    <div style="color: #666; font-size: 12px; margin-bottom: 8px;">${teamLabel}${isHistorical ? ' (Historical)' : ''}</div>
                    <div style="margin-bottom: 8px;">${statusText}</div>
                    ${detailsHtml}
                </div>
            `;

            marker.bindPopup(popupContent);
            markersRef.current.push(marker);
        });
    }, [visitedData]);

    return (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <div className="p-4 border-b bg-gradient-to-r from-orange-500 to-orange-600 text-white">
                <h3 className="font-bold text-lg">🗺️ Orioles Stadium Quest</h3>
                <p className="text-sm text-orange-100 mt-1">See the Orioles at all 30 MLB stadiums</p>
            </div>
            <div ref={mapRef} style={{ height: '400px', width: '100%' }}></div>
            <div className="p-4 bg-orange-50 border-t">
                <div className="grid grid-cols-5 gap-4 text-center">
                    <div>
                        <div className="text-2xl font-bold text-orange-600">{stats.visitedCount}</div>
                        <div className="text-xs text-slate-600">Current</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-purple-600">{stats.historicalVisited}</div>
                        <div className="text-xs text-slate-600">Historical</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-slate-500">{stats.remaining}</div>
                        <div className="text-xs text-slate-600">Remaining</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-orange-600">{stats.percent}%</div>
                        <div className="text-xs text-slate-600">Complete</div>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1">
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                            <span className="text-xs text-slate-600">Current</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                            <span className="text-xs text-slate-600">Historical</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                            <span className="text-xs text-slate-600">Not yet</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const OriolesDashboard = ({ orioles, games }) => {
    // Filter to only Orioles games
    const oriolesGames = useMemo(() => {
        return (games || []).filter(g => g.homeTeam === 'BAL' || g.awayTeam === 'BAL')
            .sort((a, b) => new Date(a.date) - new Date(b.date));
    }, [games]);

    // Helper to parse score from format like "BOS 6 - 5 BAL" or "6-5"
    const parseScore = (scoreStr, homeTeam, awayTeam) => {
        if (!scoreStr) return null;
        // Try format: "AWAY # - # HOME" (e.g., "BOS 6 - 5 BAL")
        const match1 = scoreStr.match(/(\w+)\s+(\d+)\s*-\s*(\d+)\s+(\w+)/);
        if (match1) {
            const [_, team1, score1, score2, team2] = match1;
            // Determine which score belongs to home/away
            if (team2 === homeTeam || team2.includes(homeTeam)) {
                return { awayScore: parseInt(score1), homeScore: parseInt(score2) };
            } else {
                return { awayScore: parseInt(score2), homeScore: parseInt(score1) };
            }
        }
        // Try simple format: "#-#"
        const match2 = scoreStr.match(/(\d+)\s*-\s*(\d+)/);
        if (match2) {
            return { awayScore: parseInt(match2[1]), homeScore: parseInt(match2[2]) };
        }
        return null;
    };

    // Calculate summary stats
    const summaryStats = useMemo(() => {
        let wins = 0, losses = 0, runsScored = 0, runsAllowed = 0, homeRuns = 0;
        let homeWins = 0, homeLosses = 0, awayWins = 0, awayLosses = 0;

        oriolesGames.forEach(game => {
            const isHome = game.homeTeam === 'BAL';
            const scores = parseScore(game.score, game.homeTeam, game.awayTeam);
            if (!scores) return;

            const { awayScore, homeScore } = scores;
            const oRuns = isHome ? homeScore : awayScore;
            const oppRuns = isHome ? awayScore : homeScore;
            const won = oRuns > oppRuns;

            runsScored += oRuns;
            runsAllowed += oppRuns;

            if (won) {
                wins++;
                if (isHome) homeWins++; else awayWins++;
            } else {
                losses++;
                if (isHome) homeLosses++; else awayLosses++;
            }
        });

        return {
            record: `${wins}-${losses}`,
            winPct: wins + losses > 0 ? ((wins / (wins + losses)) * 100).toFixed(1) : '0.0',
            runsScored,
            runsAllowed,
            runDiff: runsScored - runsAllowed,
            homeRecord: `${homeWins}-${homeLosses}`,
            awayRecord: `${awayWins}-${awayLosses}`,
            totalGames: oriolesGames.length
        };
    }, [oriolesGames]);

    // Normalize team codes (OAK and ATH are the same franchise)
    const normalizeTeam = (code) => {
        return normalizeTeamCode(code);
    };

    // Calculate opponent breakdown
    const opponentStats = useMemo(() => {
        const stats = {};
        const alEast = ['NYY', 'NYA', 'BOS', 'TOR', 'TB', 'TBA'];

        oriolesGames.forEach(game => {
            const isHome = game.homeTeam === 'BAL';
            const rawOpponent = isHome ? game.awayTeam : game.homeTeam;
            const opponent = normalizeTeam(rawOpponent);
            const scores = parseScore(game.score, game.homeTeam, game.awayTeam);
            if (!scores) return;

            const { awayScore, homeScore } = scores;
            const oRuns = isHome ? homeScore : awayScore;
            const oppRuns = isHome ? awayScore : homeScore;
            const won = oRuns > oppRuns;

            if (!stats[opponent]) {
                stats[opponent] = { wins: 0, losses: 0, runsScored: 0, runsAllowed: 0, isAlEast: alEast.includes(opponent) };
            }
            if (won) stats[opponent].wins++;
            else stats[opponent].losses++;
            stats[opponent].runsScored += oRuns;
            stats[opponent].runsAllowed += oppRuns;
        });

        return Object.entries(stats)
            .map(([team, s]) => ({
                team,
                record: `${s.wins}-${s.losses}`,
                wins: s.wins,
                losses: s.losses,
                games: s.wins + s.losses,
                runsScored: s.runsScored,
                runsAllowed: s.runsAllowed,
                runDiff: s.runsScored - s.runsAllowed,
                isAlEast: s.isAlEast
            }))
            .sort((a, b) => b.games - a.games);
    }, [oriolesGames]);

    // Calculate streaks and timeline
    const streaksData = useMemo(() => {
        let currentStreak = { type: null, count: 0 };
        let longestWinStreak = 0, longestLossStreak = 0;
        let tempWinStreak = 0, tempLossStreak = 0;
        const recentGames = [];

        oriolesGames.forEach(game => {
            const isHome = game.homeTeam === 'BAL';
            const scores = parseScore(game.score, game.homeTeam, game.awayTeam);
            if (!scores) return;

            const { awayScore, homeScore } = scores;
            const oRuns = isHome ? homeScore : awayScore;
            const oppRuns = isHome ? awayScore : homeScore;
            const won = oRuns > oppRuns;

            recentGames.push({
                date: game.date,
                opponent: isHome ? game.awayTeam : game.homeTeam,
                result: won ? 'W' : 'L',
                score: `${oRuns}-${oppRuns}`,
                venue: game.venue,
                isHome
            });

            if (won) {
                tempWinStreak++;
                tempLossStreak = 0;
                longestWinStreak = Math.max(longestWinStreak, tempWinStreak);
            } else {
                tempLossStreak++;
                tempWinStreak = 0;
                longestLossStreak = Math.max(longestLossStreak, tempLossStreak);
            }
        });

        // Current streak from most recent games
        if (recentGames.length > 0) {
            const lastResult = recentGames[recentGames.length - 1].result;
            let streakCount = 0;
            for (let i = recentGames.length - 1; i >= 0; i--) {
                if (recentGames[i].result === lastResult) streakCount++;
                else break;
            }
            currentStreak = { type: lastResult, count: streakCount };
        }

        // Monthly breakdown - handle both YYYY-MM-DD and MM/DD/YYYY formats
        const monthlyStats = {};
        const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        recentGames.forEach(g => {
            if (!g.date) return;
            let year, monthNum;
            if (g.date.includes('/')) {
                // MM/DD/YYYY format
                const parts = g.date.split('/');
                monthNum = parseInt(parts[0]);
                year = parts[2]?.length === 2 ? '20' + parts[2] : parts[2];
            } else if (g.date.includes('-')) {
                // YYYY-MM-DD format
                const parts = g.date.split('-');
                year = parts[0];
                monthNum = parseInt(parts[1]);
            }
            if (!year || !monthNum) return;
            const monthKey = `${year}-${String(monthNum).padStart(2, '0')}`;
            if (!monthlyStats[monthKey]) monthlyStats[monthKey] = { wins: 0, losses: 0, year, monthNum };
            if (g.result === 'W') monthlyStats[monthKey].wins++;
            else monthlyStats[monthKey].losses++;
        });

        return {
            currentStreak,
            longestWinStreak,
            longestLossStreak,
            recentGames: recentGames.slice(-10).reverse(),
            monthlyStats: Object.entries(monthlyStats).map(([key, s]) => ({
                month: `${monthNames[s.monthNum]} ${s.year}`,
                sortKey: key,
                record: `${s.wins}-${s.losses}`,
                wins: s.wins,
                losses: s.losses
            })).sort((a, b) => a.sortKey.localeCompare(b.sortKey))
        };
    }, [oriolesGames]);

    const alEastOpponents = opponentStats.filter(o => o.isAlEast);
    const otherOpponents = opponentStats.filter(o => !o.isAlEast);

    return (
        <div className="space-y-6">
            {/* Summary Stats */}
            <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
                <h2 className="text-2xl font-bold mb-4">🧡 Orioles Dashboard</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.record}</div>
                        <div className="text-sm opacity-90">Record</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.winPct}%</div>
                        <div className="text-sm opacity-90">Win %</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.runsScored}</div>
                        <div className="text-sm opacity-90">Runs Scored</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.runsAllowed}</div>
                        <div className="text-sm opacity-90">Runs Allowed</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className={`text-3xl font-bold ${summaryStats.runDiff >= 0 ? 'text-green-200' : 'text-red-200'}`}>
                            {summaryStats.runDiff >= 0 ? '+' : ''}{summaryStats.runDiff}
                        </div>
                        <div className="text-sm opacity-90">Run Diff</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.homeRecord}</div>
                        <div className="text-sm opacity-90">Home</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <div className="text-3xl font-bold">{summaryStats.awayRecord}</div>
                        <div className="text-sm opacity-90">Away</div>
                    </div>
                </div>
            </div>

            {/* Stadium Map */}
            <OriolesStadiumMap orioles={orioles} />

            {/* Streaks & Recent Games */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b">
                        <h3 className="font-bold text-lg">📈 Streaks</h3>
                    </div>
                    <div className="p-4">
                        <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="text-center p-3 bg-slate-50 rounded-lg">
                                <div className={`text-2xl font-bold ${streaksData.currentStreak.type === 'W' ? 'text-green-600' : 'text-red-600'}`}>
                                    {streaksData.currentStreak.type}{streaksData.currentStreak.count}
                                </div>
                                <div className="text-xs text-slate-500">Current</div>
                            </div>
                            <div className="text-center p-3 bg-green-50 rounded-lg">
                                <div className="text-2xl font-bold text-green-600">W{streaksData.longestWinStreak}</div>
                                <div className="text-xs text-slate-500">Longest Win Streak</div>
                            </div>
                            <div className="text-center p-3 bg-red-50 rounded-lg">
                                <div className="text-2xl font-bold text-red-600">L{streaksData.longestLossStreak}</div>
                                <div className="text-xs text-slate-500">Longest Loss Streak</div>
                            </div>
                        </div>
                        <h4 className="font-semibold text-sm text-slate-600 mb-2">Last 10 Games</h4>
                        <div className="flex gap-1 flex-wrap">
                            {streaksData.recentGames.map((g) => (
                                <div key={g.gameId || `${g.date}-${g.opponent}`} className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold text-white ${g.result === 'W' ? 'bg-green-500' : 'bg-red-500'}`} title={`${g.date}: ${g.result} ${g.score} vs ${g.opponent}`}>
                                    {g.result}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b">
                        <h3 className="font-bold text-lg">📅 Monthly Breakdown</h3>
                    </div>
                    <div className="p-4">
                        <div className="space-y-2">
                            {streaksData.monthlyStats.map(m => {
                                const total = m.wins + m.losses;
                                const winPct = total > 0 ? (m.wins / total) * 100 : 0;
                                return (
                                    <div key={m.month} className="flex items-center gap-3">
                                        <span className="w-20 text-sm font-medium">{m.month}</span>
                                        <div className="flex-1 bg-slate-200 rounded-full h-4 overflow-hidden">
                                            <div className="bg-green-500 h-full" style={{ width: `${winPct}%` }}></div>
                                        </div>
                                        <span className="w-16 text-sm font-semibold text-right">{m.record}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>

            {/* Opponent Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-t-lg">
                        <h3 className="font-bold text-lg">⚔️ vs AL East</h3>
                    </div>
                    <div className="p-4">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-slate-500 border-b">
                                    <th className="pb-2">Team</th>
                                    <th className="pb-2 text-center">G</th>
                                    <th className="pb-2 text-center">Record</th>
                                    <th className="pb-2 text-center">RS</th>
                                    <th className="pb-2 text-center">RA</th>
                                    <th className="pb-2 text-center">Diff</th>
                                </tr>
                            </thead>
                            <tbody>
                                {alEastOpponents.map(o => (
                                    <tr key={o.team} className="border-b last:border-0 hover:bg-slate-50">
                                        <td className="py-2 font-semibold">{o.team}</td>
                                        <td className="py-2 text-center">{o.games}</td>
                                        <td className="py-2 text-center font-mono">{o.record}</td>
                                        <td className="py-2 text-center">{o.runsScored}</td>
                                        <td className="py-2 text-center">{o.runsAllowed}</td>
                                        <td className={`py-2 text-center font-semibold ${o.runDiff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {o.runDiff >= 0 ? '+' : ''}{o.runDiff}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b">
                        <h3 className="font-bold text-lg">🏟️ vs Other Teams</h3>
                    </div>
                    <div className="p-4 max-h-64 overflow-y-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-slate-500 border-b">
                                    <th className="pb-2">Team</th>
                                    <th className="pb-2 text-center">G</th>
                                    <th className="pb-2 text-center">Record</th>
                                    <th className="pb-2 text-center">Diff</th>
                                </tr>
                            </thead>
                            <tbody>
                                {otherOpponents.map(o => (
                                    <tr key={o.team} className="border-b last:border-0 hover:bg-slate-50">
                                        <td className="py-2 font-semibold">{o.team}</td>
                                        <td className="py-2 text-center">{o.games}</td>
                                        <td className="py-2 text-center font-mono">{o.record}</td>
                                        <td className={`py-2 text-center font-semibold ${o.runDiff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {o.runDiff >= 0 ? '+' : ''}{o.runDiff}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Stadium Table */}
            <DataTable
                title="🏟️ Orioles by Stadium"
                data={orioles || []}
                defaultSortKey="games"
                columns={[
                    { key: 'stadium', label: 'Stadium' },
                    { key: 'games', label: 'G' },
                    { key: 'record', label: 'Record' },
                    { key: 'firstVisit', label: 'First' },
                    { key: 'lastVisit', label: 'Last' },
                    { key: 'runsScored', label: 'RS' },
                    { key: 'runsAllowed', label: 'RA' },
                    { key: 'runDiff', label: 'Diff' },
                    { key: 'homeRunsHit', label: 'HR' },
                    { key: 'oneRunGames', label: '1-Run' }
                ]}
            />
        </div>
    );
};

const CompanionStadiumMap = ({ companion }) => {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markersRef = useRef([]);

    // Build visited stadiums data from companion data
    const visitedData = useMemo(() => {
        const visited = {};
        const stadiumsList = companion?.stadiumsList || [];
        const oriolesStadiumsList = companion?.oriolesStadiumsList || [];

        // Mark all visited stadiums
        stadiumsList.forEach(stadiumName => {
            const match = matchStadiumByName(stadiumName);
            if (match) {
                visited[match.id] = {
                    stadiumInfo: match,
                    hasVisited: true,
                    sawOrioles: oriolesStadiumsList.includes(stadiumName),
                };
            }
        });
        return visited;
    }, [companion]);

    // Calculate stats (only count current MLB stadiums toward the goal - exclude spring training)
    const stats = useMemo(() => {
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const historicalStadiums = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining);
        const visitedCount = currentStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        const oriolesCount = currentStadiums.filter(s => visitedData[s.id]?.sawOrioles).length;
        const historicalVisited = historicalStadiums.filter(s => visitedData[s.id]?.hasVisited).length;
        return {
            currentTotal: currentStadiums.length,
            visitedCount,
            oriolesCount,
            historicalVisited,
            remaining: currentStadiums.length - visitedCount,
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

        // Show current MLB stadiums + historical that were visited + spring training that were visited
        const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
        const visitedHistorical = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining && visitedData[s.id]?.hasVisited);
        const visitedSpringTraining = ALL_MLB_STADIUMS.filter(s => s.springTraining && visitedData[s.id]?.hasVisited);
        const stadiumsToShow = [...currentStadiums, ...visitedHistorical, ...visitedSpringTraining];

        stadiumsToShow.forEach(stadium => {
            const data = visitedData[stadium.id];
            const hasVisited = data?.hasVisited;
            const sawOrioles = data?.sawOrioles;
            const isHistorical = !stadium.current && !stadium.springTraining;
            const isSpringTraining = stadium.springTraining;

            // Determine marker color
            let fillColor = '#9ca3af'; // gray - not visited
            let borderColor = '#6b7280';
            if (hasVisited && isSpringTraining) {
                fillColor = '#06b6d4'; // cyan - spring training
                borderColor = '#0891b2';
            } else if (hasVisited && isHistorical) {
                fillColor = '#a855f7'; // purple - historical
                borderColor = '#9333ea';
            } else if (sawOrioles) {
                fillColor = '#f97316'; // orange - saw Orioles
                borderColor = '#ea580c';
            } else if (hasVisited) {
                fillColor = '#22c55e'; // green - visited (non-Orioles)
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
            let statusText = '<span style="color: #9ca3af;">Not yet visited together</span>';
            let teamLabel = stadium.team;
            if (hasVisited && isSpringTraining) {
                statusText = `<span style="color: #06b6d4; font-weight: bold;">✓ Spring Training${sawOrioles ? ' + Orioles' : ''}</span>`;
                teamLabel = 'Spring Training';
            } else if (hasVisited && isHistorical) {
                statusText = `<span style="color: #a855f7; font-weight: bold;">✓ Historical${sawOrioles ? ' + Orioles' : ''}</span>`;
            } else if (sawOrioles) {
                statusText = '<span style="color: #f97316; font-weight: bold;">✓ Visited + Saw Orioles</span>';
            } else if (hasVisited) {
                statusText = '<span style="color: #22c55e; font-weight: bold;">✓ Visited together</span>';
            }

            const popupContent = `
                <div style="min-width: 180px; font-family: system-ui, sans-serif;">
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">${stadium.name}</div>
                    <div style="color: #666; font-size: 12px; margin-bottom: 8px;">${teamLabel}${isHistorical ? ' (Historical)' : ''}</div>
                    ${isHistorical ? `<div style="color: #666; font-size: 11px; margin-bottom: 4px;">${stadium.years}</div>` : ''}
                    <div>${statusText}</div>
                </div>
            `;

            marker.bindPopup(popupContent);
            markersRef.current.push(marker);
        });
    }, [visitedData]);

    if (!companion) return null;

    return (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden mt-4">
            <div className="p-3 border-b bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                <h4 className="font-bold">🗺️ Stadiums with {companion.name}</h4>
            </div>
            <div ref={mapRef} style={{ height: '300px', width: '100%' }}></div>
            <div className="p-3 bg-slate-50 border-t">
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3 flex-wrap">
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-500"></span>
                            <span className="text-slate-600 text-xs">Visited ({stats.visitedCount - stats.oriolesCount})</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                            <span className="text-slate-600 text-xs">O's ({stats.oriolesCount})</span>
                        </div>
                        {stats.historicalVisited > 0 && (
                            <div className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                                <span className="text-slate-600 text-xs">Historical ({stats.historicalVisited})</span>
                            </div>
                        )}
                        <div className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                            <span className="text-slate-600 text-xs">Not yet ({stats.remaining})</span>
                        </div>
                    </div>
                    <span className="font-bold text-blue-600">{stats.visitedCount}/30</span>
                </div>
            </div>
        </div>
    );
};

const CompanionsView = ({ companionData }) => {
    const [selectedCompanion, setSelectedCompanion] = useState(null);
    const [showGames, setShowGames] = useState(false);

    if (!companionData || !companionData.companions || Object.keys(companionData.companions).length === 0) {
        return (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h2 className="section-title font-bold mb-4">👥 Games With Companions</h2>
                <div className="text-center py-8">
                    <p className="body-text text-slate-600 mb-4">No companion data found.</p>
                    <div className="bg-slate-50 rounded-lg p-4 max-w-lg mx-auto text-left">
                        <p className="font-semibold text-slate-800 mb-2">To track games with companions:</p>
                        <ol className="list-decimal list-inside space-y-1 text-sm text-slate-600">
                            <li>Edit <code className="bg-slate-200 px-1 rounded">companions.csv</code> in your MLB Game Tracker folder</li>
                            <li>Add rows with format: <code className="bg-slate-200 px-1 rounded">GameID,Companion1|Companion2</code></li>
                            <li>Example: <code className="bg-slate-200 px-1 rounded">BAL202505090,Dad</code></li>
                            <li>Regenerate the website</li>
                        </ol>
                    </div>
                </div>
            </div>
        );
    }

    const companions = Object.values(companionData.companions);

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg border border-slate-200">
                <div className="p-4 border-b">
                    <h2 className="section-title font-bold">👥 Games With Companions</h2>
                    <p className="body-text text-slate-500 mt-1">Track who you've attended games with</p>
                </div>
                <div className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {companions.map(companion => (
                            <div key={companion.name} className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="font-bold text-lg text-blue-800">{companion.name}</h3>
                                    <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-bold">
                                        {companion.totalGames} game{companion.totalGames !== 1 ? 's' : ''}
                                    </span>
                                </div>
                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-slate-600">Stadiums visited:</span>
                                        <span className="font-semibold">{companion.uniqueStadiums}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-600">Orioles games:</span>
                                        <span className="font-semibold text-orange-600">{companion.oriolesGames}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-600">O's stadiums:</span>
                                        <span className="font-semibold text-orange-600">{companion.oriolesStadiums}</span>
                                    </div>
                                </div>
                                <div className="mt-3 pt-3 border-t border-blue-200">
                                    <button
                                        onClick={() => { setSelectedCompanion(companion); setShowGames(true); }}
                                        className="w-full text-center text-sm text-blue-600 hover:text-blue-800 font-medium"
                                    >
                                        View all games →
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Detailed stats per companion */}
            {companions.map(companion => (
                <div key={companion.name} className="bg-white rounded-lg border border-slate-200">
                    <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
                        <h3 className="font-bold text-lg">📊 {companion.name} - Detailed Stats</h3>
                    </div>
                    <div className="p-4">
                        {/* All 30 current MLB stadiums + historical stadiums visited with this companion */}
                        {(() => {
                            const currentStadiums = ALL_MLB_STADIUMS.filter(s => s.current && !s.international && !s.springTraining);
                            const historicalAll = ALL_MLB_STADIUMS.filter(s => !s.current && !s.international && !s.springTraining);
                            const visitedIds = new Set();
                            const oriolesIds = new Set();
                            (companion.stadiumsList || []).forEach(name => {
                                const m = matchStadiumByName(name);
                                if (m) visitedIds.add(m.id);
                            });
                            (companion.oriolesStadiumsList || []).forEach(name => {
                                const m = matchStadiumByName(name);
                                if (m) oriolesIds.add(m.id);
                            });
                            const visitedCurrent = currentStadiums.filter(s => visitedIds.has(s.id));
                            const oriolesCurrent = currentStadiums.filter(s => oriolesIds.has(s.id));
                            const unvisitedCurrent = currentStadiums.filter(s => !visitedIds.has(s.id));
                            // Historical stadiums visited (don't count toward "still to see")
                            const visitedHistorical = historicalAll.filter(s => visitedIds.has(s.id));
                            // Sort: Orioles-seen, visited current, unvisited current, historical-orioles, historical-visited
                            const orderRank = (s) => {
                                const isCurrent = !!s.current;
                                if (oriolesIds.has(s.id)) return isCurrent ? 0 : 3;
                                if (visitedIds.has(s.id)) return isCurrent ? 1 : 4;
                                return 2;  // unvisited current
                            };
                            const all = [...currentStadiums, ...visitedHistorical].sort((a, b) => {
                                const ra = orderRank(a), rb = orderRank(b);
                                return ra - rb || a.name.localeCompare(b.name);
                            });
                            return (
                                <div>
                                    <div className="flex flex-wrap items-baseline justify-between gap-2 mb-2">
                                        <h4 className="font-semibold text-slate-800">🏟️ MLB Stadiums</h4>
                                        <div className="text-xs text-slate-500 flex flex-wrap gap-3">
                                            <span className="inline-flex items-center gap-1">
                                                <span className="inline-block w-3 h-3 bg-orange-100 border border-orange-300 rounded"></span>
                                                Saw Orioles ({oriolesCurrent.length})
                                            </span>
                                            <span className="inline-flex items-center gap-1">
                                                <span className="inline-block w-3 h-3 bg-blue-100 border border-blue-300 rounded"></span>
                                                Visited together ({visitedCurrent.length - oriolesCurrent.length})
                                            </span>
                                            <span className="inline-flex items-center gap-1">
                                                <span className="inline-block w-3 h-3 bg-slate-50 border border-slate-200 rounded"></span>
                                                Still to see ({unvisitedCurrent.length})
                                            </span>
                                            {visitedHistorical.length > 0 && (
                                                <span className="inline-flex items-center gap-1">
                                                    <span className="inline-block w-3 h-3 bg-amber-50 border border-amber-300 border-dashed rounded"></span>
                                                    Historical ({visitedHistorical.length})
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {all.map(s => {
                                            const visited = visitedIds.has(s.id);
                                            const sawOrioles = oriolesIds.has(s.id);
                                            const isHistorical = !s.current;
                                            let cls;
                                            if (isHistorical) {
                                                cls = sawOrioles
                                                    ? 'bg-orange-50 text-orange-700 border-orange-300 border-dashed italic'
                                                    : 'bg-amber-50 text-amber-700 border-amber-300 border-dashed italic';
                                            } else {
                                                cls = sawOrioles
                                                    ? 'bg-orange-100 text-orange-800 border-orange-300'
                                                    : visited
                                                    ? 'bg-blue-100 text-blue-800 border-blue-300'
                                                    : 'bg-slate-50 text-slate-400 border-slate-200';
                                            }
                                            const icon = sawOrioles ? '🧡' : visited ? '✓' : '○';
                                            const histTag = isHistorical ? ' (historical)' : '';
                                            const title = sawOrioles
                                                ? `Saw Orioles at ${s.name}${histTag}`
                                                : visited
                                                ? `Visited ${s.name}${histTag} with ${companion.name}`
                                                : `Not yet visited with ${companion.name}`;
                                            return (
                                                <span key={s.id} title={title}
                                                      className={`px-2 py-1 rounded border text-xs whitespace-nowrap ${cls}`}>
                                                    {icon} {s.name}
                                                </span>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })()}
                        {/* Recent games */}
                        <div className="mt-4">
                            <h4 className="font-semibold text-slate-800 mb-2">📋 Recent Games (last 5)</h4>
                            <div className="space-y-1">
                                {companion.games.slice(0, 5).map(game => {
                                    const formatDate = (dateStr) => {
                                        if (!dateStr) return '';
                                        const d = new Date(dateStr.split(' ')[0]);
                                        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                                    };
                                    return (
                                        <div key={game.gameId} className="grid grid-cols-3 text-sm bg-slate-50 px-3 py-2 rounded">
                                            <span className="font-medium">{formatDate(game.date)}</span>
                                            <span className="text-center">{game.awayTeam} @ {game.homeTeam}</span>
                                            <span className="text-slate-500 text-right">{game.venue}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                        {/* Stadium Map */}
                        <CompanionStadiumMap companion={companion} />
                    </div>
                </div>
            ))}

            {/* Modal for all games */}
            {showGames && selectedCompanion && (
                <div role="dialog" aria-modal="true" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowGames(false)}>
                    <div className="bg-white rounded-lg shadow-lg max-w-4xl max-w-[95vw] w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="p-6 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                            <h3 className="section-title font-bold">Games with {selectedCompanion.name}</h3>
                            <p className="body-text text-blue-100 mt-1">{selectedCompanion.totalGames} total games</p>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '60vh' }}>
                            <div className="divide-y">
                                {selectedCompanion.games.map((game) => (
                                    <div key={game.gameId || `${game.date}-${game.awayTeam}-${game.homeTeam}`}
                                        className="p-4 hover:bg-blue-50 transition-colors cursor-pointer"
                                        onClick={() => { if (game.gameId) { requestGameDetails(game.gameId); setShowGames(false); } }}>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <span className="font-bold text-blue-600">{(game.date || '').split(' ')[0]}</span>
                                                <span className="font-semibold">{game.awayTeam} @ {game.homeTeam}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className="text-slate-600">{game.venue}</span>
                                                <span className="text-xs text-blue-500">View →</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="p-4 border-t bg-slate-50">
                            <button onClick={() => setShowGames(false)} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium w-full">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};


'''
