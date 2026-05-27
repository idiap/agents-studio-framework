// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client';

import React, { useState, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { YearSlider } from './year-slider';
import rangeData from '../data/range_of_expected_annualized_returns.json';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface RangeData {
  [year: string]: {
    'Benchmark Return': number[];
    'Survey Average': number[];
  };
}

const DynamicRangeOfExpectedAnnualizedReturns: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<number>(2025);

  const typedRangeData = rangeData as RangeData;
  const availableYears = Object.keys(typedRangeData).map(Number).sort((a, b) => b - a);
  const minYear = Math.min(...availableYears);
  const maxYear = Math.max(...availableYears);

  const chartData = useMemo(() => {
    const yearKey = selectedYear.toString();
    const data = typedRangeData[yearKey];

    if (!data) {
      return {
        labels: [],
        datasets: [],
      };
    }

    // Create labels for data points (periods 1-10)
    const labels = data['Benchmark Return'].map((_, index) => `Period ${index + 1}`);

    return {
      labels,
      datasets: [
        {
          label: 'Benchmark Return',
          data: data['Benchmark Return'],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 3,
          pointBackgroundColor: '#3b82f6',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          tension: 0.1,
        },
        {
          label: 'Survey Average',
          data: data['Survey Average'],
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderWidth: 3,
          pointBackgroundColor: '#ef4444',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          tension: 0.1,
        },
      ],
    };
  }, [selectedYear, typedRangeData]);

  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          pointStyle: 'circle',
          padding: 20,
          font: {
            size: 14,
            weight: 'bold',
          },
        },
      },
      title: {
        display: true,
        text: `Range of Expected Annualized Returns - ${selectedYear}`,
        font: {
          size: 18,
          weight: 'bold',
        },
        padding: {
          top: 10,
          bottom: 30,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#374151',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function (context) {
            if (context.parsed.y === null) {
              return `${context.dataset.label}: N/A`;
            }
            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`;
          },
        },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Time Periods',
          font: {
            size: 14,
            weight: 'bold',
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Expected Return (%)',
          font: {
            size: 14,
            weight: 'bold',
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        beginAtZero: false,
        min: 4,
        max: 8,
        ticks: {
          callback: function (value) {
            return `${value}%`;
          },
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
    elements: {
      line: {
        tension: 0.1,
      },
    },
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-2 text-center">
          Expected Annualized Returns Analysis
        </h2>
        <p className="text-gray-600 text-center mb-6">
          Compare benchmark returns with survey averages across different time periods
        </p>

        <div className="max-w-md mx-auto">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Year
          </label>
          <YearSlider
            selectedYear={selectedYear}
            onYearChange={setSelectedYear}
            minYear={minYear}
            maxYear={maxYear}
          />
        </div>
      </div>

      <div className="h-96 w-full">
        <Line data={chartData} options={chartOptions} />
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
          <h3 className="font-semibold text-blue-800 mb-1">Benchmark Return</h3>
          <p className="text-sm text-blue-600">
            Standard expected return baseline for comparison
          </p>
        </div>
        <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-500">
          <h3 className="font-semibold text-red-800 mb-1">Survey Average</h3>
          <p className="text-sm text-red-600">
            Average expected returns from industry surveys
          </p>
        </div>
      </div>
    </div>
  );
};

export default DynamicRangeOfExpectedAnnualizedReturns;
