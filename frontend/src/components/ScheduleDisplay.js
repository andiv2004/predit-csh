import React from 'react';
import './ScheduleDisplay.css';

function ScheduleDisplay({ schedule, duplicates, matchesCount, eventName }) {
  if (!schedule || schedule.length === 0) {
    return <div className="no-data">Nu sunt date de program disponibile</div>;
  }

  return (
    <div className="schedule-display">
      <div className="schedule-header">
        <h2>📋 Program Generated</h2>
        <p>{eventName} | {matchesCount} meciuri generate</p>
        
        <div className="schedule-stats">
          <div className={`stat ${duplicates === 0 ? 'perfect' : 'warning'}`}>
            <span className="label">Alianțe Duplicate:</span>
            <span className="value">{duplicates}</span>
            {duplicates === 0 && <span className="badge">✨ Perfect</span>}
          </div>
        </div>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Meci</th>
              <th>Red 1</th>
              <th>Red 2</th>
              <th>Blue 1</th>
              <th>Blue 2</th>
            </tr>
          </thead>
          <tbody>
            {schedule.map((match, idx) => (
              <tr key={idx} className={idx % 2 === 0 ? 'even' : 'odd'}>
                <td className="match-number">{match['Match']}</td>
                <td className="red-alliance">{match['Red 1']}</td>
                <td className="red-alliance">{match['Red 2']}</td>
                <td className="blue-alliance">{match['Blue 1']}</td>
                <td className="blue-alliance">{match['Blue 2']}</td>
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
              ['Match', 'Red 1', 'Red 2', 'Blue 1', 'Blue 2'],
              ...schedule.map(m => [m['Match'], m['Red 1'], m['Red 2'], m['Blue 1'], m['Blue 2']])
            ].map(row => row.join(',')).join('\n');
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `schedule_${Date.now()}.csv`;
            a.click();
          }}
        >
          📥 Descarcă CSV
        </button>
      </div>
    </div>
  );
}

export default ScheduleDisplay;
