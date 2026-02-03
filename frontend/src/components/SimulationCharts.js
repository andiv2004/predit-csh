import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import './SimulationCharts.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function SimulationCharts({ simResults, teamNumber }) {
  if (!simResults) return null;

  // Position distribution data for line chart
  const createPositionDistribution = () => {
    const positions = Array.from({ length: 100 }, (_, i) => i + 1);
    const distribution = positions.map(p => {
      const inTop = p <= 10 ? simResults.position_distribution?.top_10 || 0 : 
                   p <= 20 ? simResults.position_distribution?.top_20 || 0 :
                   p <= 50 ? simResults.position_distribution?.top_50 || 0 : 0;
      return inTop;
    });

    return {
      labels: positions,
      datasets: [
        {
          label: 'Distribuție Poziții (100 Simulări)',
          data: distribution,
          borderColor: '#5CDD7C',
          backgroundColor: 'rgba(92, 221, 124, 0.1)',
          fill: true,
          tension: 0.4,
          borderWidth: 3,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointBackgroundColor: '#5CDD7C',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2
        }
      ]
    };
  };

  // Position stats bar chart
  const createPositionStats = () => {
    return {
      labels: ['Top 10', 'Top 20', 'Top 50'],
      datasets: [
        {
          label: 'Simulări în Top',
          data: [
            simResults.position_distribution?.top_10 || 0,
            simResults.position_distribution?.top_20 || 0,
            simResults.position_distribution?.top_50 || 0
          ],
          backgroundColor: [
            '#5CDD7C',
            '#6be58f',
            '#88ffcc'
          ],
          borderColor: [
            '#5CDD7C',
            '#6be58f',
            '#88ffcc'
          ],
          borderWidth: 2,
          borderRadius: 8,
          hoverBackgroundColor: [
            '#6be58f',
            '#75eda6',
            '#9dffdd'
          ]
        }
      ]
    };
  };

  // Win distribution pie chart
  const createWinDistribution = () => {
    const avgWins = Math.round(simResults.avg_wins || 0);
    const avgLosses = 6 - avgWins; // assuming 6 matches per regional

    return {
      labels: ['Victorii Medii', 'Înfrângeri Medii'],
      datasets: [
        {
          data: [avgWins, avgLosses],
          backgroundColor: [
            '#5CDD7C',
            '#ff6b6b'
          ],
          borderColor: [
            '#5CDD7C',
            '#ff6b6b'
          ],
          borderWidth: 2,
          hoverBackgroundColor: [
            '#6be58f',
            '#ff8080'
          ]
        }
      ]
    };
  };

  // Position range doughnut
  const createPositionRange = () => {
    const top10 = simResults.position_distribution?.top_10 || 0;
    const top20_10 = (simResults.position_distribution?.top_20 || 0) - top10;
    const top50_20 = (simResults.position_distribution?.top_50 || 0) - (simResults.position_distribution?.top_20 || 0);
    const other = 100 - (simResults.position_distribution?.top_50 || 0);

    return {
      labels: ['🥇 Top 10', '🥈 Top 11-20', '🥉 Top 21-50', 'Alte poziții'],
      datasets: [
        {
          data: [top10, top20_10, top50_20, other],
          backgroundColor: [
            '#00FF41',     // Verde neon strălucitor - Top 10
            '#FFD700',     // Auriu vibrant - Top 11-20
            '#FF6B35',     // Portocaliu/roșu vibrant - Top 21-50
            '#4A4A4A'      // Gri închis - Alte poziții
          ],
          borderColor: [
            '#00FF41',
            '#FFD700',
            '#FF6B35',
            '#6A6A6A'
          ],
          borderWidth: 3,
          hoverBackgroundColor: [
            '#33FF66',     // Verde mai deschis
            '#FFEE66',     // Auriu mai deschis
            '#FF8855',     // Portocaliu mai deschis
            '#7A7A7A'      // Gri mai deschis
          ]
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        labels: {
          color: '#d8d8f0',
          font: {
            size: 13,
            weight: '600'
          },
          padding: 15,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: 'rgba(45, 27, 78, 0.9)',
        titleColor: '#5CDD7C',
        bodyColor: '#d8d8f0',
        borderColor: '#5CDD7C',
        borderWidth: 1,
        padding: 12,
        titleFont: { size: 14, weight: 'bold' },
        bodyFont: { size: 12 }
      }
    },
    scales: {
      x: {
        ticks: { color: '#b3b3ff', font: { size: 11 } },
        grid: { color: 'rgba(92, 221, 124, 0.1)' }
      },
      y: {
        ticks: { color: '#b3b3ff', font: { size: 11 } },
        grid: { color: 'rgba(92, 221, 124, 0.1)' }
      }
    }
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        labels: {
          color: '#d8d8f0',
          font: {
            size: 13,
            weight: '600'
          },
          padding: 15,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: 'rgba(45, 27, 78, 0.9)',
        titleColor: '#5CDD7C',
        bodyColor: '#d8d8f0',
        borderColor: '#5CDD7C',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    }
  };

  return (
    <div className="simulation-charts-container">
      <div className="charts-grid">
        {/* Bar Chart - Position Stats */}
        <div className="chart-wrapper">
          <div className="chart-title">🎯 Performanță în Top Poziții</div>
          <div className="chart-inner">
            <Bar data={createPositionStats()} options={chartOptions} />
          </div>
        </div>

        {/* Pie Chart - Win Distribution */}
        <div className="chart-wrapper">
          <div className="chart-title">🏆 Medie Victorii/Înfrângeri</div>
          <div className="chart-inner">
            <Pie data={createWinDistribution()} options={pieOptions} />
          </div>
        </div>

        {/* Doughnut Chart - Position Range */}
        <div className="chart-wrapper chart-full-width">
          <div className="chart-title">🥇 Distribuția Medalierii</div>
          <div className="chart-inner">
            <Doughnut data={createPositionRange()} options={pieOptions} />
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="sim-summary-stats">
        <div className="summary-stat-card">
          <div className="summary-stat-label">Poziție Medie</div>
          <div className="summary-stat-value">{simResults.avg_position || 0}</div>
          <div className="summary-stat-range">
            Min: {simResults.min_position || 0} | Max: {simResults.max_position || 0}
          </div>
        </div>
        <div className="summary-stat-card">
          <div className="summary-stat-label">Victorii Medii</div>
          <div className="summary-stat-value">{(simResults.avg_wins || 0).toFixed(2)}</div>
          <div className="summary-stat-range">Din 6 meciuri</div>
        </div>
        <div className="summary-stat-card">
          <div className="summary-stat-label">Rata Top 10</div>
          <div className="summary-stat-value">{(((simResults.position_distribution?.top_10 || 0) / 100) * 100).toFixed(1)}%</div>
          <div className="summary-stat-range">{simResults.position_distribution?.top_10 || 0} din 100</div>
        </div>
        <div className="summary-stat-card">
          <div className="summary-stat-label">Rata Top 50</div>
          <div className="summary-stat-value">{(((simResults.position_distribution?.top_50 || 0) / 100) * 100).toFixed(1)}%</div>
          <div className="summary-stat-range">{simResults.position_distribution?.top_50 || 0} din 100</div>
        </div>
      </div>
    </div>
  );
}

export default SimulationCharts;
