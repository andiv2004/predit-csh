import React, { useState } from 'react';
import SimulationCharts from './SimulationCharts';
import './SimulationTab.css';

function SimulationTab({ eventData, eventName, currentEvent, loading, onSimulationComplete }) {
  const [mode, setMode] = useState('single'); // 'single' or 'comparison'
  const [selectedTeam1, setSelectedTeam1] = useState('');
  const [selectedTeam2, setSelectedTeam2] = useState('');
  const [simResults, setSimResults] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState(null);

  if (!eventData || !eventData.data || eventData.data.length === 0) {
    return (
      <div className="simulation-tab">
        <div className="no-data">
          Niciun eveniment selectat. Analizează un eveniment mai întâi.
        </div>
      </div>
    );
  }

  const teams = eventData.data.map(team => ({
    number: team.Team,
    name: team.Name
  }));

  const handleSimulateSingleTeam = async () => {
    if (!selectedTeam1) {
      setSimError('Selectează o echipă!');
      return;
    }

    setSimLoading(true);
    setSimError(null);
    setSimResults(null);

    try {
      const response = await fetch(
        `/api/simulate-team/${currentEvent.code}?season=${currentEvent.season}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ team_number: parseInt(selectedTeam1) })
        }
      );

      if (!response.ok) {
        throw new Error('Simulare eșuată');
      }

      const data = await response.json();
      setSimResults(data.results);
    } catch (err) {
      setSimError(err.message);
    } finally {
      setSimLoading(false);
    }
  };

  const handleCompareTeams = async () => {
    if (!selectedTeam1 || !selectedTeam2) {
      setSimError('Selectează ambele echipe!');
      return;
    }

    if (selectedTeam1 === selectedTeam2) {
      setSimError('Selectează echipe diferite!');
      return;
    }

    setSimLoading(true);
    setSimError(null);
    setSimResults(null);

    try {
      const response = await fetch(
        `/api/compare-teams/${currentEvent.code}?season=${currentEvent.season}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            team1: parseInt(selectedTeam1), 
            team2: parseInt(selectedTeam2)
          })
        }
      );

      if (!response.ok) {
        throw new Error('Comparație eșuată');
      }

      const data = await response.json();
      setSimResults(data.results);
    } catch (err) {
      setSimError(err.message);
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div className="simulation-tab">
      <div className="sim-header">
        <h2>🎯 Simulator 100 Regionale</h2>
        <p>{eventName}</p>
      </div>

      <div className="mode-selector">
        <button 
          className={`mode-btn ${mode === 'single' ? 'active' : ''}`}
          onClick={() => setMode('single')}
        >
          📊 O Echipă
        </button>
        <button 
          className={`mode-btn ${mode === 'comparison' ? 'active' : ''}`}
          onClick={() => setMode('comparison')}
        >
          ⚔️ Comparare 2 Echipe
        </button>
      </div>

      <div className="sim-config">
        {mode === 'single' ? (
          <>
            <div className="form-group">
              <label>Selectează Echipă:</label>
              <select 
                value={selectedTeam1} 
                onChange={(e) => setSelectedTeam1(e.target.value)}
                disabled={simLoading}
              >
                <option value="">-- Alege echipa --</option>
                {teams.map(team => (
                  <option key={team.number} value={team.number}>
                    {team.number} - {team.name}
                  </option>
                ))}
              </select>
            </div>
            <button 
              className="simulate-btn"
              onClick={handleSimulateSingleTeam}
              disabled={simLoading || !selectedTeam1}
            >
              {simLoading ? '⏳ Simulare...' : '▶️ Simulează'}
            </button>
          </>
        ) : (
          <>
            <div className="form-group">
              <label>Echipa 1:</label>
              <select 
                value={selectedTeam1} 
                onChange={(e) => setSelectedTeam1(e.target.value)}
                disabled={simLoading}
              >
                <option value="">-- Alege echipa 1 --</option>
                {teams.map(team => (
                  <option key={`t1-${team.number}`} value={team.number}>
                    {team.number} - {team.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Echipa 2:</label>
              <select 
                value={selectedTeam2} 
                onChange={(e) => setSelectedTeam2(e.target.value)}
                disabled={simLoading}
              >
                <option value="">-- Alege echipa 2 --</option>
                {teams.map(team => (
                  <option key={`t2-${team.number}`} value={team.number}>
                    {team.number} - {team.name}
                  </option>
                ))}
              </select>
            </div>
            <button 
              className="simulate-btn"
              onClick={handleCompareTeams}
              disabled={simLoading || !selectedTeam1 || !selectedTeam2}
            >
              {simLoading ? '⏳ Comparare...' : '⚔️ Compară'}
            </button>
          </>
        )}
      </div>

      {simError && <div className="sim-error">{simError}</div>}

      {simResults && (
        <div className="sim-results">
          {mode === 'single' ? (
            <div className="single-results">
              <div className="result-header">
                <h3>📊 Rezultate Simulare - Echipa {simResults.team}</h3>
              </div>
              <SimulationCharts simResults={simResults} teamNumber={simResults.team} />
            </div>
          ) : (
            <div className="comparison-results">
              <div className="result-header">
                <h3>⚔️ Comparare: {simResults.team1} vs {simResults.team2}</h3>
              </div>
              <div className="comparison-grid">
                <div className="team-box">
                  <h4>Echipa {simResults.team1}</h4>
                  <div className="stat">
                    <span>Regionale Câștigate</span>
                    <div className="value">{simResults.team1_better}</div>
                  </div>
                  <div className="stat">
                    <span>Poziție Medie</span>
                    <div className="value">{simResults.team1_avg_position}</div>
                  </div>
                  <div className="stat">
                    <span>Victorii Medii</span>
                    <div className="value">{simResults.team1_avg_wins}</div>
                  </div>
                  <div className="stat">
                    <span>Top 10</span>
                    <div className="value">{simResults.team1_top_10}</div>
                  </div>
                </div>

                <div className="vs-separator">VS</div>

                <div className="team-box">
                  <h4>Echipa {simResults.team2}</h4>
                  <div className="stat">
                    <span>Regionale Câștigate</span>
                    <div className="value">{simResults.team2_better}</div>
                  </div>
                  <div className="stat">
                    <span>Poziție Medie</span>
                    <div className="value">{simResults.team2_avg_position}</div>
                  </div>
                  <div className="stat">
                    <span>Victorii Medii</span>
                    <div className="value">{simResults.team2_avg_wins}</div>
                  </div>
                  <div className="stat">
                    <span>Top 10</span>
                    <div className="value">{simResults.team2_top_10}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SimulationTab;
