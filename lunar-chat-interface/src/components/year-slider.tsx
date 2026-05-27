// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client';

import React from 'react';

interface YearSliderProps {
  selectedYear: number;
  onYearChange: (year: number) => void;
  minYear?: number;
  maxYear?: number;
}

export const YearSlider: React.FC<YearSliderProps> = ({
  selectedYear,
  onYearChange,
  minYear = 2015,
  maxYear = 2025,
}) => {
  const handleSliderChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const year = parseInt(event.target.value, 10);
    onYearChange(year);
  };

  return (
    <div className="w-full max-w-md mx-auto space-y-4">
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>{minYear}</span>
        <span className="font-semibold text-lg text-gray-800">{selectedYear}</span>
        <span>{maxYear}</span>
      </div>

      <div className="relative">
        <input
          type="range"
          min={minYear}
          max={maxYear}
          value={selectedYear}
          onChange={handleSliderChange}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          style={{
            background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((selectedYear - minYear) / (maxYear - minYear)) * 100
              }%, #e5e7eb ${((selectedYear - minYear) / (maxYear - minYear)) * 100
              }%, #e5e7eb 100%)`,
          }}
        />

        {/* Custom slider thumb styling */}
        <style jsx>{`
          .slider::-webkit-slider-thumb {
            appearance: none;
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #3b82f6;
            cursor: pointer;
            border: 2px solid #ffffff;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          }

          .slider::-moz-range-thumb {
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #3b82f6;
            cursor: pointer;
            border: 2px solid #ffffff;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          }
        `}</style>
      </div>

      <div className="flex justify-between text-xs text-gray-500">
        {Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i).map(
          (year) => (
            <div
              key={year}
              className={`w-1 h-2 rounded ${year === selectedYear ? 'bg-blue-500' : 'bg-gray-300'
                }`}
            />
          )
        )}
      </div>

      <div className="text-center">
        <span className="text-sm text-gray-600">
          Correlation Matrix for Year {selectedYear}
        </span>
      </div>
    </div>
  );
};