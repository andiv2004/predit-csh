import React from 'react';
import './NavigationBar.css';

function NavigationBar({ activeTab, onTabChange, hasSchedule }) {
  return (
    <div className="navigation-bar">
      <button
        className={`nav-tab ${activeTab === 'teams' ? 'active' : ''}`}
        onClick={() => onTabChange('teams')}
      >
        👥 Echipe
      </button>
      <button
        className={`nav-tab ${activeTab === 'schedule' ? 'active' : ''}`}
        onClick={() => onTabChange('schedule')}
        disabled={!hasSchedule}
      >
        📋 Program
      </button>
      <button
        className={`nav-tab ${activeTab === 'predictions' ? 'active' : ''}`}
        onClick={() => onTabChange('predictions')}
        disabled={!hasSchedule}
      >
        🔮 Predicții
      </button>
      <button
        className={`nav-tab ${activeTab === 'rankings' ? 'active' : ''}`}
        onClick={() => onTabChange('rankings')}
        disabled={!hasSchedule}
      >
        🏆 Clasament
      </button>
      <button
        className={`nav-tab ${activeTab === 'simulator' ? 'active' : ''}`}
        onClick={() => onTabChange('simulator')}
        disabled={!hasSchedule}
      >
        🎯 Simulator
      </button>
    </div>
  );
}

export default NavigationBar;
