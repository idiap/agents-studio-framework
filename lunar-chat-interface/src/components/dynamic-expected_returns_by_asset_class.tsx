// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client';

import React, { useState, useMemo } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData,
} from 'chart.js';
import { YearSlider } from './year-slider';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface AssetClassData {
  Min: number | null;
  '25th': number | null;
  '50th': number | null;
  '75th': number | null;
  Max: number | null;
}

interface YearData {
  [assetClass: string]: AssetClassData;
}

interface CandleData {
  [year: string]: YearData;
}

// Define colors for each percentile
const percentileColors = {
  Min: '#ef4444',      // Red
  '25th': '#f97316',   // Orange
  '50th': '#eab308',   // Yellow
  '75th': '#22c55e',   // Green
  Max: '#3b82f6',      // Blue
};

// Asset class display names
const assetClassDisplayNames: { [key: string]: string } = {
  us_equity_large_cap: 'US Equity Large Cap',
  us_equity_small_mid_cap: 'US Equity Small/Mid Cap',
  non_us_equity_developed: 'Non-US Equity Developed',
  non_us_equity_emerging: 'Non-US Equity Emerging',
  us_corporate_bonds_core: 'US Corporate Bonds Core',
  us_corporate_bonds_long_duration: 'US Corporate Bonds Long Duration',
  us_corporate_bonds_high_yield: 'US Corporate Bonds High Yield',
  non_us_debt_developed: 'Non-US Debt Developed',
  non_us_debt_emerging: 'Non-US Debt Emerging',
  us_treasuries_cash_equivalents: 'US Treasuries Cash Equivalents',
  tips_inflation_protected: 'TIPS Inflation Protected',
  real_estate: 'Real Estate',
  hedge_funds: 'Hedge Funds',
  commodities: 'Commodities',
};

interface Props {
  title: string;
  candleData: CandleData;
}

export const DynamicExpectedReturnsByAssetClass: React.FC<Props> = ({
  candleData,
  title = 'Expected Returns by Asset Class',
}) => {
  // Get available years from data
  const availableYears = Object.keys(candleData)
    .map(year => parseInt(year))
    .sort();

  const [selectedYear, setSelectedYear] = useState<number>(availableYears[0] || 2025);

  const chartData = useMemo((): ChartData<'bar'> => {
    const yearData = candleData[selectedYear.toString()];

    if (!yearData) {
      return {
        labels: [],
        datasets: [],
      };
    }

    // Filter out asset classes with null values
    const validAssetClasses = Object.keys(yearData).filter(assetClass => {
      const data = yearData[assetClass];
      return data.Min !== null && data['25th'] !== null && data['50th'] !== null &&
        data['75th'] !== null && data.Max !== null;
    });

    const labels = validAssetClasses.map(assetClass =>
      assetClassDisplayNames[assetClass] || assetClass
    );

    // Create floating bar datasets - each segment represents the range between percentiles
    const datasets = [
      {
        label: 'Min to 25th Percentile',
        data: validAssetClasses.map(assetClass => {
          const data = yearData[assetClass];
          return [data.Min as number, data['25th'] as number] as [number, number];
        }),
        backgroundColor: percentileColors['Min'],
        borderColor: percentileColors['Min'],
        borderWidth: 1,
      },
      {
        label: '25th to 50th Percentile',
        data: validAssetClasses.map(assetClass => {
          const data = yearData[assetClass];
          return [data['25th'] as number, data['50th'] as number] as [number, number];
        }),
        backgroundColor: percentileColors['25th'],
        borderColor: percentileColors['25th'],
        borderWidth: 1,
      },
      {
        label: '50th to 75th Percentile',
        data: validAssetClasses.map(assetClass => {
          const data = yearData[assetClass];
          return [data['50th'] as number, data['75th'] as number] as [number, number];
        }),
        backgroundColor: percentileColors['50th'],
        borderColor: percentileColors['50th'],
        borderWidth: 1,
      },
      {
        label: '75th to Max Percentile',
        data: validAssetClasses.map(assetClass => {
          const data = yearData[assetClass];
          return [data['75th'] as number, data.Max as number] as [number, number];
        }),
        backgroundColor: percentileColors['75th'],
        borderColor: percentileColors['75th'],
        borderWidth: 1,
      },
    ];

    return {
      labels,
      datasets,
    };
  }, [selectedYear]);

  const options: ChartOptions<'bar'> = {
    indexAxis: 'y' as const, // This makes the chart horizontal
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          boxWidth: 12,
          padding: 15,
          font: {
            size: 11,
          },
        },
      },
      title: {
        display: true,
        text: `Expected Returns by Asset Class - ${selectedYear}`,
        font: {
          size: 18,
          weight: 'bold',
        },
        padding: 20,
        color: '#1f2937',
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#3b82f6',
        borderWidth: 0,
        callbacks: {
          label: function (context) {
            const label = context.dataset.label || '';
            const value = context.parsed.x;
            if (value === null) {
              return `${label}: N/A`;
            }
            if (Array.isArray(value)) {
              return `${label}: ${value[0].toFixed(2)}% - ${value[1].toFixed(2)}%`;
            }
            return `${label}: ${value.toFixed(2)}%`;
          },
        },
      },
    },
    scales: {
      x: {
        stacked: false,
        title: {
          display: true,
          text: 'Expected Return (%)',
          font: {
            size: 14,
            weight: 'bold',
          },
          color: '#374151',
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        ticks: {
          color: '#6b7280',
        },
      },
      y: {
        stacked: true,
        title: {
          display: true,
          text: 'Asset Classes',
          font: {
            size: 14,
            weight: 'bold',
          },
          color: '#374151',
        },
        grid: {
          display: false,
        },
        ticks: {
          maxRotation: 0,
          font: {
            size: 11,
          },
          color: '#6b7280',
        },
      },
    },
    elements: {
      bar: {
        borderRadius: 0,
      },
    },
    animation: {
      duration: 750,
      easing: 'easeInOutQuart',
    },
  };

  return (
    <div className="w-full space-y-6 p-6">
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-xl font-semibold text-gray-800 my-4">
            {title}
          </h3>
          <p className="text-gray-600 mt-2">
            Distribution of expected returns across different percentiles
          </p>
        </div>
        <YearSlider
          selectedYear={selectedYear}
          onYearChange={setSelectedYear}
          minYear={Math.min(...availableYears)}
          maxYear={Math.max(...availableYears)}
        />
      </div>

      <div className="bg-white p-4">
        <div className="h-125 w-full">
          <Bar data={chartData} options={options} />
        </div>
      </div>
    </div>
  );
};

export default DynamicExpectedReturnsByAssetClass;
