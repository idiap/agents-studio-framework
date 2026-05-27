// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartConfiguration,
} from "chart.js";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface ChartRenderOptions {
  width?: number;
  height?: number;
}

/**
 * Renders a Chart.js configuration to a base64 PNG image
 */
export async function renderChartToBase64(
  config: ChartConfiguration,
  options: ChartRenderOptions = {}
): Promise<string> {
  const { width = 800, height = 400 } = options;

  // Create an offscreen canvas
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");

  if (!ctx) {
    throw new Error("Could not get canvas context");
  }

  // Fill with white background
  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, width, height);

  // Create chart instance
  const chart = new ChartJS(ctx, {
    ...config,
    options: {
      ...config.options,
      responsive: false,
      animation: false,
      maintainAspectRatio: false,
    },
  });

  // Wait for chart to render
  await new Promise((resolve) => setTimeout(resolve, 100));

  // Get base64 data
  const base64 = canvas.toDataURL("image/png");

  // Destroy chart to free memory
  chart.destroy();

  return base64;
}

/**
 * Parses a LineChart tag and returns chart configuration
 */
export function parseLineChartTagToConfig(
  tagString: string
): { config: ChartConfiguration<"line">; title: string; note?: string } | null {
  try {
    const seriesMatch = tagString.match(/series=\{(.+?)\}(?=\s+\w+=|\s*\/>)/);
    const titleMatch = tagString.match(/title="([^"]+)"/);
    const noteMatch = tagString.match(/note="([^"]+)"/);

    if (!seriesMatch) return null;

    const seriesStr = seriesMatch[1].trim();
    const jsonStr = `{${seriesStr}}`.replace(/'/g, '"');
    const seriesData = JSON.parse(jsonStr);

    const colors = [
      { border: "rgb(59, 130, 246)", bg: "rgba(59, 130, 246, 0.1)" },
      { border: "rgb(16, 185, 129)", bg: "rgba(16, 185, 129, 0.1)" },
      { border: "rgb(245, 158, 11)", bg: "rgba(245, 158, 11, 0.1)" },
      { border: "rgb(239, 68, 68)", bg: "rgba(239, 68, 68, 0.1)" },
      { border: "rgb(168, 85, 247)", bg: "rgba(168, 85, 247, 0.1)" },
      { border: "rgb(236, 72, 153)", bg: "rgba(236, 72, 153, 0.1)" },
    ];

    const allDates = new Set<string>();
    Object.values(seriesData).forEach((data: unknown) => {
      const typedData = data as { x: string[]; y: number[] };
      typedData.x.forEach((date: string) => allDates.add(date));
    });
    const sortedDates = Array.from(allDates).sort();

    const datasets = Object.entries(seriesData).map(
      ([name, data]: [string, unknown], idx: number) => {
        const typedData = data as { x: string[]; y: number[] };
        const color = colors[idx % colors.length];
        const dateValueMap = new Map<string, number>();
        typedData.x.forEach((date: string, i: number) => {
          dateValueMap.set(date, typedData.y[i]);
        });
        return {
          label: name,
          data: sortedDates.map((date) => dateValueMap.get(date) ?? null),
          borderColor: color.border,
          backgroundColor: color.bg,
          fill: false,
          tension: 0.1,
        };
      }
    );

    const title = titleMatch?.[1] || "";
    const note = noteMatch?.[1];

    const config: ChartConfiguration<"line"> = {
      type: "line",
      data: {
        labels: sortedDates,
        datasets,
      },
      options: {
        responsive: false,
        animation: false,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "top",
          },
          title: {
            display: !!title,
            text: title,
            font: { size: 16 },
          },
        },
        scales: {
          x: {
            display: true,
            grid: { display: true },
          },
          y: {
            display: true,
            grid: { display: true },
          },
        },
      },
    };

    return { config, title, note };
  } catch (error) {
    console.error("Error parsing LineChart tag:", error);
    return null;
  }
}

/**
 * Parses a BarChart tag and returns chart configuration
 */
export function parseBarChartTagToConfig(
  tagString: string
): { config: ChartConfiguration<"bar">; title: string; note?: string } | null {
  try {
    const xMatch = tagString.match(/x=\[([^\]]+)\]/);
    const yMatch = tagString.match(/y=\[([^\]]+)\]/);
    const titleMatch = tagString.match(/title="([^"]+)"/);
    const noteMatch = tagString.match(/note="([^"]+)"/);

    if (!xMatch || !yMatch) return null;

    // Parse x values (strings)
    const xValues = xMatch[1]
      .split(",")
      .map((val) => val.trim().replace(/^["']|["']$/g, ""));

    // Parse y values (numbers)
    const yValues = yMatch[1].split(",").map((val) => parseFloat(val.trim()));

    const title = titleMatch?.[1] || "";
    const note = noteMatch?.[1];

    const config: ChartConfiguration<"bar"> = {
      type: "bar",
      data: {
        labels: xValues,
        datasets: [
          {
            label: title || "Data",
            data: yValues,
            backgroundColor: "rgba(59, 130, 246, 0.6)",
            borderColor: "rgb(59, 130, 246)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: false,
        animation: false,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "top",
          },
          title: {
            display: !!title,
            text: title,
            font: { size: 16 },
          },
        },
        scales: {
          x: {
            display: true,
            grid: { display: true },
          },
          y: {
            display: true,
            grid: { display: true },
          },
        },
      },
    };

    return { config, title, note };
  } catch (error) {
    console.error("Error parsing BarChart tag:", error);
    return null;
  }
}
