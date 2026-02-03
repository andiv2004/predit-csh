import React, { useMemo } from 'react';
import './RankingsDisplay.css';

function RankingsDisplay({ rankingData, eventName }) {
  if (!rankingData || rankingData.length === 0) {
    return (
      <div className="rankings-display">
        <div className="no-data">
          Niciun clasament disponibil. Generează programul mai întâi.
        </div>
      </div>
    );
  }

  // Calculate stats
  const topTeams = rankingData.slice(0, 3);
  const totalTeams = rankingData.length;
  const maxPoints = Math.max(...rankingData.map(r => r['Ranking Score'] || 0));

  // Export function
  const handleExport = () => {
    const csv = [
      ['Loc', 'Echipa', 'Nume Echipa', 'Ranking Score', 'Win/Loss', 'TBP1', 'OPR', 'Auto OPR'].join(','),
      ...rankingData.map(row =>
        [
          row['Loc'],
          row['Echipa'],
          `"${row['Nume']}"`,
          row['Ranking Score'],
          `${row['Wins']}/${row['Losses']}`,
          row['TBP1'],
          row['OPR'],
          row['Auto OPR']
        ].join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `clasament_${eventName}_${new Date().toISOString().split('T')[0]}.csv`);
    link.click();
  };

  return (
    <div className="rankings-display">
      <div className="rankings-header">
        <h2>🏆 Clasament Predictiv</h2>
        <p>{eventName} - {totalTeams} echipe</p>
        <div className="rankings-stats">
          {topTeams.map((team, idx) => (
            <div key={team['Echipa']} className={`stat top-${idx + 1}`}>
              <div className="label">
                {idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉'} #{team['Loc']}
              </div>
              <div className="value">{team['Echipa']}</div>
              <div className="team-name">{team['Nume'].substring(0, 20)}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Loc</th>
              <th>Echipa</th>
              <th>Nume Echipa</th>
              <th>Ranking Score</th>
              <th>Win/Loss</th>
              <th>TBP1</th>
              <th>OPR</th>
              <th>Auto OPR</th>
            </tr>
          </thead>
          <tbody>
            {rankingData.map((row, idx) => {
              const isTopTeam = idx < 3;
              const rowClass = isTopTeam ? `top-${idx + 1}` : '';
              return (
                <tr key={row['Echipa']} className={rowClass}>
                  <td className="rank-position">{row['Loc']}</td>
                  <td className="team-number">{row['Echipa']}</td>
                  <td className="team-name">{row['Nume']}</td>
                  <td className="ranking-score">{row['Ranking Score']}</td>
                  <td className="win-loss">{row['Wins']}/{row['Losses']}</td>
                  <td className="tbp1">{row['TBP1']}</td>
                  <td className="opr">{row['OPR']}</td>
                  <td className="auto-opr">{row['Auto OPR']}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="export-section">
        <button className="export-btn" onClick={handleExport}>
          📥 Exportă Clasament CSV
        </button>
      </div>
    </div>
  );
}

export default RankingsDisplay;
