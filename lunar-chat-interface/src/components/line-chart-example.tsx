// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import React from "react";
import { LineChart } from "./data-vis/line-chart";
import lineChartData10y from "../data/line_chart-10y.json";

export const LineChartExample: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-4">
          Investment Returns Over Time
        </h2>
        <LineChart
          data={lineChartData10y}
          title="Expected Returns by Asset Class (10-Year Horizon)"
          height={500}
          showLegend={true}
        />
      </div>

      <div className="text-sm text-gray-600 max-w-4xl mx-auto">
        <h3 className="font-semibold mb-2">Features:</h3>
        <ul className="list-disc list-inside space-y-1">
          <li>Displays all data points across the complete time range</li>
          <li>Hover over data points to see detailed values</li>
          <li>
            The chart shows expected annualized returns for various asset
            classes
          </li>
          <li>
            Data points marked as null will not be displayed for those years
          </li>
        </ul>
      </div>
    </div>
  );
};
