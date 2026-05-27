// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client';

import React, { useState } from 'react';
import { CorrelationHeatmap } from './correlation-heatmap';
import { YearSlider } from './year-slider';

export const DynamicCorrelationMatrix: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<number>(2020);

  const handleYearChange = (year: number) => {
    setSelectedYear(year);
  };

  return (
    <div className="w-full space-y-6 my-6">
      <div className="text-center">
        <h3 className="text-xl font-semibold text-gray-800 my-4">
          Asset Class Correlation Matrix
        </h3>
      </div>

      {/* Year Slider */}
      <div className="flex justify-center">
        <YearSlider
          selectedYear={selectedYear}
          onYearChange={handleYearChange}
          minYear={2015}
          maxYear={2025}
        />
      </div>

      {/* Correlation Heatmap */}
      <div className="w-full" style={{ height: '600px' }}>
        <CorrelationHeatmap selectedYear={selectedYear} />
      </div>

      {/* Enhanced Legend */}
      <div className="space-y-4">
        <div className="text-center text-sm font-semibold text-gray-700">
          Correlation Strength Legend
        </div>

        {/* Color scale bar */}
        <div className="flex justify-center">
          <div className="flex items-center space-x-1 bg-gray-50 p-3 rounded-lg">
            <div className="text-xs text-gray-600 mr-2">-1.0</div>
            <div className="w-6 h-4" style={{ backgroundColor: '#dc2626' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#ef4444' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#ec4899' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#f9a8d4' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#fce7f3' }}></div>
            <div className="w-6 h-4 border border-gray-300" style={{ backgroundColor: '#ffffff' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#dbeafe' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#93c5fd' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#60a5fa' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#3b82f6' }}></div>
            <div className="w-6 h-4" style={{ backgroundColor: '#1e3a8a' }}></div>
            <div className="text-xs text-gray-600 ml-2">+1.0</div>
          </div>
        </div>
      </div>
    </div>
  );
};