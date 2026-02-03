import React, { useState } from 'react';
import './EventAnalyzer.css';

function EventAnalyzer({ onAnalyze, onImportSchedule, loading }) {
  const [eventCode, setEventCode] = useState('');
  const [season, setSeason] = useState(2025);

  const handleAnalyzeSubmit = (e) => {
    e.preventDefault();
    if (eventCode.trim()) {
      onAnalyze(eventCode.trim().toUpperCase(), season);
    }
  };

  const handleImportSubmit = (e) => {
    e.preventDefault();
    if (eventCode.trim()) {
      onImportSchedule(eventCode.trim().toUpperCase(), season);
    }
  };

  return (
    <div className="event-analyzer">
      <form>
        <div className="form-group">
          <label htmlFor="eventCode">Event Code:</label>
          <input
            type="text"
            id="eventCode"
            value={eventCode}
            onChange={(e) => setEventCode(e.target.value)}
            placeholder="e.g., USMIIN, TXHOU1"
            disabled={loading}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="season">Season:</label>
          <select
            id="season"
            value={season}
            onChange={(e) => setSeason(parseInt(e.target.value))}
            disabled={loading}
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
            <option value={2023}>2023</option>
            <option value={2022}>2022</option>
          </select>
        </div>

        <div className="button-group">
          <button 
            type="button"
            onClick={handleAnalyzeSubmit}
            disabled={loading}
          >
            {loading ? '⏳ Analyzing...' : '🔍 Analyze Event'}
          </button>
          <button 
            type="button"
            onClick={handleImportSubmit}
            disabled={loading}
            className="import-btn"
          >
            {loading ? '⏳ Importing...' : '📥 Import Schedule'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default EventAnalyzer;
