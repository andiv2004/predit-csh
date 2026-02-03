import React from 'react';
import './PredictionsDisplay.css';

function PredictionsDisplay({ predictions, eventName }) {
  if (!predictions || predictions.length === 0) {
    return <div className="no-data">Nu sunt predicții disponibile</div>;
  }

  const redWins = predictions.filter(p => p.Winner === "🔴 ROȘU").length;
  const blueWins = predictions.filter(p => p.Winner === "🔵 ALBASTRU").length;
  const draws = predictions.filter(p => p.Winner === "⚪ EGAL").length;

  return (
    <div className="predictions-display">
      <div className="predictions-header">
        <h2>🔮 Predicții Meciuri</h2>
        <p>{eventName}</p>
        
        <div className="predictions-stats">
          <div className="stat red">
            <span className="label">🔴 Roșu Câștigă:</span>
            <span className="value">{redWins}</span>
          </div>
          <div className="stat blue">
            <span className="label">🔵 Albastru Câștigă:</span>
            <span className="value">{blueWins}</span>
          </div>
          <div className="stat draw">
            <span className="label">⚪ Egal:</span>
            <span className="value">{draws}</span>
          </div>
        </div>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Meci</th>
              <th>Red Alliance</th>
              <th>Red OPR</th>
              <th>Blue Alliance</th>
              <th>Blue OPR</th>
              <th>Winner</th>
              <th>Margin</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((pred, idx) => (
              <tr key={idx} className={`match ${pred.Winner.includes('ROȘU') ? 'red-win' : pred.Winner.includes('ALBASTRU') ? 'blue-win' : 'draw'}`}>
                <td className="match-number">#{pred.Match}</td>
                <td className="alliance-names">
                  <div className="team">{pred['Red 1']} - {pred['Red 1 Name']}</div>
                  <div className="team">{pred['Red 2']} - {pred['Red 2 Name']}</div>
                </td>
                <td className="score red-score">{pred['Red OPR'].toFixed(1)}</td>
                <td className="alliance-names">
                  <div className="team">{pred['Blue 1']} - {pred['Blue 1 Name']}</div>
                  <div className="team">{pred['Blue 2']} - {pred['Blue 2 Name']}</div>
                </td>
                <td className="score blue-score">{pred['Blue OPR'].toFixed(1)}</td>
                <td className="winner">{pred.Winner}</td>
                <td className="margin">{pred['Win Margin'].toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="export-section">
        <button 
          className="export-btn"
          onClick={() => {
            const csv = [
              ['Match', 'Red Team 1', 'Red Team 2', 'Red OPR', 'Blue Team 1', 'Blue Team 2', 'Blue OPR', 'Winner', 'Margin'],
              ...predictions.map(p => [
                p.Match,
                `${p['Red 1']} - ${p['Red 1 Name']}`,
                `${p['Red 2']} - ${p['Red 2 Name']}`,
                p['Red OPR'],
                `${p['Blue 1']} - ${p['Blue 1 Name']}`,
                `${p['Blue 2']} - ${p['Blue 2 Name']}`,
                p['Blue OPR'],
                p.Winner,
                p['Win Margin']
              ])
            ].map(row => row.join(',')).join('\n');
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `predictions_${Date.now()}.csv`;
            a.click();
          }}
        >
          📥 Descarcă CSV
        </button>
      </div>
    </div>
  );
}

export default PredictionsDisplay;
