// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client';

import React from 'react';
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

interface LineChartProps {
  data: LineChartData;
  title?: string;
  height?: number;
  showLegend?: boolean;
}

export const LineChart: React.FC<LineChartProps> = ({
  data,
  title = "Investment Returns Over Time",
  height = 400,
  showLegend = true,
}) => {
  const chartData: ChartData<'line'> = {
    labels: data.labels,
    datasets: data.datasets,
  };

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
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
      y: {
        display: true,
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
    <div className="w-full bg-white p-6">
      <div className="text-center">
        <h3 className="text-xl font-semibold text-gray-800 my-4">
          {title}
        </h3>
      </div>
      <div className="relative" style={{ height: `${height}px` }}>
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  );
};