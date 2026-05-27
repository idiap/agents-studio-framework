// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client';

import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { MatrixController, MatrixElement } from 'chartjs-chart-matrix';
import { Chart } from 'react-chartjs-2';
import correlationDataJson from '../data/correlation-data.json';

ChartJS.register(CategoryScale, LinearScale, PointElement, Tooltip, Legend, MatrixController, MatrixElement);

interface CorrelationData {
  x: number;
  y: number;
  v: number | null;
}

interface CorrelationHeatmapProps {
  selectedYear: number;
}

const variables = [
  'US Equity - Large Cap',
  'US Equity - Small/Mid Cap',
  'Non-US Equity - Developed',
  'Non-US Equity - Emerging',
  'US Corporate Bonds - Core',
  'US Corporate Bonds - Long Duration',
  'US Corporate Bonds - High Yield',
  'Non-US Debt - Developed',
  'Non-US Debt - Emerging',
  'US Treasuries (Cash Equivalents)',
  'TIPS (Inflation-Protected)',
  'Real Estate',
  'Hedge Funds',
  'Commodities',
  'Infrastructure',
  'Private Equity',
  'Private Debt'
];

const generateCorrelationData = (year: number): CorrelationData[] => {
  const yearString = year.toString();

  let rawData: CorrelationData[] = [];

  if (correlationDataJson[yearString as keyof typeof correlationDataJson]) {
    rawData = correlationDataJson[yearString as keyof typeof correlationDataJson];
  } else if (correlationDataJson['2025']) {
    const baseData = correlationDataJson['2025'];
    const seed = year - 2015;

    rawData = baseData.map(point => {
      if (point.x === point.y) {
        return { ...point, v: 1.0 };
      }

      const variation = Math.sin((point.x + point.y + seed) * 0.1) * 0.05;
      const newValue = Math.max(-1, Math.min(1, point.v + variation));

      return { ...point, v: newValue };
    });
  } else {
    return [];
  }

  return rawData.filter(point => point.y >= point.x);
};

const getColor = (value: number): string => {
  const clampedValue = Math.max(-1, Math.min(1, value));

  if (clampedValue <= -0.8) {
    return '#dc2626';
  } else if (clampedValue <= -0.6) {
    return '#ef4444';
  } else if (clampedValue <= -0.4) {
    return '#ec4899';
  } else if (clampedValue <= -0.2) {
    return '#f9a8d4';
  } else if (clampedValue < 0) {
    return '#fce7f3';
  } else if (clampedValue === 0) {
    return '#ffffff';
  } else if (clampedValue <= 0.2) {
    return '#dbeafe';
  } else if (clampedValue <= 0.4) {
    return '#93c5fd';
  } else if (clampedValue <= 0.6) {
    return '#60a5fa';
  } else if (clampedValue <= 0.8) {
    return '#3b82f6';
  } else {
    return '#1e3a8a';
  }
}; export const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({ selectedYear }) => {
  const [correlationData, setCorrelationData] = useState<CorrelationData[]>([]);

  useEffect(() => {
    const data = generateCorrelationData(selectedYear);
    setCorrelationData(data);
  }, [selectedYear]);

  const chartData = {
    datasets: [
      {
        label: `Correlation Matrix ${selectedYear}`,
        data: correlationData,
        backgroundColor: correlationData.map(point => getColor(point.v ?? 0)),
        borderColor: 'rgba(100, 100, 100, 0.1)',
        borderWidth: 0,
        width: (context: any) => {
          const chart = context.chart;
          const area = chart.chartArea;
          if (!area || area.right === undefined || area.left === undefined) {
            return 30;
          }
          return (area.right - area.left) / 17;
        },
        height: (context: any) => {
          const chart = context.chart;
          const area = chart.chartArea;
          if (!area || area.bottom === undefined || area.top === undefined) {
            return 30;
          }
          return (area.bottom - area.top) / 17;
        },
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: 'linear' as const,
        position: 'bottom' as const,
        min: -0.5,
        max: 16.5,
        ticks: {
          stepSize: 1,
          callback: function (value: any) {
            const index = Math.round(value);
            return index >= 0 && index < variables.length ? variables[index] : '';
          },
          maxRotation: 45,
          minRotation: 45,
          font: {
            size: 10,
          },
        },
        grid: {
          display: false,
        },
      },
      y: {
        type: 'linear' as const,
        min: -0.5,
        max: 16.5,
        ticks: {
          stepSize: 1,
          callback: function (value: any) {
            const index = Math.round(value);
            return index >= 0 && index < variables.length ? variables[index] : '';
          },
          font: {
            size: 10,
          },
        },
        grid: {
          display: false,
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          title: function () {
            return '';
          },
          label: function (context: any) {
            const data = context.raw;
            const xVar = variables[data.x] || '';
            const yVar = variables[data.y] || '';
            const correlation = data.v ? data.v.toFixed(3) : 0;
            return [
              `${xVar} ↔ ${yVar}`,
              `Correlation: ${correlation}`,
              `Year: ${selectedYear}`
            ];
          },
        },
      },
    },
    animation: {
      duration: 0,
    },
    transitions: {
      active: {
        animation: {
          duration: 0
        }
      }
    },
    interaction: {
      intersect: false,
    },
  };

  return (
    <div className="w-full h-full">
      <Chart type="matrix" data={chartData} options={options} />
    </div>
  );
};