import React, { useState } from 'react';
import './DataDisplay.css';

function DataDisplay({ data }) {
  const [sortField, setSortField] = useState('ranking_score');
  const [sortDirection, setSortDirection] = useState('desc');

  if (!data || !data.data || data.data.length === 0) {
    return <div className="no-data">No data available</div>;
  }

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedData = [...data.data].sort((a, b) => {
    const aVal = a[sortField] ?? '';
    const bVal = b[sortField] ?? '';

    if (typeof aVal === 'string') {
      return sortDirection === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }

    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const columns = [
    { key: 'Team', label: 'Team #' },
    { key: 'Name', label: 'Team Name' },
    { key: 'ranking_score', label: 'Ranking Score' },
    { key: 'OPR_Season', label: 'OPR' },
    { key: 'totalPointsNp', label: 'Total Points' },
    { key: 'autoPoints', label: 'Auto Points' },
    { key: 'dcPoints', label: 'DC Points' },
    { key: 'Matches_Played', label: 'Matches' },
  ];

  return (
    <div className="data-display">
      <div className="data-header">
        <h2>{data.event_name}</h2>
        <p>Event: {data.event} | Season: {data.season} | Teams: {data.teams_count}</p>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={sortField === col.key ? 'sortable active' : 'sortable'}
                >
                  {col.label}
                  {sortField === col.key && (
                    <span className="sort-indicator">
                      {sortDirection === 'asc' ? ' ↑' : ' ↓'}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row, idx) => (
              <tr key={idx} className={idx % 2 === 0 ? 'even' : 'odd'}>
                {columns.map((col) => (
                  <td key={col.key}>
                    {typeof row[col.key] === 'number'
                      ? row[col.key].toFixed(2)
                      : row[col.key] || '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DataDisplay;
