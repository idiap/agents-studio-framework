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
  ChartData,
} from 'chart.js';
import { YearSlider } from './year-slider';

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

interface Dataset {
  label: string;
  data: (number | null)[];
  borderColor: string;
  backgroundColor: string;
  fill: boolean;
  tension: number;
}

interface LineChartData {
  labels: number[];
  datasets: Dataset[];
}

interface DynamicLineChartProps {
  data: LineChartData;
  title?: string;
  height?: number;
  showLegend?: boolean;
}

export const DynamicLineChart: React.FC<DynamicLineChartProps> = ({
  data,
  title = "Investment Returns Over Time",
  height = 400,
  showLegend = true,
}) => {
  const availableYears = data.labels.sort((a, b) => a - b);
  const [selectedYear, setSelectedYear] = useState<number>(Math.max(...availableYears));

  const minYear = Math.min(...availableYears);
  const maxYear = Math.max(...availableYears);

  // Filter data up to the selected year
  const chartData = useMemo((): ChartData<'line'> => {
    const selectedYearIndex = data.labels.indexOf(selectedYear);

    if (selectedYearIndex === -1) {
      return {
        labels: [],
        datasets: [],
      };
    }

    const filteredLabels = data.labels.slice(0, selectedYearIndex + 1);
    const filteredDatasets = data.datasets.map((dataset) => ({
      ...dataset,
      data: dataset.data.slice(0, selectedYearIndex + 1),
    }));

    return {
      labels: filteredLabels,
      datasets: filteredDatasets,
    };
  }, [data, selectedYear]);

  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: showLegend,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          pointStyle: 'circle',
          padding: 20,
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: !!title,
        text: title,
        font: {
          size: 16,
          weight: 'bold',
        },
        padding: {
          top: 10,
          bottom: 30,
        },
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            return value !== null ? `${label}: ${value.toFixed(2)}%` : `${label}: N/A`;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Year',
          font: {
            size: 14,
            weight: 'bold',
          },
        },
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Returns (%)',
          font: {
            size: 14,
            weight: 'bold',
          },
        },
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.1)',
        },
        ticks: {
          callback: function (value) {
            return `${value}%`;
          },
        },
      },
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
    },
    elements: {
      point: {
        radius: 4,
        hoverRadius: 6,
        hitRadius: 8,
      },
      line: {
        tension: 0.1,
        borderWidth: 2,
      },
    },
  };

  return (
    <div className="w-full bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <YearSlider
          selectedYear={selectedYear}
          onYearChange={setSelectedYear}
          minYear={minYear}
          maxYear={maxYear}
        />
      </div>

      <div className="relative" style={{ height: `${height}px` }}>
        <Line data={chartData} options={chartOptions} />
      </div>

      <div className="mt-4 text-sm text-gray-600 text-center">
        Showing data up to {selectedYear}
      </div>
    </div>
  );
};