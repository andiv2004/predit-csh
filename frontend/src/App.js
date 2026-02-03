import React, { useState } from 'react';
import './App.css';
import EventAnalyzer from './components/EventAnalyzer';
import NavigationBar from './components/NavigationBar';
import DataDisplay from './components/DataDisplay';
import ScheduleDisplay from './components/ScheduleDisplay';
import PredictionsDisplay from './components/PredictionsDisplay';
import RankingsDisplay from './components/RankingsDisplay';
import SimulationTab from './components/SimulationTab';

function App() {
  const [eventData, setEventData] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [predictionsData, setPredictionsData] = useState(null);
  const [rankingsData, setRankingsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentEvent, setCurrentEvent] = useState(null);
  const [activeTab, setActiveTab] = useState('teams');

  const handleEventAnalysis = async (eventCode, season) => {
    setLoading(true);
    setError(null);
    setEventData(null);
    setScheduleData(null);
    setPredictionsData(null);
    setRankingsData(null);
    setActiveTab('teams');
    setCurrentEvent({ code: eventCode, season });

    try {
      const response = await fetch(`/api/event/${eventCode}?season=${season}`);
      if (!response.ok) {
        throw new Error('Failed to fetch event data');
      }
      const data = await response.json();
      setEventData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSchedule = async () => {
    if (!currentEvent) return;

    setLoading(true);
    setError(null);
    setPredictionsData(null);
    setRankingsData(null);

    try {
      const response = await fetch(
        `/api/generate-schedule/${currentEvent.code}?season=${currentEvent.season}`
      );
      if (!response.ok) {
        throw new Error('Failed to generate schedule');
      }
      const data = await response.json();
      setScheduleData(data);
      setActiveTab('schedule');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImportSchedule = async (eventCode, season) => {
    setLoading(true);
    setError(null);
    setPredictionsData(null);
    setRankingsData(null);
    setCurrentEvent({ code: eventCode, season });

    try {
      // Fetch event data first
      const eventResponse = await fetch(`/api/event/${eventCode}?season=${season}`);
      if (!eventResponse.ok) {
        throw new Error('Failed to fetch event data');
      }
      const eventData = await eventResponse.json();
      setEventData(eventData);

      // Then import schedule
      const scheduleResponse = await fetch(
        `/api/import-schedule/${eventCode}?season=${season}`
      );
      if (!scheduleResponse.ok) {
        throw new Error('Failed to import schedule');
      }
      const scheduleData = await scheduleResponse.json();
      setScheduleData(scheduleData);
      setActiveTab('schedule');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePredictions = async () => {
    if (!currentEvent || !scheduleData) return;

    setLoading(true);
    setError(null);
    setRankingsData(null);

    try {
      const response = await fetch(
        `/api/predict-schedule/${currentEvent.code}?season=${currentEvent.season}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            schedule: scheduleData.schedule
          })
        }
      );
      if (!response.ok) {
        throw new Error('Failed to generate predictions');
      }
      const data = await response.json();
      setPredictionsData(data);
      setActiveTab('predictions');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRankings = async () => {
    if (!currentEvent || !scheduleData) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/ranking/${currentEvent.code}?season=${currentEvent.season}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            schedule: scheduleData.schedule
          })
        }
      );
      if (!response.ok) {
        throw new Error('Failed to generate rankings');
      }
      const data = await response.json();
      setRankingsData(data);
      setActiveTab('rankings');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 CSH Predict - Team Performance Analysis</h1>
        <p>Analyze FTC team performance by event</p>
      </header>

      <div className="container">
        <EventAnalyzer 
          onAnalyze={handleEventAnalysis} 
          onImportSchedule={handleImportSchedule}
          loading={loading} 
        />

        {error && <div className="error-message">Error: {error}</div>}

        {loading && <div className="loading-message">Loading data...</div>}

        {eventData && (
          <>
            <NavigationBar 
              activeTab={activeTab} 
              onTabChange={setActiveTab}
              hasSchedule={true}
            />

            {activeTab === 'teams' && (
              <>
                <DataDisplay data={eventData} />
              </>
            )}

            {activeTab === 'schedule' && (
              <>
                <div className="action-buttons">
                  <button 
                    className="generate-btn"
                    onClick={handleGenerateSchedule}
                    disabled={loading}
                  >
                    📋 Generează Program
                  </button>
                </div>
                {scheduleData ? (
                  <ScheduleDisplay
                    schedule={scheduleData.schedule}
                    duplicates={scheduleData.duplicate_alliances}
                    matchesCount={scheduleData.matches_count}
                    eventName={scheduleData.event_name}
                  />
                ) : (
                  <div className="empty-schedule">
                    <p>Apasă butonul pentru a genera programul evenimentului</p>
                  </div>
                )}
              </>
            )}

            {activeTab === 'predictions' && (
              <>
                <div className="action-buttons">
                  <button 
                    className="generate-btn"
                    onClick={handleGeneratePredictions}
                    disabled={loading || !scheduleData}
                  >
                    🔮 Generează Predicții
                  </button>
                </div>
                {predictionsData ? (
                  <PredictionsDisplay
                    predictions={predictionsData.predictions}
                    eventName={predictionsData.event_name}
                  />
                ) : (
                  <div className="empty-schedule">
                    <p>Generează mai întâi programul, apoi apasă butonul pentru predicții</p>
                  </div>
                )}
              </>
            )}

            {activeTab === 'rankings' && (
              <>
                <div className="action-buttons">
                  <button 
                    className="generate-btn rankings-btn"
                    onClick={handleGenerateRankings}
                    disabled={loading || !scheduleData}
                  >
                    🏆 Generează Clasament
                  </button>
                </div>
                {rankingsData ? (
                  <RankingsDisplay
                    rankingData={rankingsData.ranking}
                    eventName={rankingsData.event_name}
                  />
                ) : (
                  <div className="empty-schedule">
                    <p>Generează mai întâi programul, apoi apasă butonul pentru clasament</p>
                  </div>
                )}
              </>
            )}

            {activeTab === 'simulator' && (
              <SimulationTab
                eventData={eventData}
                eventName={eventData?.event_name || currentEvent?.code}
                currentEvent={currentEvent}
                loading={loading}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default App;
